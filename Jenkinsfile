// Jenkinsfile for 'crawler' repository

pipeline {
    agent {
        kubernetes {
            cloud 'kubernetes'
            yamlFile 'pod-template.yaml'
        }
    }

    environment {
        AWS_ACCOUNT_ID   = '150297826798' // 올바른 AWS 계정 ID
        AWS_REGION       = 'ap-northeast-2'
        ECR_REGISTRY     = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        ECR_REPOSITORY   = 'crawler'
        INFRA_REPO_URL   = 'git@github.com:KOSA-CloudArchitect/infra.git' // SSH 주소 방식
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verification') { // Develop 브랜치 Push 또는 Main 브랜치 PR 시 실행
            steps {
                container('python') {
                    echo 'Running Linter, Unit Tests, etc.'
                    // sh 'pip install pylint'
                    // sh 'pylint src/**/*.py'
                }
            }
        }

        stage('Build & Push to ECR') {
            when { branch 'main' } // Main 브랜치일 때만 실행
            steps {
                script {
                    def imageTag = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.FULL_IMAGE_NAME = "${ECR_REGISTRY}/${ECR_REPOSITORY}:${imageTag}"
                    
                    container('podman') {
                        withCredentials([aws(credentialsId: 'aws-credentials-for-ecr')]) {
                            sh "aws ecr get-login-password --region ${AWS_REGION} | podman login --username AWS --password-stdin ${ECR_REGISTRY}"
                            sh "podman build -t ${FULL_IMAGE_NAME} ."
                            sh "podman push ${FULL_IMAGE_NAME}"
                        }
                    }
                }
            }
        }

        stage('Update Infra Repository') {
            when { branch 'main' } // Main 브랜치일 때만 실행
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'github-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                    sh """
                        # Git SSH 명령을 위한 설정
                        mkdir -p ~/.ssh
                        echo "Host github.com\n  StrictHostKeyChecking no" > ~/.ssh/config
                        
                        # Infra Repo를 별도 디렉토리에 클론
                        git clone ${INFRA_REPO_URL} infra_repo
                        cd infra_repo

                        # YAML 파일에서 이미지 태그 업데이트 (sed 명령어 사용)
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
