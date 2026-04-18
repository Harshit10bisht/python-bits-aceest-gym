# A/B Testing (header-based routing)

Uses the NGINX Ingress canary annotations to send users that send a
`X-User-Group: beta` header to v2 while everyone else stays on v1.

## Prereqs

```bash
minikube addons enable ingress
```

## Apply

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-deployment-v1.yaml
kubectl apply -f k8s/11-deployment-v2.yaml
kubectl apply -f k8s/strategies/ab-services.yaml
kubectl apply -f k8s/strategies/ab-ingress.yaml
```

## Demo

```bash
INGRESS_IP=$(minikube ip)

# Default users -> v1
curl -H "Host: aceest.local" http://${INGRESS_IP}/version

# Beta cohort -> v2
curl -H "Host: aceest.local" -H "X-User-Group: beta" http://${INGRESS_IP}/version
```

## Rollback (disable beta cohort)

```bash
kubectl -n aceest delete ingress aceest-canary
```
