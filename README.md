# ACEest Fitness & Gym — Flask API and CI/CD

Flask REST API for client and progress management, ported from the original Tkinter baseline (`Aceestver2.0.1.py`): same programs, calorie targets, and SQLite schema. This repository includes **Pytest** coverage, **Docker** images, **GitHub Actions** CI, and a **Jenkins** pipeline definition.

## Features

- `GET /health` — liveness probe
- `GET /programs` — training programs and calorie multipliers
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

Optional: lint before commit:

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
| **When it runs** | On every **push** and **pull_request** to `main` | When the Jenkins job is triggered (SCM polling, webhook, or manual) |
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
app.py                 # Flask application factory and routes
fitness_core.py        # Programs, calories, DB bootstrap
requirements.txt       # Runtime (Flask, Gunicorn)
requirements-dev.txt   # Dev tools (Pytest, Ruff) + runtime
tests/                 # Pytest suite
Dockerfile             # Multi-stage: test + runtime
Jenkinsfile            # Declarative pipeline
.github/workflows/main.yml
```

Legacy Tkinter prototypes (`Aceest*.py`) remain in the folder as reference only; they are excluded from Ruff via `pyproject.toml`.

## License

Educational use — ACEest Fitness & Gym assignment.
