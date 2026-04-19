# Rolling Update

The base [10-deployment-v1.yaml](../10-deployment-v1.yaml) already declares
`strategy.type: RollingUpdate` with `maxSurge: 1, maxUnavailable: 0`.

## Demo

```bash
# Start with v1 (3 replicas)
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-deployment-v1.yaml
kubectl apply -f k8s/20-service.yaml

# Watch
kubectl -n aceest get pods -w &

# Roll forward to v2 image (in-place rolling update of the v1 Deployment)
kubectl -n aceest set image deployment/aceest-v1 \
    app=hbisht1210/aceest-fitness:v2
kubectl -n aceest set env deployment/aceest-v1 APP_VERSION=v2

kubectl -n aceest rollout status deployment/aceest-v1
```

## Rollback

```bash
kubectl -n aceest rollout undo deployment/aceest-v1
kubectl -n aceest rollout status deployment/aceest-v1
```
