# Terraform Infrastructure as Code

이 디렉토리는 AWS Cloud에 LangChain LangGraph Agent를 배포하기 위한 Terraform IaC 코드를 포함합니다.

## 구조

- `main.tf`: Terraform 및 AWS Provider 설정
- `variables.tf`: 변수 정의
- `outputs.tf`: 출력 값 정의
- `vpc.tf`: VPC, Subnet, NAT Gateway 등 네트워크 리소스
- `security.tf`: Security Groups
- `rds.tf`: RDS PostgreSQL (pgvector 지원)
- `ecr.tf`: ECR 리포지토리
- `ecs.tf`: ECS Cluster, Task Definitions, Services
- `alb.tf`: Application Load Balancer
- `s3.tf`: S3 버킷 (파일 저장용)
- `secrets.tf`: AWS Secrets Manager 설정

## 사전 요구사항

1. AWS CLI 설치 및 구성
2. Terraform >= 1.5.0 설치
3. AWS 자격 증명 설정 (`aws configure` 또는 환경 변수)

## 사용 방법

### 1. 변수 파일 생성

```bash
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` 파일을 편집하여 필요한 값들을 설정하세요:

```hcl
aws_region = "ap-northeast-2"
environment = "dev"
db_password = "your-secure-password"
openai_api_key = "your-openai-api-key"
secret_key = "your-secret-key"
```

### 2. Terraform 초기화

```bash
terraform init
```

### 3. 계획 확인

```bash
terraform plan
```

### 4. 인프라 배포

```bash
terraform apply
```

### 5. 출력 값 확인

배포 후 다음 명령으로 출력 값을 확인할 수 있습니다:

```bash
terraform output
```

주요 출력:
- `alb_dns_name`: ALB DNS 이름 (애플리케이션 접근 URL)
- `rds_endpoint`: RDS 엔드포인트
- `ecr_backend_repository_url`: Backend ECR 리포지토리 URL
- `ecr_frontend_repository_url`: Frontend ECR 리포지토리 URL

### 6. 인프라 삭제

```bash
terraform destroy
```

## Docker 이미지 빌드 및 푸시

### Backend 이미지

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <ECR_URL>

# 프로덕션 이미지 빌드 (Gunicorn + Uvicorn workers 사용)
docker build -t <ECR_URL>/langchain-langgraph-agent-backend:latest -f backend/Dockerfile.prod .

# 이미지 푸시
docker push <ECR_URL>/langchain-langgraph-agent-backend:latest
```

### Frontend 이미지

```bash
# 프로덕션 이미지 빌드 (Nginx 사용)
docker build -t <ECR_URL>/langchain-langgraph-agent-frontend:latest -f frontend/Dockerfile.prod ./frontend

# 이미지 푸시
docker push <ECR_URL>/langchain-langgraph-agent-frontend:latest
```

## CI/CD 통합

GitHub Actions 또는 GitLab CI를 사용하여 자동 배포를 설정할 수 있습니다. 
`infra/ci-cd/` 디렉토리의 예제를 참고하세요.

## 비용 최적화

- 개발 환경에서는 `db_instance_class`를 `db.t3.micro`로 설정
- `backend_desired_count`와 `frontend_desired_count`를 1로 설정
- 불필요한 경우 `enable_s3_storage`를 `false`로 설정

## 보안 고려사항

- `terraform.tfvars` 파일은 절대 Git에 커밋하지 마세요
- 프로덕션 환경에서는 `db_password`, `secret_key` 등을 AWS Secrets Manager에 저장
- RDS는 Private Subnet에 배치되어 있으며, ECS Tasks에서만 접근 가능
- S3 버킷은 Public Access가 차단되어 있습니다

## 문제 해결

### ECS Task가 시작되지 않는 경우

1. CloudWatch Logs 확인: `/ecs/langchain-langgraph-agent-backend`
2. Security Group 규칙 확인
3. Task Definition의 환경 변수 확인
4. Secrets Manager에 필요한 시크릿이 있는지 확인

### RDS 연결 실패

1. Security Group에서 ECS Tasks의 Security Group이 허용되어 있는지 확인
2. RDS 엔드포인트가 올바른지 확인
3. 데이터베이스 자격 증명 확인

