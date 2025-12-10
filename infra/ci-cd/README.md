# CI/CD Pipeline

이 디렉토리는 자동 배포를 위한 CI/CD 파이프라인 설정 파일을 포함합니다.

## GitHub Actions

### AWS 배포 (`github-actions-aws.yml`)

AWS ECS에 자동 배포하는 파이프라인입니다.

#### 필요한 GitHub Secrets

- `AWS_ACCESS_KEY_ID`: AWS 액세스 키 ID
- `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 액세스 키
- `DB_PASSWORD`: RDS 데이터베이스 비밀번호
- `SECRET_KEY`: JWT 시크릿 키
- `OPENAI_API_KEY`: OpenAI API 키

#### 사용 방법

1. `.github/workflows/` 디렉토리에 파일 복사:
   ```bash
   mkdir -p .github/workflows
   cp infra/ci-cd/github-actions-aws.yml .github/workflows/deploy-aws.yml
   ```

2. GitHub Repository Settings > Secrets에 필요한 시크릿 추가

3. `main` 브랜치에 푸시하면 자동으로 빌드 및 배포됩니다

### Kubernetes 배포 (`github-actions-k8s.yml`)

Kubernetes 클러스터에 자동 배포하는 파이프라인입니다.

#### 필요한 GitHub Secrets

- `REGISTRY_USERNAME`: 컨테이너 레지스트리 사용자명
- `REGISTRY_PASSWORD`: 컨테이너 레지스트리 비밀번호
- `KUBECONFIG`: Kubernetes 클러스터 kubeconfig (base64 인코딩)

#### 사용 방법

1. `.github/workflows/` 디렉토리에 파일 복사:
   ```bash
   mkdir -p .github/workflows
   cp infra/ci-cd/github-actions-k8s.yml .github/workflows/deploy-k8s.yml
   ```

2. 파일에서 `REGISTRY` 환경 변수를 실제 레지스트리 주소로 변경

3. GitHub Repository Settings > Secrets에 필요한 시크릿 추가

4. `main` 브랜치에 푸시하면 자동으로 빌드 및 배포됩니다

## GitLab CI

GitLab CI를 사용하는 경우 `.gitlab-ci.yml` 파일을 프로젝트 루트에 추가할 수 있습니다.

## 수동 배포 스크립트

CI/CD를 사용하지 않는 경우, 수동 배포 스크립트를 사용할 수 있습니다.

### AWS 배포 스크립트

```bash
#!/bin/bash
# deploy-aws.sh

set -e

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <ECR_URL>

# 프로덕션 이미지 빌드 및 푸시
docker build -t <ECR_URL>/langchain-langgraph-agent-backend:latest -f backend/Dockerfile.prod .
docker push <ECR_URL>/langchain-langgraph-agent-backend:latest

docker build -t <ECR_URL>/langchain-langgraph-agent-frontend:latest -f frontend/Dockerfile.prod ./frontend
docker push <ECR_URL>/langchain-langgraph-agent-frontend:latest

# ECS 서비스 업데이트
aws ecs update-service --cluster <cluster-name> --service <backend-service> --force-new-deployment
aws ecs update-service --cluster <cluster-name> --service <frontend-service> --force-new-deployment
```

### Kubernetes 배포 스크립트

```bash
#!/bin/bash
# deploy-k8s.sh

set -e

# 프로덕션 이미지 빌드 및 푸시
docker build -t your-registry/langchain-langgraph-agent-backend:latest -f backend/Dockerfile.prod .
docker push your-registry/langchain-langgraph-agent-backend:latest

docker build -t your-registry/langchain-langgraph-agent-frontend:latest -f frontend/Dockerfile.prod ./frontend
docker push your-registry/langchain-langgraph-agent-frontend:latest

# Kubernetes 배포
kubectl apply -f infra/k8s/

# 롤아웃 재시작
kubectl rollout restart deployment/backend -n langchain-langgraph-agent
kubectl rollout restart deployment/frontend -n langchain-langgraph-agent
```

