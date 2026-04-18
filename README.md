# ACEest Fitness & Gym — Flask API and CI/CD

Flask REST API for client and progress management, ported from the original Tkinter baseline (`Aceestver2.0.1.py`): same programs, calorie targets, and SQLite schema. This repository includes **Pytest** coverage, **Docker** images, **GitHub Actions** CI, and a **Jenkins** pipeline definition that publishes to **Docker Hub**, runs a **SonarCloud** quality gate, and deploys to **Kubernetes (Minikube)** with five progressive delivery strategies.

## Versions

| Version | Branch / tag | Image | Endpoints added |
|---------|--------------|-------|-----------------|
| **v1**  | `v1.0.0` tag (commit before `feature/v2` merge) | `YOUR_DOCKERHUB_USER/aceest-fitness:v1` | core API + `/version` |
| **v2**  | `main` (post-merge of `feature/v2`), tag `v2.0.0` | `YOUR_DOCKERHUB_USER/aceest-fitness:v2` and `:latest` | adds `/workouts`, `/workouts/<program>` |

The same image is parameterised with the `APP_VERSION` environment variable so both Deployments can be observed in the same cluster.

## Features

- `GET /health` — liveness probe
- `GET /version` — returns `APP_VERSION` (default `v1` on the v1 build, `v2` on the v2 build)
- `GET /programs` — training programs and calorie multipliers
- `GET /workouts` (v2) — full catalog
- `GET /workouts/<program>` (v2) — workouts for one program
- `POST /clients` — create or update a client (JSON: `name`, `age`, `weight`, `program`)
- `GET /clients/<name>` — fetch a client profile
- `POST /clients/<name>/progress` — log weekly adherence (JSON: `adherence` 0–100)

SQLite file path: environment variable `ACEEST_DB` (default `aceest_fitness.db` in the working directory).

## Prerequisites

- Python **3.12+** (3.12 matches Docker and CI)
- Optional: **Docker** for container build/run
- Optional: **Jenkins** with Git, Docker CLI on the agent, and Python 3

## Local setup and run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run the API:

```bash
python app.py
```

Or with the Flask CLI:

```bash
flask --app app run --host 0.0.0.0 --port 5000
```

The server listens on port **5000** by default (`PORT` env overrides this for `python app.py`).

### Example requests

```bash
curl -s http://127.0.0.1:5000/programs
curl -s -X POST http://127.0.0.1:5000/clients -H "Content-Type: application/json" \
  -d '{"name":"Alex","age":28,"weight":75,"program":"Fat Loss (FL)"}'
curl -s http://127.0.0.1:5000/clients/Alex
curl -s -X POST http://127.0.0.1:5000/clients/Alex/progress -H "Content-Type: application/json" \
  -d '{"adherence":85}'
```

## Run tests manually

With the virtual environment activated and dev dependencies installed:

```bash
pytest -v
```

With coverage and JUnit XML (used by CI and SonarCloud):

```bash
pytest --cov=. --cov-report=xml --junitxml=pytest-junit.xml -v
```

Lint before commit:

```bash
ruff check .
python -m compileall -q app.py fitness_core.py tests
```

## Docker

Build the **runtime** image (non-root user, `gunicorn` with the `create_app` factory):

```bash
docker build -t aceest-fitness:latest .
docker run --rm -e ACEEST_DB=/tmp/aceest.db -p 5000:5000 aceest-fitness:latest
```

Build the **test** image and run the full Pytest suite inside the container (same command CI uses):

```bash
docker build --target test -t aceest-fitness:test .
docker run --rm aceest-fitness:test
```

## GitHub Actions vs Jenkins

| Aspect | GitHub Actions (`.github/workflows/main.yml`) | Jenkins (`Jenkinsfile`) |
|--------|-----------------------------------------------|-------------------------|
| **When it runs** | On every **push** and **pull_request** (all branches) | When the Jenkins job is triggered (SCM polling, webhook, or manual) |
| **Purpose** | Fast feedback on GitHub for all contributors | Controlled **build server** (lab or on-prem) that mirrors a dedicated integration environment |
| **Steps** | Install Python deps → **Ruff** + **compileall** → build Docker **test** target → **`docker run`** to execute Pytest in the container | Checkout → venv → lint + compile → **Pytest on agent** → Docker test image + container Pytest → runtime image build |

