# Canary Release

Weighted traffic split via replica counts behind one Service that selects
`app: aceest` (matching both v1 and v2 pods).

## Setup (~20% canary to v2)

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-deployment-v1.yaml
kubectl apply -f k8s/11-deployment-v2.yaml
kubectl apply -f k8s/20-service.yaml

# 4 stable v1 + 1 canary v2 = ~20%
kubectl -n aceest scale deployment/aceest-v1 --replicas=4
kubectl -n aceest scale deployment/aceest-v2 --replicas=1
```

## Probe traffic distribution

```bash
URL=$(minikube service aceest -n aceest --url)
for i in $(seq 1 20); do curl -s ${URL}/version; echo; done | sort | uniq -c
```

## Promote v2 (full cut)

```bash
kubectl -n aceest scale deployment/aceest-v1 --replicas=0
kubectl -n aceest scale deployment/aceest-v2 --replicas=3
```

## Rollback

```bash
kubectl -n aceest scale deployment/aceest-v2 --replicas=0
kubectl -n aceest scale deployment/aceest-v1 --replicas=3
```
