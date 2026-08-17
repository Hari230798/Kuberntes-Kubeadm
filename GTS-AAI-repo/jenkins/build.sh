#!/usr/bin/env bash
# Build step for the Jenkins FREESTYLE project.
# Configure the job's single "Execute shell" build step to run:  bash jenkins/build.sh
#
# Requirements on the Jenkins agent/node:
#   - docker (logged-in identity provided via the DOCKERHUB_USR/DOCKERHUB_PSW
#     credential binding configured in the job)
#   - kubectl already configured with a kubeconfig that can reach the cluster
#
# Job credential binding (Job > Configure > Build Environment >
#   "Use secret text(s) or file(s)" > Username and password (separated)):
#     Username Variable: DOCKERHUB_USR
#     Password Variable: DOCKERHUB_PSW
#     Credentials:       <your Docker Hub username/password or access token>

set -euo pipefail

IMAGE="docker.io/hariharan230798/gts-aai"
TAG="${BUILD_NUMBER:-latest}"

echo "==> Building image ${IMAGE}:${TAG}"
docker build -t "${IMAGE}:${TAG}" -t "${IMAGE}:latest" .

echo "==> Logging in to Docker Hub"
echo "${DOCKERHUB_PSW}" | docker login -u "${DOCKERHUB_USR}" --password-stdin

echo "==> Pushing image"
docker push "${IMAGE}:${TAG}"
docker push "${IMAGE}:latest"

echo "==> Applying Kubernetes manifests"
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/deployment.yaml

echo "==> Rolling out image ${IMAGE}:${TAG}"
kubectl -n gts-aai set image deployment/gts-aai web="${IMAGE}:${TAG}"
kubectl -n gts-aai rollout status deployment/gts-aai --timeout=180s

echo "==> Done. Current pods:"
kubectl -n gts-aai get pods -o wide
