# Infrastructure as Code (IaC)

이 디렉토리는 LangChain LangGraph Agent 프로젝트의 인프라스트럭처를 코드로 관리하는 파일들을 포함합니다. 온프레미스와 클라우드 모두에서 프로덕션 배포가 가능하도록 Kubernetes 매니페스트와 Terraform 예제를 제공합니다. Terraform은 개인 환경에서 전체 E2E 검증을 아직 완료하지 않았으므로 적용 전에 `plan` 결과를 반드시 검토하세요.

## 구조

```
infra/
├── terraform/          # AWS Cloud 배포를 위한 Terraform 코드
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf
│   ├── security.tf
│   ├── rds.tf
│   ├── ecr.tf
│   ├── ecs.tf
│   ├── alb.tf
│   ├── s3.tf
│   ├── secrets.tf
│   └── README.md
├── k8s/                # On-premise/Cloud Kubernetes 배포를 위한 매니페스트
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml.example
│   ├── postgres-statefulset.yaml
│   ├── postgres-init-configmap.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── ingress.yaml
│   └── README.md
└── ci-cd/              # CI/CD 파이프라인 설정
    ├── github-actions-aws.yml
    ├── github-actions-k8s.yml
    └── README.md
```

## 배포 옵션 (K8s 우선, AWS Terraform 예제 제공)

기본 배포 경로는 Kubernetes입니다. on-prem 클러스터나 클라우드 매니지드 K8s(EKS/GKE/AKS 등)에 그대로 적용할 수 있으며, 로깅/모니터링 예제가 포함돼 있습니다. AWS ECS Fargate용 Terraform 예제도 제공하지만, 전체 검증 전이므로 신중히 사용하세요.

### 1. AWS Cloud 배포 (Terraform 예제, 전체 검증 전)

AWS ECS Fargate를 사용한 클라우드 배포입니다.

**주요 구성 요소:**
- VPC, Subnets, NAT Gateway
- RDS PostgreSQL (pgvector 지원)
- ECS Fargate (Backend + Frontend)
- Application Load Balancer
- ECR (Docker 이미지 저장소)
- S3 (파일 저장, 선택적)
- Secrets Manager

**사용 방법:**
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

자세한 내용은 [terraform/README.md](./terraform/README.md)를 참고하세요.

### 2. On-premise / Cloud Kubernetes 배포

Kubernetes 클러스터(온프레미스 또는 매니지드)에 배포합니다.

**주요 구성 요소:**
- Namespace
- PostgreSQL StatefulSet
- Backend Deployment & Service
- Frontend Deployment & Service
- Ingress
- ConfigMap & Secrets
- PersistentVolumeClaim

**사용 방법:**
```bash
kubectl apply -f infra/k8s/
```

자세한 내용은 [k8s/README.md](./k8s/README.md)를 참고하세요.

**모니터링/로깅 추가:** `infra/k8s/MONITORING.md`, `prometheus-*.yaml`, `loki-*.yaml`, `promtail-*.yaml`, `grafana-*.yaml` 파일을 참고해 Prometheus/Grafana/Loki 스택을 함께 배포할 수 있습니다.

## CI/CD

자동 배포를 위한 GitHub Actions 워크플로우가 제공됩니다.

- **AWS 배포**: `ci-cd/github-actions-aws.yml`
- **Kubernetes 배포**: `ci-cd/github-actions-k8s.yml`

자세한 내용은 [ci-cd/README.md](./ci-cd/README.md)를 참고하세요.

## 레포지토리 구조 선택

### Monorepo 방식 (현재 구조)

현재 프로젝트는 **Monorepo 방식**으로 구성되어 있습니다. 애플리케이션 코드와 인프라 코드가 같은 레포지토리에 있습니다.

**장점:**
- 코드와 인프라 코드의 버전 관리가 일치
- 변경 사항 추적이 용이
- 배포 스크립트와 애플리케이션 코드가 함께 관리

**단점:**
- 레포지토리 크기 증가
- 인프라 코드 접근 권한이 애플리케이션 코드와 동일

### 별도 레포지토리 방식

인프라 코드를 별도 레포지토리로 분리하려면:

1. 상위 디렉토리에서 새 레포지토리 생성:
   ```bash
   cd ..
   mkdir langchain-langgraph-agent-infra
   cd langchain-langgraph-agent-infra
   git init
   ```

2. `infra/` 디렉토리 내용 복사:
   ```bash
   cp -r langchain-langgraph-agent/infra/* .
   ```

3. 별도로 관리

**장점:**
- 인프라 코드와 애플리케이션 코드의 접근 권한 분리 가능
- 인프라 코드만 별도로 버전 관리

**단점:**
- 코드와 인프라 코드의 동기화가 어려움
- 배포 시 두 레포지토리를 모두 확인해야 함

## 권장 사항

대부분의 경우 **Monorepo 방식**을 권장합니다:
- 소규모/중규모 프로젝트에 적합
- 버전 관리가 간단
- CI/CD 파이프라인 구성이 용이

별도 레포지토리가 필요한 경우:
- 대규모 조직에서 인프라 팀과 개발 팀이 분리된 경우
- 여러 프로젝트에서 공통 인프라 코드를 공유하는 경우
- 인프라 코드에 대한 접근 권한을 엄격히 제어해야 하는 경우

## 다음 단계

1. **Terraform 배포**: [terraform/README.md](./terraform/README.md) 참고
2. **Kubernetes 배포**: [k8s/README.md](./k8s/README.md) 참고
3. **CI/CD 설정**: [ci-cd/README.md](./ci-cd/README.md) 참고

