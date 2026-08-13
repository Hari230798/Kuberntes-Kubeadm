pipeline {
    agent any

    environment {
        // ---- Change this to match your Docker Hub repo ----
        DOCKER_REPO   = 'your-dockerhub-username/devops-demo'
        // ---------------------------------------------------
        IMAGE_TAG     = "${BUILD_NUMBER}"
        K8S_NAMESPACE = 'devops-demo'
        RELEASE_NAME  = 'devops-demo'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r app/requirements.txt
                    cd app && python -m pytest -v
                '''
            }
        }

        stage('Build & Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker build -t $DOCKER_REPO:$IMAGE_TAG -t $DOCKER_REPO:latest .
                        docker push $DOCKER_REPO:$IMAGE_TAG
                        docker push $DOCKER_REPO:latest
                    '''
                }
            }
        }

        stage('Deploy to kubeadm (Helm)') {
            steps {
                // 'kubeconfig' is a Jenkins "Secret file" credential holding your cluster's kubeconfig.
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        helm upgrade --install $RELEASE_NAME helm/myapp \
                            --namespace $K8S_NAMESPACE --create-namespace \
                            --set image.repository=$DOCKER_REPO \
                            --set image.tag=$IMAGE_TAG \
                            --wait --timeout 120s

                        kubectl -n $K8S_NAMESPACE rollout status deploy/$RELEASE_NAME-myapp
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'
        }
        success {
            echo "Deployed $DOCKER_REPO:$IMAGE_TAG to namespace $K8S_NAMESPACE"
        }
    }
}
