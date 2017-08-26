"""
This converts django_extensions graph_models JSON output to graphwalker JSON format
"""

# TODO Support both python 2 and 3

import json
import sys
import traceback


# maps Django type to multiplicity contains both forward and reverse versions
MULTIPLICITY_MAP = {
    'ForeignKey': '*..1',
    'FlexibleForeignKey': '*..1', # NOTE: specific to Sentry
    'ManyToManyField': '*..*',
    'OneToOneField': '1..1'
}


def _make_key(*components):
    return reduce(
        lambda key, component: key + (('#' + component) if key else component),
        components
    )


def convert(django_graph_data):
    vertices = []
    vertex_map = {}

    for graph in django_graph_data['graphs']:
        for model in graph['models']:
            new_vertex = {
                'internalAppName': model['app_name'],
                'appName': graph['app_name'],
                'modelName': model['name']
            }
            vertices.append(new_vertex)

            # store composite key references for both the app name and internal app name
            vertex_map[_make_key(graph['app_name'], model['name'])] = new_vertex
            vertex_map[_make_key(model['app_name'], model['name'])] = new_vertex

    edges = []
    edge_map = {}
    for graph in django_graph_data['graphs']:
        for model in graph['models']:
            for relation in model['relations']:
                source_vertex = vertex_map.get(_make_key(graph['app_name'], model['name']))
                dest_vertex = vertex_map.get(_make_key(relation['target_app'], relation['target']))

                if source_vertex and dest_vertex:
                    multiplicity = MULTIPLICITY_MAP.get(relation['type'])

                    # invert direction for inheritance
                    if relation['type'] == 'inheritance':
                        source_vertex, dest_vertex = dest_vertex, source_vertex
                        multiplicity = None

                    # deduplicate and merge where possible
                    criteria = {
                        'source': source_vertex,
                        'dest': dest_vertex,
                        'type': relation['type'],
                        'label': None,
                        'multiplicity': None
                    }
                    edge_key = _make_key(
                        criteria['source'].get('appName'),
                        criteria['source'].get('modelName'),
                        criteria['dest'].get('appName'),
                        criteria['dest'].get('modelName'),
                        criteria['type']
                    )
                    existing_edge = edge_map.get(edge_key)
                    if not existing_edge:
                        criteria['label'] = relation['name']
                        criteria['multiplicity'] = multiplicity
                        edge_map[edge_key] = edges.append(criteria)
                    else:
                        existing_edge['label']= existing_edge.get('label', '') + ', ' + relation.name

        return {
            'vertices': vertices,
            'edges': edges
        }


def convert_files(*args):
    django_graph_data_file = args[0]
    with open(django_graph_data_file, 'r') as f:
        django_graph_data = json.load(f)

    graphwalker_data = convert(django_graph_data)
    print json.dumps(graphwalker_data, indent=2)


if __name__ == '__main__':
    convert_files(*sys.argv[1:])
