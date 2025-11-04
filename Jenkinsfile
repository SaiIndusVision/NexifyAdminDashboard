pipeline {
    agent any

    environment {
        IMAGE_NAME   = "nexify_staging:v1"
        CODE_DIR     = "/home/NexifyStaging"   // repo clone location
        COMPOSE_DIR  = "/home/server"          // where docker-compose.yml lives
        REPO_URL     = "https://github.com/IndusVision/NexifyAdminDashboard.git"
        BRANCH_NAME  = "staging"
        CHAT_WEBHOOK = "https://chat.googleapis.com/v1/spaces/AAQA7BaGsTI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=1QsVTw73BTPAktu56LoIZQPSAcJ6Fa_KBcxsKQlCR0U"
    }

    stages {
        stage('Clone or Update Repo') {
            steps {
                echo "📥 Cloning/Updating ${BRANCH_NAME} branch into ${CODE_DIR}..."
                dir("${CODE_DIR}") {
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "*/${BRANCH_NAME}"]],
                        userRemoteConfigs: [[
                            url: "${REPO_URL}",
                            credentialsId: "Github-credentials"
                        ]]
                    ])
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image: ${IMAGE_NAME}..."
                dir("${CODE_DIR}") {
                    sh '''
                        if [ ! -f Dockerfile ]; then
                            echo "❌ Dockerfile not found in ${CODE_DIR}"
                            exit 1
                        fi

                        if command -v docker >/dev/null 2>&1; then
                            docker build -t ${IMAGE_NAME} .
                        elif [ -x "/usr/bin/docker" ]; then
                            /usr/bin/docker build -t ${IMAGE_NAME} .
                        else
                            echo "❌ Docker not found. Please install Docker or add to PATH."
                            exit 1
                        fi
                    '''
                }
            }
        }

        stage('Restart Docker Services') {
            steps {
                echo '🔁 Restarting Docker containers...'
                dir("${COMPOSE_DIR}") {
                    sh '''
                        if command -v docker-compose >/dev/null 2>&1; then
                            docker-compose down || true
                            docker-compose up -d --build
                        elif command -v docker >/dev/null 2>&1; then
                            docker compose down || true
                            docker compose up -d --build
                        else
                            echo "❌ docker-compose not found. Please install docker-compose or add to PATH."
                            exit 1
                        fi
                    '''
                }
            }
        }

        stage('Restart Nginx') {
            steps {
                echo '🌐 Restarting Nginx service...'
                sh '''
                    if command -v nginx >/dev/null 2>&1; then
                        sudo nginx -t && sudo systemctl restart nginx
                        echo "✅ Nginx restarted successfully"
                    else
                        echo "⚠️ Nginx not installed on host or not in PATH"
                    fi
                '''
            }
        }
    }

    post {
        always {
            echo '🧹 Cleaning up Docker system...'
            sh '''
                docker image prune -f
                docker container prune -f
                docker volume prune -f
                docker network prune -f
            '''
        }

        success {
            echo '✅ Staging Deployment completed successfully!'
            sh """
                curl -X POST -H 'Content-Type: application/json' \
                -d '{
                      "text": "✅ *Staging Deployment Success*\\nJob: ${JOB_NAME} #${BUILD_NUMBER}\\nURL: ${BUILD_URL}"
                    }' \
                '${CHAT_WEBHOOK}'
            """
        }

        failure {
            echo '❌ Staging Deployment failed. Check logs.'
            sh """
                curl -X POST -H 'Content-Type: application/json' \
                -d '{
                      "text": "❌ *Staging Deployment Failed*\\nJob: ${JOB_NAME} #${BUILD_NUMBER}\\nURL: ${BUILD_URL}"
                    }' \
                '${CHAT_WEBHOOK}'
            """
        }
    }
}
