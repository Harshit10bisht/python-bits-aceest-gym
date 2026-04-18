# ACEest Fitness — Assignment 2 Report

**Course:** Introduction to DEVOPS (CSIZG514 / SEZG514) — S1-25
**Scope:** End-to-end CI/CD pipeline with version control, automated testing, code-quality gating, container registry publishing, and progressive Kubernetes delivery for the ACEest Fitness Flask application.

## 1. CI/CD Architecture Overview

The application is a Python 3.12 Flask API with two evolving versions: **v1** (baseline endpoints) and **v2** (adds `/workouts` catalog). Both share a single image; the `APP_VERSION` environment variable distinguishes the running build at request time via `GET /version`.

```text
                +---------------------+
                |   Developer push    |
                +----------+----------+
                           |
                           v
                +---------------------+
                |       GitHub        | <-- branches: main, feature/v2 ; tags: v1.0.0, v2.0.0
                +----------+----------+
                           |  pollSCM (H/2 * * * *) + webhook
                           v
+----------------------------------------------------------+
|                         Jenkins                          |
|  Checkout -> venv -> ruff + compileall                   |
|  pytest --cov (junit + coverage XML)                     |
|  sonar-scanner -> SonarCloud + waitForQualityGate        |
|  docker build --target test  +  docker run pytest        |
|  docker build runtime  -> docker push v1 | v2 | latest   |
|  kubectl apply -f k8s/  (only on main)                   |
+----------------------------------------------------------+
                           |
                           v
                +---------------------+
                |  Docker Hub repo    |  <user>/aceest-fitness:{v1, v2, latest, <tag>-<sha>}
                +----------+----------+
                           |
                           v
                +---------------------+
                |   Minikube cluster  |  ns: aceest
                |  Deployments: v1,v2 |  Services: aceest, aceest-blue/green
                |   Ingress: nginx    |  Strategies: Rolling/BlueGreen/Canary/AB/Shadow
                +---------------------+
```

### Stage gating
Every stage is a hard gate. If lint, tests, the SonarCloud Quality Gate, the Docker test image, or the in-container Pytest run fail, the build aborts and nothing is pushed or deployed. This satisfies the assignment's emphasis on quality validation before delivery.

### Versioning strategy
- **v1**: tagged `v1.0.0` on `main` immediately after the baseline implementation.
- **v2**: developed on `feature/v2`, tagged `v2.0.0`, then merged into `main` via a no-fast-forward merge so the branch topology is preserved in history.
- Image tags map 1:1 to git tags, plus a per-commit `<tag>-<gitsha>` for traceability and `latest` only on `v2`.

## 2. Tooling Map

| Concern              | Tool                | Where it appears                                     |
|----------------------|---------------------|------------------------------------------------------|
| Version control      | Git, GitHub         | repo + branch/tag policy                             |
| Build server         | Jenkins             | [Jenkinsfile](../Jenkinsfile)                        |
| Test framework       | Pytest, pytest-cov  | [tests/](../tests)                                   |
| Linter               | Ruff                | [pyproject.toml](../pyproject.toml)                  |
| Code quality         | SonarCloud          | [sonar-project.properties](../sonar-project.properties) |
| Containerisation     | Docker (multi-stage)| [Dockerfile](../Dockerfile)                          |
| Registry             | Docker Hub          | Jenkins push stage                                   |
| Orchestration        | Kubernetes/Minikube | [k8s/](../k8s)                                       |
| Ingress / mirroring  | NGINX Ingress       | [k8s/30-ingress.yaml](../k8s/30-ingress.yaml), strategy ingresses |
| Secondary CI         | GitHub Actions      | [.github/workflows/main.yml](../.github/workflows/main.yml) |

## 3. Deployment Strategies and Rollback

All five strategies are implemented as runbooks with manifests under [k8s/strategies/](../k8s/strategies):

