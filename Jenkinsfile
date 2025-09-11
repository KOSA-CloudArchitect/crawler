// Jenkinsfile for 'crawler' repository (Final Version)

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
                    def imageTag = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.FULL_IMAGE_NAME = "${ECR_REGISTRY}/${ECR_REPOSITORY}:${imageTag}"
                    
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
                        # git 명령어에 사용할 SSH 키를 직접 지정 (핵심 수정 사항)
                        export GIT_SSH_COMMAND="ssh -i ${SSH_KEY} -o IdentitiesOnly=yes"
                        
                        # GitHub 호스트 키 검증 비활성화
                        mkdir -p ~/.ssh
                        echo "Host github.com\n  StrictHostKeyChecking no" > ~/.ssh/config
                        
                        # Infra 리포지토리 클론
                        git clone ${INFRA_REPO_URL} infra_repo
                        cd infra_repo

                        # YAML 파일에서 이미지 태그 업데이트
                        # !! 중요: 아래 파일 경로는 Infra Repo의 실제 구조에 맞게 반드시 수정해야 합니다 !!
                        sed -i "s|image: ${ECR_REGISTRY}/${ECR_REPOSITORY}:.*|image: ${FULL_IMAGE_NAME}|g" kubernetes/apps/crawler-deployment.yaml

                        # Git 설정 및 변경사항 푸시
                        git config user.email "jenkins@your-domain.com"
                        git config user.name "Jenkins CI"
                        git add .
                        git commit -m "Update crawler image to ${FULL_IMAGE_NAME}"
                        git push origin main
                    """
                }
            }
        }
    }
}
