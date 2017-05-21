# PyCon 2017 Demo

This repo holds Kelsey's PyCon 2017 demo.

## Building the Hello World Container

```
docker build -t gcr.io/hightowerlabs/helloworld:1.0.0 .
```

```
gcloud docker -- push gcr.io/hightowerlabs/helloworld:1.0.0
```

## Testing the Hello World Container

```
docker run -p 5000:5000 -d gcr.io/hightowerlabs/helloworld:1.0.0
```

## Testing with Kubernetes

```
kubectl create -f deployments/helloworld.yaml
```

```
kubectl create -f services/helloworld.yaml
```

## Deploy the Hello World Pod

```
kubectl create configmap helloworld \
  --from-file nginx/helloworld.conf
```
