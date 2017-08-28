"""
This converts django_extensions graph_models JSON output to graphwalker JSON format
"""

import hashlib
import json
import sys


# maps Django type to multiplicity contains both forward and reverse versions
MULTIPLICITY_MAP = {
    'ForeignKey': '*..1',
    'FlexibleForeignKey': '*..1', # NOTE: specific to Sentry
    'ManyToManyField': '*..*',
    'OneToOneField': '1..1'
}


def _make_vertex_id(qualified_model_name):
    return hashlib.sha1(qualified_model_name.encode('utf-8')).hexdigest()


def _make_edge_id(source_vertex, dest_vertex, relation):
    return hashlib.sha1(
        '{}({},{})'.format(relation['type'], source_vertex['id'], dest_vertex['id']).encode('utf-8')
    ).hexdigest()


def convert(django_graph_data):
    vertices = []
    vertex_map = {}

    for graph in django_graph_data['graphs']:
        for model in graph['models']:
            qualified_model_name = '{}.{}'.format(graph['app_name'], model['name'])
            new_vertex = {
                'id': _make_vertex_id(qualified_model_name),
                'label': model['name'],
                'searchableComponents': [graph['app_name'], model['name']],
                'properties': {
                    'internalAppName': model['app_name'],
                    'appName': graph['app_name'],
                    'modelName': model['name'],
                    'baseClasses': model.get('abstracts', [])
                }
            }
            vertices.append(new_vertex)

            # store composite key references via tuples for both the app name and internal app name
            vertex_map[(graph['app_name'], model['name'])] = new_vertex
            vertex_map[(model['app_name'], model['name'])] = new_vertex

    edges = []
    edge_map = {}
    for graph in django_graph_data['graphs']:
        for model in graph['models']:
            for relation in model['relations']:
                source_vertex = vertex_map.get((graph['app_name'], model['name']))
                dest_vertex = vertex_map.get((relation['target_app'], relation['target']))

                if source_vertex and dest_vertex:
                    multiplicity = MULTIPLICITY_MAP.get(relation['type'])

                    # invert direction for inheritance
                    if relation['type'] == 'inheritance':
                        source_vertex, dest_vertex = dest_vertex, source_vertex
                        multiplicity = None

                    # deduplicate and merge where possible
                    new_edge = {
                        'id': _make_edge_id(source_vertex, dest_vertex, relation),
                        'source': source_vertex['id'],
                        'dest': dest_vertex['id'],
                        'properties': {
                            'type': relation['type'],
                            'multiplicity': multiplicity,
                            'fields': [relation['name']]
                        }
                    }
                    edge_key = (
                        source_vertex['id'],
                        dest_vertex['id'],
                        relation['type'],
                    )
                    existing_edge = edge_map.get(edge_key)
                    if not existing_edge:
                        # the name of the model property/column or just 'inheritance'
                        edges.append(new_edge)
                        edge_map[edge_key] = new_edge
                    else:
                        # if the same edge already exists with a different label, we collapse the labels
                        # into a comma separated list
                        existing_edge['properties']['fields'].append(relation['name'])

        # recompute label names
        for edge in edges:
            edge['label'] = ', '.join(edge['properties']['fields'])
            if edge['properties'].get('multiplicity'):
                edge['label'] += ' ({})'.format(edge['properties']['multiplicity'])

        return {
            'vertices': vertices,
            'edges': edges
        }


def convert_files(*args):
    django_graph_data_file = args[0]
    with open(django_graph_data_file, 'r') as f:
        django_graph_data = json.load(f)

    graphwalker_data = convert(django_graph_data)
    print(json.dumps(graphwalker_data, indent=2))


if __name__ == '__main__':
    convert_files(*sys.argv[1:])
