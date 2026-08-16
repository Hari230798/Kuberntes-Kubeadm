#!/usr/bin/env bash
# ===========================================================================
# One-time cluster prerequisites for the DataProtector app on kubeadm.
# Run these on the master node (or wherever kubectl/helm are configured).
# ===========================================================================
set -euo pipefail

echo "==> 1. Install MetalLB (LoadBalancer implementation)"
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.8/config/manifests/metallb-native.yaml
echo "Waiting for MetalLB controller to be ready..."
kubectl wait --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app=metallb \
  --timeout=180s

echo "==> 2. Configure MetalLB IP pool (edit the range first if needed!)"
kubectl apply -f k8s/metallb/metallb-config.yaml

echo "==> 3. Install NGINX Ingress Controller (as LoadBalancer -> MetalLB IP)"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/baremetal/deploy.yaml
# Switch the controller Service to LoadBalancer so MetalLB assigns an external IP.
kubectl -n ingress-nginx patch svc ingress-nginx-controller \
  -p '{"spec": {"type": "LoadBalancer"}}'

echo "==> 4. Show the assigned LoadBalancer IP"
kubectl -n ingress-nginx get svc ingress-nginx-controller

cat <<'EOF'

Next steps:
  * Note the EXTERNAL-IP from the command above (assigned by MetalLB).
  * Add a hosts entry on the machine you browse from:
        <EXTERNAL-IP>  dataprotector.local
  * Trigger the Jenkins pipeline (push to git) to build + deploy.
  * Browse to http://dataprotector.local
EOF
