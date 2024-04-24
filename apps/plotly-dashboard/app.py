import os
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services import ResourceManagerV2, ResourceControllerV2
import plotly.express as px
import dash
from dash import dcc
from dash import html

# Set up the IBM Cloud SDK authenticator
authenticator = IAMAuthenticator(os.environ['IBMCLOUD_API_KEY'])

# Create an instance of the Resource Manager service
resource_manager = ResourceManagerV2(authenticator=authenticator)
resource_controller = ResourceControllerV2(authenticator=authenticator)

# Retrieve the list of resource groups
resource_groups = resource_manager.list_resource_groups().get_result()['resources']

# Create a list to store the data for the bubble chart
data = []

# Iterate over each resource group and count the number of resources
for group in resource_groups:
    resource_group_id = group['id']
    resource_count = resource_controller.list_resource_instances(resource_group_id=resource_group_id).get_result()['resources']
    data.append({'resource_group': group['name'], 'resource_count': len(resource_count)})

# Create the Dash app
app = dash.Dash(__name__)

# Create the layout
# app.layout = html.Div([
#     html.H1('IBM Cloud Resource Groups'),
#     dcc.Graph(
#         id='resource-group-bubble-chart',
#         figure=px.scatter(
#             data,
#             x='resource_group',
#             y='resource_count',
#             size='resource_count',
#             hover_name='resource_group',
#             title='Resource Count by Resource Group'
#         )
#     )
# ])

app.layout = html.Div([
    html.H1('IBM Cloud Resource Groups'),
    dcc.Graph(
        id='resource-group-bar-chart',
        figure=px.bar(
            data,
            x='resource_group',
            y='resource_count',
            title='Resource Count by Resource Group',
            labels={'resource_group': 'Resource Group', 'resource_count': 'Resource Count'}
        )
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
