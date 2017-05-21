# API.AI Kubernetes Webhook

```
docker build -t gcr.io/hightowerlabs/apiai-kubernetes-webhook:0.0.1 .
```

```
gcloud docker -- push gcr.io/hightowerlabs/apiai-kubernetes-webhook:0.0.1
```

```
kubectl -n kube-system \
  create secret tls apiai-kubernetes-webhook \
  --key=${HOME}/apiai-kubernetes-webhook-hightowerlabs-com.key \
  --cert=${HOME}/apiai-kubernetes-webhook-hightowerlabs-com.pem
```

```
kubectl -n kube-system \
  create configmap apiai-kubernetes-webhook \
  --from-file nginx/apiai-kubernetes-webhook.conf
```

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

```
kubectl create secret generic apiai-kubernetes-webhook-service-account \
  --from-file service-account.json -n kube-system
```
