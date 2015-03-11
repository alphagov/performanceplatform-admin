import requests

from application import app
from application.helpers import requires_authentication, base_template_context
from colour import Color
from flask import make_response, render_template, session
from graphviz import Digraph


@app.route("/admin/transforms", methods=['GET'])
@requires_authentication
def transforms_index(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    return render_template('transforms/index.html', **template_context)


@app.route("/admin/transforms/dotfile", methods=['GET'])
@requires_authentication
def transforms_dotfile(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    transforms_url = '{0}/transforms'.format(app.config['STAGECRAFT_HOST'])
    transforms = requests.get(transforms_url).json()

    dot = Digraph(
        name='Performance Platform transforms',
        format='svg',
        graph_attr={'rankdir': 'LR'},
        node_attr={'shape': 'box', 'fontname': 'Helvetica', 'fontsize': '24'},
        edge_attr={'fontname': 'Helvetica', 'fontsize': '24'},
    )

    output_datasets = []
    output_transforms = []
    dataset_id = 0

    def dictionary_is_subset(subset, superset):
        """Return a boolean indicating whether one dictionary is a subset
           of another."""
        return all(item in superset.items() for item in subset.items())

    def find_dataset(dataset, dataset_list):
        return [d for d in dataset_list if dictionary_is_subset(dataset, d)]

    for transform in transforms:
        ids = {
            'input': None,
            'output': None,
        }

        for key in ['input', 'output']:
            dataset = transform[key]

            filtered_datasets = find_dataset(dataset, output_datasets)

            if filtered_datasets:
                ids[key] = filtered_datasets[0]['id']
            else:
                ids[key] = dataset_id
                dataset_id += 1

                output_datasets.append({
                    'id': str(ids[key]),
                    'data-group': dataset['data-group'],
                    'data-type': dataset['data-type'],
                    'colour': Color(pick_for=dataset['data-type']).hex,
                })

        transform_type = transform['type']['function'].split('.')[3]

        output_transforms.append({
            'input': str(ids['input']),
            'output': str(ids['output']),
            'label': transform_type,
            'colour': Color(pick_for=transform_type).hex,
        })

    for node in output_datasets:
        dot.node(
            node['id'],
            '{0} {1}'.format(node['data-group'], node['data-type']),
            fontcolor=node['colour']
        )

    for edge in output_transforms:
        dot.edge(
            edge['input'],
            edge['output'],
            label=edge['label'],
            fontcolor=edge['colour']
        )

    resp = make_response(dot.source)
    resp.content_type = 'text/plain'
    resp.headers['Content-Disposition'] = 'attachment; filename=transforms.dot'

    return resp
