// 크롤러 파이프라인
pipeline {
    agent {
        kubernetes {
            cloud 'kubernetes'
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: "slave"
    app: "crawler-agent"
spec:
  nodeSelector:
    workload: core
  serviceAccountName: jenkins-agent
  containers:
  - name: python
    image: "python:3.10-slim"   # 🔑 ECR 이미지 참조 제거 (빌드 후 사용)
    command: ["sleep"]
    args: ["infinity"]
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1"
  - name: podman
    image: "quay.io/podman/stable"
    command: ["sleep"]
    args: ["infinity"]
    securityContext:
      privileged: true
  - name: aws-cli
    image: "amazon/aws-cli:latest"
    command: ["sleep"]
    args: ["infinity"]
  - name: jnlp
    image: "jenkins/inbound-agent:3327.v868139a_d00e0-6"
    args: ["\$(JENKINS_AGENT_NAME)", "\$(JENKINS_SECRET)"]
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
"""
        }
    }

    environment {
        AWS_ACCOUNT_ID   = '150297826798'
        AWS_REGION       = 'ap-northeast-2'
        ECR_REGISTRY     = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        ECR_REPOSITORY   = 'crawler'
        INFRA_REPO_URL   = 'git@github.com:KOSA-CloudArchitect/infra.git'
        GITHUB_REPO      = 'https://github.com/KOSA-CloudArchitect/crawler'
        COMMIT_HASH      = ""
        FULL_IMAGE_NAME  = ""
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    env.COMMIT_HASH       = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.GITHUB_COMMIT_URL = "${env.GITHUB_REPO}/commit/${env.COMMIT_HASH}"
                    env.FULL_IMAGE_NAME   = "${env.ECR_REGISTRY}/${env.ECR_REPOSITORY}:${env.COMMIT_HASH}"
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Push to ECR') {
            when { branch 'main' }
            steps {
                script {
                    def ecrPassword = container('aws-cli') {
                        withCredentials([aws(credentialsId: 'aws-credentials-manual-test')]) {
                            return sh(
                                script: "aws ecr get-login-password --region ${env.AWS_REGION}",
                                returnStdout: true
                            ).trim()
                        }
                    }

                    container('podman') {
                        sh "echo '${ecrPassword}' | podman login --username AWS --password-stdin ${env.ECR_REGISTRY}"
                        sh "podman build -t ${env.FULL_IMAGE_NAME} ."
                        sh "podman push ${env.FULL_IMAGE_NAME}"
                    }

                    echo "FULL_IMAGE_NAME = ${env.FULL_IMAGE_NAME}"
                    echo "COMMIT_HASH     = ${env.COMMIT_HASH}"
                    echo "GITHUB_COMMIT_URL = ${env.GITHUB_COMMIT_URL}"
                }
            }
        }

        stage('Verification') {
            steps {
                container('python') {
                    echo 'Running Linter, Unit Tests, etc. on the newly built image.'
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
            discordSend(
                description: "✅ 크롤러 CI/CD 파이프라인 성공!\n\n📌 이미지: `${env.FULL_IMAGE_NAME}`\n🔗 GitHub Commit: [${env.COMMIT_HASH}](${env.GITHUB_COMMIT_URL})",
                footer: "빌드 번호: ${env.BUILD_NUMBER}",
                link: env.BUILD_URL,
                result: currentBuild.currentResult,
                title: "크롤러 Jenkins Job",
                webhookURL: "https://discord.com/api/webhooks/1415897323028086804/4FgLSXOR5RU25KqJdK8MSgoAjxAabGzluiNpP44pBGWAWXcVBOfMjxyu0pmPpmqEO5sa"
            )
        }
        failure {
            discordSend(
                description: "❌ 크롤러 CI/CD 파이프라인 실패\n\n🔗 GitHub Commit: [${env.COMMIT_HASH}](${env.GITHUB_COMMIT_URL})",
                footer: "빌드 번호: ${env.BUILD_NUMBER}",
                link: env.BUILD_URL,
                result: currentBuild.currentResult,
                title: "크롤러 Jenkins Job",
                webhookURL: "https://discord.com/api/webhooks/1415897323028086804/4FgLSXOR5RU25KqJdK8MSgoAjxAabGzluiNpP44pBGWAWXcVBOfMjxyu0pmPpmqEO5sa"
            )
        }
    }
}

