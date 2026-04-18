# Shadow (Mirror) Deployment

Real production traffic continues to hit v1, while a copy of every request
is mirrored to a v2 "shadow" Deployment. The mirror's response is discarded,
so users are never affected, but you can observe v2 behavior under real load.

Implemented with the NGINX Ingress `mirror-target` annotation.

## Apply

```bash
minikube addons enable ingress
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-deployment-v1.yaml
kubectl apply -f k8s/strategies/shadow-deployment.yaml
kubectl apply -f k8s/strategies/ab-services.yaml          # reuse aceest-v1 svc
kubectl apply -f k8s/strategies/shadow-service.yaml
kubectl apply -f k8s/strategies/shadow-ingress.yaml
```

## Verify mirroring

```bash
INGRESS_IP=$(minikube ip)
curl -H "Host: aceest.local" http://${INGRESS_IP}/version    # response from v1

# Tail shadow logs while curling
kubectl -n aceest logs -l app=aceest,role=shadow -f
```

## Disable shadow

```bash
kubectl -n aceest delete ingress aceest-shadow-ingress
kubectl -n aceest delete -f k8s/strategies/shadow-deployment.yaml
```
