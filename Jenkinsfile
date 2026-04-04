pipeline {
    agent any

    environment {
        IMAGE_TEST = 'aceest-fitness:test'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint and compile') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                    ruff check .
                    python -m compileall -q app.py fitness_core.py tests
                '''
            }
        }

        stage('Unit tests (host)') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -v
                '''
            }
        }

        stage('Docker build (test target)') {
            steps {
                sh "docker build --target test -t ${IMAGE_TEST} ."
            }
        }

        stage('Pytest in container') {
            steps {
                sh "docker run --rm ${IMAGE_TEST}"
            }
        }

        stage('Docker build (runtime image)') {
            steps {
                sh 'docker build -t aceest-fitness:latest .'
            }
        }
    }
}
