```
docker build -t gcr.io/hightowerlabs/helloworld-python:0.0.1 .
```

```
gcloud docker -- push gcr.io/hightowerlabs/helloworld-python:0.0.1
```

```
docker run -p 5000:5000 -d gcr.io/hightowerlabs/pycon:0.0.1
```

```
kubectl create configmap helloworld --from-file nginx/helloworld.conf
```
