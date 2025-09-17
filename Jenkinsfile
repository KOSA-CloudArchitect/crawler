// Jenkinsfile (Final Version for Multibranch with Enhanced Discord Notifications)

pipeline {
    agent {
        kubernetes {
            cloud 'kubernetes'
            yamlFile 'pod-template.yaml'
        }
    }

    environment {
        AWS_ACCOUNT_ID    = '914215749228'
        AWS_REGION        = 'ap-northeast-2'
        ECR_REGISTRY      = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        ECR_REPOSITORY    = 'crawler'
        INFRA_REPO_URL    = 'git@github.com:KOSA-CloudArchitect/infra.git'
        GITHUB_REPO       = 'https://github.com/KOSA-CloudArchitect/crawler'
    }

    stages {
        // Stage 1: Initialize variables available to all branches
        stage('⚙️ Initialize') {
            steps {
                script {
                    // COMMIT_HASH와 GITHUB_COMMIT_URL을 여기서 미리 정의하여
                    // 어떤 브랜치에서 실패하더라도 post 단계에서 참조할 수 있도록 합니다.
                    env.COMMIT_HASH        = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.GITHUB_COMMIT_URL  = "${env.GITHUB_REPO}/commit/${env.COMMIT_HASH}"
                }
            }
        }

        // Stage 2: Verification for 'develop' branch and Pull Requests
        stage('✅ Verification & Build Check') {
            when {
                anyOf {
                    branch 'develop'
                    changeRequest() // Triggered for Pull Requests
                }
            }
            steps {
                container('python') {
                    echo "Running Verification tasks (Linter, Unit Tests, etc.)..."
                }
                container('podman') {
                    echo "Verifying Docker build..."
                    sh "podman build -t crawler-build-test ."
                    echo "Docker build check completed successfully."
                }
            }
        }

        // Stage 3 & 4: For 'main' branch only (Actual Deployment)
        stage('🚀 Build & Push to ECR') {
            when { branch 'main' }
            steps {
                script {
                    // FULL_IMAGE_NAME은 main 브랜치에서만 사용되므로 여기서 정의합니다.
                    env.FULL_IMAGE_NAME    = "${env.ECR_REGISTRY}/${env.ECR_REPOSITORY}:${env.COMMIT_HASH}"

                    def ecrPassword = container('aws-cli') {
                        withCredentials([aws(credentialsId: 'aws-credentials-manual-test')]) {
                            return sh(script: "aws ecr get-login-password --region ${env.AWS_REGION}", returnStdout: true).trim()
                        }
                    }

                    container('podman') {
                        sh "echo '${ecrPassword}' | podman login --username AWS --password-stdin ${env.ECR_REGISTRY}"
                        sh "podman build -t ${env.FULL_IMAGE_NAME} ."
                        sh "podman push ${env.FULL_IMAGE_NAME}"
                    }
                    echo "Successfully pushed image: ${env.FULL_IMAGE_NAME}"
                }
            }
        }

        stage('🌐 Update Infra Repository') {
            when { branch 'main' }
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'github-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                    sh """
                        export GIT_SSH_COMMAND="ssh -i ${SSH_KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
                        git clone ${INFRA_REPO_URL} infra_repo
                        cd infra_repo
                        git config user.email "jenkins-ci@example.com"
                        git config user.name "Jenkins CI"
                        mkdir -p image
                        echo "${FULL_IMAGE_NAME}" > image/crawler.txt
                        git add image/crawler.txt
                        git commit -m "Update crawler image to ${FULL_IMAGE_NAME}" || true
                        git push origin main
                    """
                }
            }
        }
    }

    // Post-build actions with detailed Discord notifications
    post {
        always {
            cleanWs()
        }
        success {
            // main 브랜치 빌드 성공 시에만 상세 알림을 보냅니다.
            if (env.BRANCH_NAME == 'main') {
                discordSend(
                    description: "✅ 크롤러 CI/CD 파이프라인 성공!\n\n📌 이미지: `${env.FULL_IMAGE_NAME}`\n🔗 GitHub Commit: [${env.COMMIT_HASH}](${env.GITHUB_COMMIT_URL})",
                    footer: "빌드 번호: ${env.BUILD_NUMBER}",
                    link: env.BUILD_URL,
                    result: currentBuild.currentResult,
                    title: "크롤러 Jenkins Job",
                    webhookURL: "https://discord.com/api/webhooks/1415897323028086804/4FgLSXOR5RU25KqJdK8MSgoAjxAabGzluiNpP44pBGWAWXcVBOfMjxyu0pmPpmqEO5sa"
                )
            }
        }
        failure {
            discordSend(
                description: "❌ 크롤러 CI/CD 파이프라인 실패\n\n- 브랜치: `${env.BRANCH_NAME}`\n🔗 GitHub Commit: [${env.COMMIT_HASH}](${env.GITHUB_COMMIT_URL})",
                footer: "빌드 번호: ${env.BUILD_NUMBER}",
                link: env.BUILD_URL,
                result: currentBuild.currentResult,
                title: "크롤러 Jenkins Job",
                webhookURL: "https://discord.com/api/webhooks/1415897323028086804/4FgLSXOR5RU25KqJdK8MSgoAjxAabGzluiNpP44pBGWAWXcVBOfMjxyu0pmPpmqEO5sa"
            )
        }
    }
}
