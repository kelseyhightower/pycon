from __future__ import division
from pprint import pprint
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from flask import make_response
from flask import request, Response
from functools import wraps
import json
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException

app = Flask(__name__)

project_id = 'hightowerlabs'
zone = 'us-central1-c'
cluster_id = 'pycon'

scopes = [
    'https://www.googleapis.com/auth/compute.readonly',
    'https://www.googleapis.com/auth/cloud-platform'
]

credentials = ServiceAccountCredentials.from_json_keyfile_name('/etc/apiai-kubernetes-webhook/service-account.json', scopes)

compute_service = discovery.build('compute', 'v1', credentials=credentials)
container_service = discovery.build('container', 'v1', credentials=credentials)

kubernetes.config.load_incluster_config()
api_instance = kubernetes.client.AppsV1beta1Api()
namespace = 'default'


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == '' and password == ''

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/webhook', methods=['POST'])
@requires_auth
def webhook():
    req = request.get_json(silent=True, force=True)

    action = req.get("result").get("action")

    if action == "cluster_status":
        return format_response(get_cluster_status())

    parameters = req.get("result").get("parameters")

    if action == "create_deployment":
       return format_response(create_deployment(parameters))

    if action == "scale_deployment":
       return format_response(scale_deployment(parameters))

    if action == "update_deployment":
       return format_response(update_deployment(parameters))

def format_response(res):
    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def create_deployment(parameters):
    body = kubernetes.client.AppsV1beta1Deployment()
    body.metadata = {
        'name': parameters['image_name'],
        'labels': {
            'app': parameters['image_name'] 
        }
    }

    body.spec = {
        'template': {
           'metadata': {
               'labels': {
                 'app': parameters['image_name']
               }
           },
           'spec': {
               'containers': [
                   {
                      'name': parameters['image_name'],
                      'image': "gcr.io/hightowerlabs/{}:{}".format(parameters['image_name'], parameters['image_tag'])
                   }
               ]
           }
        }
    }

    try:
        api_response = api_instance.create_namespaced_deployment(namespace, body)
    except ApiException as e:
        print("Exception when calling AppsV1beta1Api->create_namespaced_deployment: %s\n" % e)

    speech = "Deploying {} {} into the pycon cluster.".format(parameters['image_name'], parameters['image_tag'])

    return {
        "speech": speech,
        "displayText": speech,
        "source": "kubernetes-webhook"
    }

def scale_deployment(parameters):
    return
def update_deployment(parameters):
    return

def get_cluster_status():
    cluster_request = container_service.projects().zones().clusters().get(projectId=project_id, zone=zone, clusterId=cluster_id)
    cluster_response = cluster_request.execute()

    num_nodes = cluster_response['currentNodeCount']
    machine_type = cluster_response['nodeConfig']['machineType']

    machine_type_request = compute_service.machineTypes().get(project=project_id, zone=zone, machineType=machine_type)
    machine_type_response = machine_type_request.execute()
    num_cpus = machine_type_response['guestCpus']
    memory_in_mb = machine_type_response['memoryMb']

    total_cpus = num_nodes * num_cpus
    total_memory_in_gb = ((num_nodes * memory_in_mb) / 1024)

    speech = "The {} cluster is running with {} CPUs and {} of ram.".format(cluster_id, total_cpus, total_memory_in_gb)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "kubernetes-webhook"
    }

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
