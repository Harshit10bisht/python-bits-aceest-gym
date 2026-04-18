# Blue-Green Deployment

Both Deployments run side-by-side. A single live `Service` selects one color
at a time using a label patch. Rollback is a label flip.

## Setup

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-deployment-v1.yaml   # blue
kubectl apply -f k8s/11-deployment-v2.yaml   # green
kubectl apply -f k8s/strategies/blue-green-service.yaml
```

## Cut over to green (v2)

```bash
kubectl -n aceest patch service aceest-live \
    -p '{"spec":{"selector":{"app":"aceest","version":"v2"}}}'

# Verify
curl $(minikube service aceest-live -n aceest --url)/version
```

## Rollback to blue (v1)

```bash
kubectl -n aceest patch service aceest-live \
    -p '{"spec":{"selector":{"app":"aceest","version":"v1"}}}'
```
