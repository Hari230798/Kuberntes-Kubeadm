# DataProtector Support Team Portal — Three-Tier App on Kubeadm (Jenkins CI/CD + Helm + MetalLB)

A mini three-tier project for the **DataProtector tech support team**. Support
engineers submit their details (name, experience, contact, qualification); an
**admin** logs in to validate (approve/reject) each record.

```
Browser ──▶ Ingress (NGINX) ──▶ frontend (nginx/HTML/JS) ──▶ backend (Flask API) ──▶ MySQL
              ▲ external IP from MetalLB (LoadBalancer)         presentation      application     data
```

## Tiers
| Tier | Tech | K8s object |
|------|------|-----------|
| Presentation | Nginx serving HTML/JS, proxies `/api` | `frontend` Deployment + Service |
| Application  | Python Flask REST API + Gunicorn | `backend` Deployment + Service |
| Data         | MySQL 8 with a PersistentVolumeClaim | `mysql` Deployment + Service + PVC |

## Repository layout
```
dataprotector-app/
├── backend/            # Flask API (Dockerfile, app.py, requirements.txt)
├── frontend/           # Nginx + static UI (Dockerfile, nginx.conf, html/)
├── helm/dataprotector/ # Helm chart (all 3 tiers + ingress + secrets)
├── k8s/metallb/        # MetalLB IPAddressPool + L2Advertisement
├── scripts/            # cluster-prereqs.sh (MetalLB + ingress installer)
├── docker-compose.yml  # Local test of all three tiers
├── Jenkinsfile         # CI (build+push) then CD (helm upgrade)
└── README.md
```

## 1. Test locally (optional, no cluster needed)
```bash
docker compose up --build
# Engineer form : http://localhost:8080
# Admin panel   : http://localhost:8080/admin.html   (admin / Admin@123)
```

## 2. Prepare your kubeadm cluster (one time)
On the master node, with kubectl + helm configured:
```bash
chmod +x scripts/cluster-prereqs.sh
./scripts/cluster-prereqs.sh
```
This installs **MetalLB**, applies the IP pool from
`k8s/metallb/metallb-config.yaml`, installs the **NGINX Ingress Controller**,
and exposes it as a `LoadBalancer` so MetalLB assigns it an external IP.

> Edit the address range in `k8s/metallb/metallb-config.yaml` to free IPs on the
> same L2 subnet as your nodes (`172.31.4.145` / `172.31.8.89`). MetalLB L2 is
> textbook-clean on bare-metal/VirtualBox; on AWS EC2 keep the range inside your
> subnet and disable the ENI source/dest check.

After it finishes, note the ingress `EXTERNAL-IP` and add a hosts entry on the
machine you browse from:
```
<EXTERNAL-IP>  dataprotector.local
```

## 3. Configure Jenkins (CI/CD)
1. Add credentials in Jenkins:
   - `dockerhub-creds` — Username/Password (your Docker Hub user + access token)
   - `kubeconfig` — Secret file (the cluster's kubeconfig)
2. Ensure the Jenkins agent has `docker`, `kubectl`, and `helm` installed and can
   reach the cluster.
3. Create a **Pipeline** (or Multibranch) job → *Pipeline script from SCM* →
   point it at this repo, script path `Jenkinsfile`.
4. Edit `DOCKERHUB_USER` in the `Jenkinsfile` and `image.repositoryPrefix` in
   `helm/dataprotector/values.yaml` to your Docker Hub username.

### How SCM push triggers CI → CD
- In GitHub: **Settings → Webhooks → Add webhook** →
  `http://<JENKINS_URL>/github-webhook/`, content type `application/json`,
  event = *push*.
- In the Jenkins job enable **GitHub hook trigger for GITScm polling**.
- The `Jenkinsfile` also has `pollSCM('H/2 * * * *')` as a fallback.

On every push, the pipeline runs:
1. **CI** — build backend + frontend Docker images (tagged with the build
   number), push to Docker Hub.
2. **CD** — `helm upgrade --install` deploys the new tag to the `dataprotector`
   namespace and waits for the rollout.

## 4. Access the app
```
http://dataprotector.local            # engineer registration
http://dataprotector.local/admin.html # admin (admin / Admin@123)
```

## API reference
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/engineers` | public | Submit engineer details |
| POST | `/api/admin/login` | public | Get admin bearer token |
| GET  | `/api/engineers` | admin | List all records |
| PUT  | `/api/engineers/{id}` | admin | Set status `Approved`/`Rejected` |
| GET  | `/api/health` | public | Health check |

## Security notes
- Default credentials/passwords live in `helm/dataprotector/values.yaml` and are
  rendered into a Kubernetes Secret. **Change them** before any real use and
  consider using a sealed-secret / external secret manager.
- The admin token is a shared bearer token for demo simplicity; swap for JWT +
  hashed passwords for production.