Together, **GitHub Actions** enforces quality on each change in the remote repository, while **Jenkins** provides a second, operator-controlled pipeline that still pulls from GitHub and proves the project builds and tests cleanly (including Docker) on your Jenkins infrastructure.

### Freestyle Jenkins (alternative)

If you do not use the `Jenkinsfile`, configure a **Pipeline** from SCM pointing at this repo, or a **Freestyle** project with:

1. Source Code Management: your GitHub URL, branch `main`
2. Build → Execute shell:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
python -m compileall -q app.py fitness_core.py tests
pytest -v
docker build --target test -t aceest-fitness:test .
docker run --rm aceest-fitness:test
docker build -t aceest-fitness:latest .
```

Use a **Linux** agent with Docker available, or adapt commands for your platform.

## Version control workflow (suggested)

- `main`: release-ready code
- Short-lived branches: `feature/...`, `fix/...`, `infra/...`
- Merge via pull requests with clear, imperative commit messages (e.g. `feat: add client progress endpoint`, `ci: add GitHub Actions workflow`)

## Project layout

```
app.py                       # Flask application factory and routes
fitness_core.py              # Programs, calories, workouts, DB bootstrap
requirements.txt             # Runtime (Flask, Gunicorn)
requirements-dev.txt         # Dev tools (Pytest, pytest-cov, Ruff) + runtime
tests/                       # Pytest suite (logic, API, version, workouts)
Dockerfile                   # Multi-stage: test + runtime (non-root)
Jenkinsfile                  # Declarative CI/CD: SonarCloud, Docker Hub, K8s
sonar-project.properties     # SonarCloud scanner config
.github/workflows/main.yml   # GitHub Actions
k8s/                         # Kubernetes base manifests (namespace, deployments, svc, ingress)
k8s/strategies/              # Rolling, Blue-Green, Canary, A/B, Shadow
report/REPORT.md             # 2-3 page assignment report
```

Legacy Tkinter prototypes (`Aceest*.py`) remain in the folder as reference only; they are excluded from Ruff via `pyproject.toml`.

---

# Assignment 2 — End-to-end CI/CD

## Architecture

```text
GitHub  --(pollSCM/webhook)-->  Jenkins
                                  |-- ruff + pytest + coverage
                                  |-- SonarCloud scan + Quality Gate
                                  |-- docker build (test) + docker run pytest
                                  |-- docker build runtime + push to Docker Hub
                                  +-- kubectl apply on Minikube  --> Strategy: Rolling | Blue-Green | Canary | A/B | Shadow
```

## Docker Hub setup (one-time)

1. Create a public Docker Hub repository named `aceest-fitness`.
2. Generate a Personal Access Token (Account Settings -> Security).
3. In Jenkins -> Manage Credentials, add a **Username with password** credential with ID **`dockerhub`** (username = your Docker Hub user, password = the PAT).
4. Replace every occurrence of `YOUR_DOCKERHUB_USER` in this repo with your Docker Hub user. The placeholders live in:
   - [`Jenkinsfile`](Jenkinsfile) (the `DOCKERHUB_USER` env)
   - [`k8s/10-deployment-v1.yaml`](k8s/10-deployment-v1.yaml), [`k8s/11-deployment-v2.yaml`](k8s/11-deployment-v2.yaml), [`k8s/strategies/shadow-deployment.yaml`](k8s/strategies/shadow-deployment.yaml)
   - The strategy markdown files under [`k8s/strategies/`](k8s/strategies)

Quick replace on Linux/macOS:

```bash
grep -rl YOUR_DOCKERHUB_USER . | xargs sed -i 's/YOUR_DOCKERHUB_USER/<your-handle>/g'
```

PowerShell:

```powershell
Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\.git\\' } |
  ForEach-Object {
    (Get-Content $_.FullName) -replace 'YOUR_DOCKERHUB_USER', '<your-handle>' |
      Set-Content $_.FullName
  }
