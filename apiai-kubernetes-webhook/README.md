# API.AI Kubernetes Webhook

## Creating the Container Images

```
docker build -t gcr.io/hightowerlabs/apiai-kubernetes-webhook:0.3.1 .
```

```
gcloud docker -- push gcr.io/hightowerlabs/apiai-kubernetes-webhook:0.3.1
```

## Secrets and Configmaps

The API.AI Kubernetes webhook requires a valid TLS certificate. Use certbot to create one then store the certs in the `apiai-kubernetes-webhook-tls` secret

```
kubectl -n kube-system \
  create secret tls apiai-kubernetes-webhook-tls \
  --key=${HOME}/apiai-kubernetes-webhook-hightowerlabs-com.key \
  --cert=${HOME}/apiai-kubernetes-webhook-hightowerlabs-com.pem
```

export BASIC_AUTH_PASSWORD=$(openssl rand -hex 16)

```
kubectl -n kube-system \
  create secret generic apiai-kubernetes-webhook \
  --from-literal "basic-auth-username=apiai" \
  --from-literal "basic-auth-password=${BASIC_AUTH_PASSWORD}"
```

```
kubectl -n kube-system \
  create configmap apiai-kubernetes-webhook \
  --from-file nginx/apiai-kubernetes-webhook.conf \
  --from-literal "cluster-id=pycon" \
  --from-literal "project-id=hightowerlabs" \
  --from-literal "namespace=default"
```

## Create GCP Service Account

```
export PROJECT_ID=$(gcloud config get-value core/project)
```

```
export SERVICE_ACCOUNT_NAME="apiai-kubernetes-webhook"
```

```
gcloud beta iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
  --display-name "apiai kubernetes webhook"
```

```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/container.viewer'
```

```
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role='roles/viewer'
```

```
gcloud beta iam service-accounts keys create \
  --iam-account "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  service-account.json
```

## Deploy the API.AI Kubernetes Webhook

```
kubectl -n kube-system \
  create secret generic apiai-kubernetes-webhook-service-account \
  --from-file $HOME/service-account.json
```

```
kubectl -n kube-system create -f services/apiai-kubernetes-webhook.yaml
```

```
kubectl -n kube-system create -f deployments/apiai-kubernetes-webhook.yaml
```
