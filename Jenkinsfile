pipeline {
    agent {
        kubernetes {
            cloud 'kubernetes'
            yamlFile 'pod-template.yaml'
        }
    }

    environment {
        AWS_ACCOUNT_ID   = '150297826798'
        AWS_REGION       = 'ap-northeast-2'
        ECR_REGISTRY     = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        ECR_REPOSITORY   = 'crawler'
        INFRA_REPO_URL   = 'git@github.com:KOSA-CloudArchitect/infra.git'
        GITHUB_REPO      = 'https://github.com/KOSA-CloudArchitect/crawler'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verification') {
            steps {
                container('python') {
                    echo 'Running Linter, Unit Tests, etc.'
                }
            }
        }

        stage('Build & Push to ECR') {
            when { branch 'main' }
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.COMMIT_HASH = commitHash
                    env.GITHUB_COMMIT_URL = "${GITHUB_REPO}/commit/${commitHash}"

                    env.FULL_IMAGE_NAME = "${ECR_REGISTRY}/${ECR_REPOSITORY}:${commitHash}"
                    
                    def ecrPassword = container('aws-cli') {
                        withCredentials([aws(credentialsId: 'aws-credentials-manual-test')]) {
                            sh(script: "aws ecr get-login-password --region ${AWS_REGION}", returnStdout: true).trim()
                        }
                    }

                    container('podman') {
                        sh "echo '${ecrPassword}' | podman login --username AWS --password-stdin ${ECR_REGISTRY}"
                        sh "podman build -t ${FULL_IMAGE_NAME} ."
                        sh "podman push ${FULL_IMAGE_NAME}"
                    }
                }
            }
        }

        stage('Update Infra Repository') {
            when { branch 'main' }
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'github-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                    sh """
                        export GIT_SSH_COMMAND="ssh -i ${SSH_KEY} -o IdentitiesOnly=yes"

                        mkdir -p ~/.ssh
                        echo "Host github.com\n  StrictHostKeyChecking no" > ~/.ssh/config

                        git clone ${INFRA_REPO_URL} infra_repo
                        cd infra_repo

                        mkdir -p image
                        echo "${FULL_IMAGE_NAME}" > image/crawler.txt

                        git config user.email "jenkins@your-domain.com"
                        git config user.name "Jenkins CI"
                        git add image/crawler.txt
                        git commit -m "Update crawler image to ${FULL_IMAGE_NAME}"
                        git push origin main
                    """
                }
            }
        }
    }

    post {
        success {
            discordSend description: "✅ 크롤러 CI/CD 파이프라인 성공!\n\n📌 이미지: `${env.FULL_IMAGE_NAME}`\n🔗 GitHub Commit: [${env.COMMIT_HASH}](${env.GITHUB_COMMIT_URL})",
                        footer: "빌드 번호: ${env.BUILD_NUMBER}",
                        link: env.BUILD_URL,
                        result: currentBuild.currentResult,
                        title: "크롤러 Jenkins Job",
                        webhookURL: "https://discord.com/api/webhooks/1415897323028086804/4FgLSXOR5RU25KqJdK8MSgoAjxAabGzluiNpP44pBGWAWXcVBOfMjxyu0pmPpmqEO5sa"
        }
        failure {
            discordSend description: "❌ 크롤러 CI/CD 파이프라인 실패\n\n🔗 GitHub Commit: [${env.COMMIT_HASH}](${env.GITHUB_COMMIT_URL})",
                        footer: "빌드 번호: ${env.BUILD_NUMBER}",
                        link: env.BUILD_URL,
                        result: currentBuild.currentResult,
                        title: "크롤러 Jenkins Job",
                        webhookURL: "https://discord.com/api/webhooks/1415897323028086804/4FgLSXOR5RU25KqJdK8MSgoAjxAabGzluiNpP44pBGWAWXcVBOfMjxyu0pmPpmqEO5sa"
        }
    }
}

