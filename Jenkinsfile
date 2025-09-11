// Jenkinsfile for 'crawler' repository

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
        // Checkout, Verification, Build & Push to ECR 스테이지는 이전과 동일
        stage('Checkout') { /* ... */ }
        stage('Verification') { /* ... */ }
        stage('Build & Push to ECR') { /* ... */ }

        // 이 스테이지만 수정됩니다.
        stage('Update Infra Repository') {
            when { branch 'main' }
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'github-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                    sh """
                        # git 명령어에 사용할 SSH 키를 직접 지정
                        export GIT_SSH_COMMAND="ssh -i ${SSH_KEY} -o IdentitiesOnly=yes"
                        
                        # GitHub 호스트 키 검증 비활성화
                        mkdir -p ~/.ssh
                        echo "Host github.com\n  StrictHostKeyChecking no" > ~/.ssh/config
                        
                        # Infra 리포지토리 클론
                        git clone ${INFRA_REPO_URL} infra_repo
                        cd infra_repo

                        # 1. image 디렉토리가 없으면 생성
                        mkdir -p image

                        # 2. 최신 이미지 태그를 image/crawler.txt 파일에 덮어쓰기
                        echo "${FULL_IMAGE_NAME}" > image/crawler.txt

                        # 3. Git 설정 및 변경사항 푸시
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
}
