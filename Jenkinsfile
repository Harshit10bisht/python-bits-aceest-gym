pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        DOCKERHUB_USER = 'YOUR_DOCKERHUB_USER'
        IMAGE_REPO     = "${DOCKERHUB_USER}/aceest-fitness"
        IMAGE_TEST     = "aceest-fitness:test-${env.BUILD_NUMBER}"
        SONAR_SERVER   = 'SonarCloud'
        K8S_NAMESPACE  = 'aceest'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    if (env.TAG_NAME) {
                        env.IMAGE_TAG = env.TAG_NAME.replaceFirst(/^v/, '').startsWith('1') ? 'v1' : 'v2'
                    } else if (env.BRANCH_NAME == 'main') {
                        env.IMAGE_TAG = 'v2'
                    } else if (env.BRANCH_NAME == 'feature/v2') {
                        env.IMAGE_TAG = 'v2'
                    } else {
                        env.IMAGE_TAG = "branch-${env.BRANCH_NAME?.replaceAll('[^a-zA-Z0-9_.-]', '-')}"
                    }
                    echo "Building image tag: ${env.IMAGE_TAG} (sha=${env.GIT_SHORT})"
                }
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Lint and compile') {
            steps {
                sh '''
                    . .venv/bin/activate
                    ruff check .
                    python -m compileall -q app.py fitness_core.py tests
                '''
            }
        }

        stage('Pytest with coverage') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest --cov=. --cov-report=xml --junitxml=pytest-junit.xml -v
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'pytest-junit.xml'
                }
            }
        }

        stage('SonarCloud analysis') {
            steps {
                withSonarQubeEnv("${SONAR_SERVER}") {
                    sh '''
                        if command -v sonar-scanner >/dev/null 2>&1; then
                            sonar-scanner -Dsonar.projectVersion=${BUILD_NUMBER}-${GIT_SHORT}
                        else
                            ${SONAR_SCANNER_HOME:-/opt/sonar-scanner}/bin/sonar-scanner \
                                -Dsonar.projectVersion=${BUILD_NUMBER}-${GIT_SHORT}
                        fi
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker build (test) and run pytest in container') {
            steps {
                sh '''
                    docker build --target test -t ${IMAGE_TEST} .
                    docker run --rm ${IMAGE_TEST}
                '''
            }
        }

        stage('Docker build runtime image') {
            steps {
                sh '''
                    docker build -t ${IMAGE_REPO}:${IMAGE_TAG} \
                                 -t ${IMAGE_REPO}:${IMAGE_TAG}-${GIT_SHORT} .
                '''
                script {
                    if (env.IMAGE_TAG == 'v2') {
                        sh 'docker tag ${IMAGE_REPO}:${IMAGE_TAG} ${IMAGE_REPO}:latest'
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            when {
                anyOf {
                    branch 'main'
                    branch 'feature/v2'
                    tag 'v*'
                }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push ${IMAGE_REPO}:${IMAGE_TAG}
                        docker push ${IMAGE_REPO}:${IMAGE_TAG}-${GIT_SHORT}
                        if [ "${IMAGE_TAG}" = "v2" ]; then
                            docker push ${IMAGE_REPO}:latest
                        fi
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            when { branch 'main' }
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl apply -f k8s/00-namespace.yaml
                        kubectl apply -f k8s/ -n ${K8S_NAMESPACE} --recursive=false
                        kubectl -n ${K8S_NAMESPACE} set image deployment/aceest-v2 \
                            app=${IMAGE_REPO}:${IMAGE_TAG}-${GIT_SHORT} || true
                        kubectl -n ${K8S_NAMESPACE} rollout status deployment/aceest-v2 --timeout=180s
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker rmi ${IMAGE_TEST} || true'
            archiveArtifacts artifacts: 'coverage.xml,pytest-junit.xml', allowEmptyArchive: true
        }
        success {
            echo "Build OK: ${IMAGE_REPO}:${IMAGE_TAG} (${GIT_SHORT})"
        }
        failure {
            echo "Build FAILED on ${env.BRANCH_NAME} @ ${env.GIT_SHORT}"
        }
    }
}