1. **Rolling Update** — declared on every Deployment (`maxSurge: 1`, `maxUnavailable: 0`); promotion via `kubectl set image` and `kubectl set env APP_VERSION=v2`. Rollback: `kubectl rollout undo`.
2. **Blue-Green** — both Deployments run concurrently; the `aceest-live` Service selector is patched between `version: v1` (blue) and `version: v2` (green). Instant cut and instant rollback.
3. **Canary** — single Service selects `app: aceest`; weighting is achieved by replica counts (e.g. 4xv1 + 1xv2 = ~20% canary), promoted by scaling.
4. **A/B Testing** — NGINX Ingress canary annotation `canary-by-header: X-User-Group` sends `beta` users to v2 while everyone else continues hitting v1.
5. **Shadow** — `mirror-target` Ingress annotation forwards a copy of every production request to a v2 shadow Deployment whose responses are discarded. Useful for risk-free observation under real traffic.

Rollback is a documented one-line command for each strategy (see the table in the README). Combined with the readiness probe on `/health`, a broken image cannot serve traffic.

## 4. Challenges and Mitigation

| Challenge | Mitigation |
|-----------|------------|
| Windows + Docker Desktop pipe occasionally unavailable | Pipeline tolerates this by running unit tests on the host venv first; Docker stages execute on the Jenkins agent (Linux) where the engine is reliable. |
| SonarCloud token leakage risk | Token stored as a Jenkins **Secret text** credential, accessed via `withSonarQubeEnv` (never echoed into logs). |
| Minikube has no public URL | Submission uses `minikube tunnel` / `minikube service --url` and the NodePort `30080` for graders running locally; documented in the README. |
| Multiple versions in one repo | Single image + `APP_VERSION` env var; per-tag image push (`v1`, `v2`, `<tag>-<sha>`); avoids divergent code branches in production. |
| Ingress addon timing on Minikube | README notes `minikube addons enable ingress` as a prerequisite for the A/B and Shadow strategies. |
| Coverage path differences (Linux CI vs Windows dev) | `pytest-cov` writes a relative `coverage.xml`; SonarCloud reads it via `sonar.python.coverage.reportPaths`. |
| Two-version Pytest matrix without duplicating tests | `tests/test_workouts.py` is only meaningful for v2; the v1 image build (from tag `v1.0.0`) does not contain it. CI builds always test the current commit. |

## 5. Key Automation Outcomes

- **Single-click delivery**: any push to `main` triggers lint, unit + container tests, SonarCloud Quality Gate, image push, and Kubernetes rollout — no manual steps.
- **Reversible deploys**: every strategy has a documented rollback that completes in under a minute.
- **Quality gating**: the Quality Gate stage `abortPipeline: true` ensures sub-standard code never reaches Docker Hub or the cluster.
- **Reproducible images**: deterministic tag per git sha (`<tag>-<sha>`) plus moving aliases (`v1`, `v2`, `latest`) gives both pinning and rollback by tag.
- **Defense in depth for testing**: Pytest runs twice — first on the host venv (fast feedback) and then inside the published container (proves the image itself is healthy).
- **Observability hooks ready**: `/health` and `/version` endpoints provide low-cost liveness and version-traceability for any monitoring stack later.

## 6. Submission Checklist

- [x] Public GitHub repository with `main`, `feature/v2`, tags `v1.0.0` and `v2.0.0`.
- [x] Flask v1/v2 application with Pytest suite (22 tests).
- [x] [Jenkinsfile](../Jenkinsfile) with SonarCloud + Docker Hub + Minikube stages.
- [x] [Dockerfile](../Dockerfile) (multi-stage, non-root) and [.dockerignore](../.dockerignore).
- [x] [k8s/](../k8s) manifests + five strategy runbooks.
- [x] [sonar-project.properties](../sonar-project.properties) referencing `coverage.xml` and `pytest-junit.xml`.
- [x] This report.
- [ ] Replace `YOUR_DOCKERHUB_USER`, `YOUR_SONAR_ORG`, `YOUR_SONAR_PROJECT_KEY` with real values before the demo.
- [ ] Push `v1` and `v2` images to Docker Hub.
- [ ] Capture screenshots of: a green Jenkins build, the SonarCloud project page with passing Quality Gate, and the Docker Hub repository tags page.
