# Copyright 2017 Google Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import division

import os
import json
from functools import wraps
from pprint import pprint

import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException

from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask
from flask import make_response
from flask import request, Response

app = Flask(__name__)

basic_auth_username = os.getenv("BASIC_AUTH_USERNAME", "")
basic_auth_password = os.getenv("BASIC_AUTH_PASSWORD", "")

namespace = os.getenv("NAMESPACE", "default")

cluster_id = os.getenv("CLUSTER_ID", "")
project_id = os.getenv("PROJECT_ID", "")
zone = os.getenv("ZONE", "us-central1-c")
scopes = [
    "https://www.googleapis.com/auth/compute.readonly",
    "https://www.googleapis.com/auth/cloud-platform"
]

credentials = ServiceAccountCredentials.from_json_keyfile_name("/etc/apiai-kubernetes-webhook/service-account.json", scopes)

compute_service = discovery.build("compute", "v1", credentials=credentials)
container_service = discovery.build("container", "v1", credentials=credentials)

kubernetes.config.load_incluster_config()
kubernetes_service = kubernetes.client.AppsV1beta1Api()


def check_auth(username, password):
    """This function is called to check if a username password combination is valid."""
    return username == basic_auth_username and password == basic_auth_password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route("/webhook", methods=["POST"])
@requires_auth
def webhook():
    req = request.get_json(silent=True, force=True)

    action = req.get("result").get("action")
    parameters = req.get("result").get("parameters")

    if action == "cluster_status":
        return format_response(get_cluster_status())
    if action == "create_deployment":
       return format_response(create_deployment(parameters))
    if action == "scale_deployment":
       return format_response(scale_deployment(parameters))
    if action == "update_deployment":
       return format_response(update_deployment(parameters))


def format_response(res):
    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers["Content-Type"] = "application/json"
    return r


def create_deployment(parameters):
    image_name = parameters["image_name"]
    image_tag = parameters["image_tag"]

    body = kubernetes.client.AppsV1beta1Deployment()
    body.metadata = {
        "name": image_name,
        "labels": {
            "app": image_name 
        }
    }

    body.spec = {
        "template": {
           "metadata": {
               "labels": {
                 "app": image_name
               }
           },
           "spec": {
               "containers": [
                   {
                      "name": image_name,
                      "image": "gcr.io/{}/{}:{}".format(project_id, image_name, image_tag)
                   }
               ]
           }
        }
    }

    speech = ""

    try:
        response = kubernetes_service.create_namespaced_deployment(namespace, body)
        speech = "Deploying {} {} into the {} cluster.".format(image_name, image_tag, cluster_id)
    except ApiException as e:
        print("Exception when calling AppsV1beta1Api->create_namespaced_deployment: %s\n" % e)
        speech = "There was an error while creating the {} deployment".format(deployment_name)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "kubernetes-webhook"
    }


def scale_deployment(parameters):
    deployment_name = parameters["deployment_name"]
    replica_count = int(parameters["replica_count"])

    body = kubernetes.client.AppsV1beta1Deployment()
    body.spec = {
       "replicas": replica_count
    }

    speech = ""

    try:
        response = kubernetes_service.patch_namespaced_deployment(deployment_name, namespace, body)
        speech = "Scaling the {} deployment to {}".format(deployment_name, replica_count)
    except ApiException as e:
        print("Exception when calling AppsV1beta1Api->patch_namespaced_deployment: %s\n" % e)
        speech = "There was an error while scaling the {} deployment".format(deployment_name)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "kubernetes-webhook"
    }


def update_deployment(parameters):
    deployment_name = parameters["deployment_name"]
    image_name = deployment_name
    image_tag = parameters["image_tag"]

    body = kubernetes.client.AppsV1beta1Deployment()
    body.spec = {
        "template": {
           "spec": {
               "containers": [
                   {
                      "name": image_name,
                      "image": "gcr.io/{}/{}:{}".format(project_id, image_name, image_tag)
                   }
               ]
           }
        }
    }

    speech = ""

    try:
        response = kubernetes_service.patch_namespaced_deployment(deployment_name, namespace, body)
        speech = "Updating the {} deployment to version {}".format(deployment_name, image_tag)
    except ApiException as e:
        print("Exception when calling AppsV1beta1Api->patch_namespaced_deployment: %s\n" % e)
        speech = "There was an error updating the {} deployment".format(deployment_name)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "kubernetes-webhook"
    }


def get_cluster_status():
    cluster_request = container_service.projects().zones().clusters().get(projectId=project_id, zone=zone, clusterId=cluster_id)
    cluster_response = cluster_request.execute()

    num_nodes = cluster_response["currentNodeCount"]
    machine_type = cluster_response["nodeConfig"]["machineType"]

    machine_type_request = compute_service.machineTypes().get(project=project_id, zone=zone, machineType=machine_type)
    machine_type_response = machine_type_request.execute()
    num_cpus = machine_type_response["guestCpus"]
    memory_in_mb = machine_type_response["memoryMb"]

    total_cpus = num_nodes * num_cpus
    total_memory_in_gb = ((num_nodes * memory_in_mb) / 1024)

    speech = "The {} cluster is running with {} CPUs and {} gigs of ram.".format(cluster_id, total_cpus, total_memory_in_gb)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "kubernetes-webhook"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