```

Manual local push (without Jenkins):

```bash
docker login
docker build -t <user>/aceest-fitness:v2 -t <user>/aceest-fitness:latest .
docker push <user>/aceest-fitness:v2
docker push <user>/aceest-fitness:latest
# v1 image:
git checkout v1.0.0
docker build -t <user>/aceest-fitness:v1 .
docker push <user>/aceest-fitness:v1
git checkout main
```

## SonarCloud setup (one-time)

1. Sign in to https://sonarcloud.io with GitHub and import the repo.
2. Note the **organization** and **project key** SonarCloud assigns; replace `YOUR_SONAR_ORG` and `YOUR_SONAR_PROJECT_KEY` in [`sonar-project.properties`](sonar-project.properties).
3. Generate a token (My Account -> Security) and add it in Jenkins as a **Secret text** credential with ID **`sonarcloud-token`**.
4. In Jenkins -> Manage Jenkins -> System, add a SonarQube server entry named exactly **`SonarCloud`** (matches the `SONAR_SERVER` env in the Jenkinsfile), URL `https://sonarcloud.io`, Authentication token = `sonarcloud-token`.
5. Install Jenkins plugins: **SonarQube Scanner**, **Docker Pipeline**, **Pipeline Utility Steps**, **Kubernetes CLI**.
6. Configure a **SonarScanner** tool (Manage Jenkins -> Tools), or pre-install `sonar-scanner` on the agent so the Jenkinsfile fallback path resolves it.

## Jenkins job configuration

- New item -> **Multibranch Pipeline** (preferred) or **Pipeline from SCM** pointing at this GitHub repo.
- Branch sources: GitHub, discover branches, build tags `v*`.
- Triggers: the [`Jenkinsfile`](Jenkinsfile) declares `pollSCM('H/2 * * * *')`. Add a GitHub webhook for instant builds.
- Required credentials: `dockerhub`, `sonarcloud-token`, and (for the deploy stage) a **Secret file** credential with ID **`kubeconfig`** containing the cluster's kubeconfig.

## Minikube setup

```bash
minikube start --cpus=4 --memory=4g
minikube addons enable ingress
kubectl create namespace aceest      # or: kubectl apply -f k8s/00-namespace.yaml

kubectl apply -f k8s/
```

Local DNS for the Ingress (point `aceest.local` at the Minikube IP):

```bash
echo "$(minikube ip) aceest.local" | sudo tee -a /etc/hosts
# Windows: add the line to C:\Windows\System32\drivers\etc\hosts (admin)
```

Reach the service:

```bash
minikube service aceest -n aceest --url
# or via Ingress:
curl -H "Host: aceest.local" http://$(minikube ip)/health
```

## Deployment strategies (with rollback)

Each strategy has a dedicated runbook under [`k8s/strategies/`](k8s/strategies):

| Strategy | Runbook | Rollback command |
|----------|---------|------------------|
| Rolling Update | [rolling-update.md](k8s/strategies/rolling-update.md) | `kubectl -n aceest rollout undo deployment/aceest-v1` |
| Blue-Green     | [blue-green.md](k8s/strategies/blue-green.md) | Patch `aceest-live` Service selector back to `version: v1` |
| Canary         | [canary.md](k8s/strategies/canary.md) | `kubectl scale` v2 to 0 and v1 to 3 |
| A/B Testing    | [ab-testing.md](k8s/strategies/ab-testing.md) | `kubectl delete ingress aceest-canary` |
| Shadow         | [shadow.md](k8s/strategies/shadow.md) | Delete `aceest-shadow-ingress` and the shadow Deployment |

Every Deployment uses `RollingUpdate` with `maxUnavailable: 0` and `/health` readiness probes, so a failed rollout never serves a non-ready pod and `kubectl rollout undo` restores the last good ReplicaSet.

## License

Educational use — ACEest Fitness & Gym assignment.
