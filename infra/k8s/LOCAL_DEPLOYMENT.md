# 로컬 Kubernetes 배포 테스트 가이드

이 가이드는 로컬 환경에서 Kubernetes를 사용하여 LangChain LangGraph Agent를 배포하고 테스트하는 방법을 설명합니다.

## 사전 요구사항

### 1. Kubernetes 클러스터 설정

로컬에서 Kubernetes를 실행하기 위한 옵션:

#### 옵션 A: Docker Desktop (Mac/Windows)
- Docker Desktop 설치
- Settings > Kubernetes에서 "Enable Kubernetes" 활성화
- kubectl이 자동으로 설치됨

#### 옵션 B: minikube
```bash
# minikube 설치 (Mac)
brew install minikube

# minikube 시작
minikube start

# kubectl 설정
minikube kubectl -- get pods -A
```

#### 옵션 C: kind (Kubernetes in Docker)
```bash
# kind 설치
brew install kind  # Mac
# 또는: https://kind.sigs.k8s.io/docs/user/quick-start/

# 클러스터 생성
kind create cluster --name langchain-agent
```

### 2. 필수 도구 설치

```bash
# kubectl 설치 확인
kubectl version --client

# Docker 설치 확인
docker --version
```

### 3. Ingress Controller 설치 (선택사항)

Ingress를 사용하려면 Ingress Controller가 필요합니다:

```bash
# Nginx Ingress Controller 설치 (minikube)
minikube addons enable ingress

# 또는 kind/Docker Desktop의 경우
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

## 배포 단계

### 1. Secrets 파일 생성

```bash
cd infra/k8s

# secrets.yaml.example을 기반으로 secrets.yaml 생성
cp secrets.yaml.example secrets.yaml

# secrets.yaml 파일 편집하여 실제 값 설정
# 필수 항목:
# - SECRET_KEY: openssl rand -hex 32 로 생성
# - POSTGRES_PASSWORD: 데이터베이스 비밀번호
# - OPENAI_API_KEY: OpenAI API 키
```

또는 직접 편집:
```bash
nano secrets.yaml  # 또는 vim, code 등
```

**중요**: `secrets.yaml`은 Git에 커밋하지 마세요!

### 2. Docker 이미지 빌드

로컬에서 이미지를 빌드하고 Kubernetes에서 사용할 수 있도록 설정합니다.

#### 옵션 A: 로컬 이미지 사용 (권장 - 로컬 테스트)

```bash
# 프로젝트 루트에서 실행

# Backend 이미지 빌드
docker build -t langchain-langgraph-agent-backend:latest -f backend/Dockerfile.prod .

# Frontend 이미지 빌드
docker build -t langchain-langgraph-agent-frontend:latest -f frontend/Dockerfile.prod ./frontend
```

**minikube를 사용하는 경우**, minikube의 Docker 데몬을 사용해야 합니다:
```bash
# minikube의 Docker 환경 사용
eval $(minikube docker-env)

# 이미지 빌드
docker build -t langchain-langgraph-agent-backend:latest -f backend/Dockerfile.prod .
docker build -t langchain-langgraph-agent-frontend:latest -f frontend/Dockerfile.prod ./frontend

# 원래 Docker 환경으로 복귀
eval $(minikube docker-env -u)
```

**kind를 사용하는 경우**, 이미지를 kind 클러스터로 로드:
```bash
kind load docker-image langchain-langgraph-agent-backend:latest --name langchain-agent
kind load docker-image langchain-langgraph-agent-frontend:latest --name langchain-agent
```

#### 옵션 B: 로컬 레지스트리 사용

```bash
# 로컬 레지스트리 시작
docker run -d -p 5500:5000 --name registry registry:2

# 이미지 태그 및 푸시
docker tag langchain-langgraph-agent-backend:latest localhost:5500/langchain-langgraph-agent-backend:latest
docker tag langchain-langgraph-agent-frontend:latest localhost:5500/langchain-langgraph-agent-frontend:latest

docker push localhost:5500/langchain-langgraph-agent-backend:latest
docker push localhost:5500/langchain-langgraph-agent-frontend:latest

# deployment.yaml에서 이미지 경로를 localhost:5500/... 로 변경
```

### 3. ConfigMap 설정 확인

`configmap.yaml`의 설정을 로컬 환경에 맞게 확인:

**Ingress 사용 시 (권장):**
```yaml
# CORS_ORIGINS: Ingress 도메인으로 설정
CORS_ORIGINS: "[\"http://langchain-agent.local\"]"

# VITE_API_BASE_URL: 상대 경로 사용 (빈 문자열) 또는 절대 경로
# 옵션 1 (권장): 빈 문자열 - 상대 경로 사용
VITE_API_BASE_URL: ""
# 옵션 2: 절대 경로 사용
# VITE_API_BASE_URL: "http://langchain-agent.local/api"
```

**Port Forwarding 사용 시:**
```yaml
# CORS_ORIGINS: localhost로 설정
CORS_ORIGINS: "[\"http://localhost:3000\", \"http://localhost:8000\"]"

# VITE_API_BASE_URL: localhost로 설정
VITE_API_BASE_URL: "http://localhost:8000"
```

**참고**: `VITE_API_BASE_URL`은 런타임에 주입되므로, ConfigMap 변경 후 Frontend Pod를 재시작하면 반영됩니다.

### 4. StorageClass 확인

로컬 환경에 맞는 StorageClass를 확인하고 필요시 수정:

```bash
# 사용 가능한 StorageClass 확인
kubectl get storageclass

# 기본 StorageClass 확인
kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

`backend-deployment.yaml`과 `postgres-statefulset.yaml`의 `storageClassName`을 확인하고 필요시 수정하세요.

**minikube**의 경우: `standard` 또는 `hostpath`
**kind**의 경우: `standard` 또는 `local-path` (local-path-provisioner 설치 필요)
**Docker Desktop**의 경우: `hostpath` 또는 `local-path`

### 5. 리소스 배포

```bash
cd infra/k8s

# 1. Namespace 생성
kubectl apply -f namespace.yaml

# 2. ConfigMap 생성
kubectl apply -f configmap.yaml
kubectl apply -f postgres-init-configmap.yaml

# 3. Secrets 생성
kubectl apply -f secrets.yaml

# 4. PostgreSQL 배포
kubectl apply -f postgres-statefulset.yaml

# 5. PostgreSQL이 준비될 때까지 대기
kubectl wait --for=condition=ready pod -l app=postgres -n langchain-langgraph-agent --timeout=300s

# 6. Backend 배포
kubectl apply -f backend-deployment.yaml

# 7. Frontend 배포
kubectl apply -f frontend-deployment.yaml

# 8. Ingress 배포 (선택사항)
kubectl apply -f ingress.yaml
```

또는 한 번에 배포:
```bash
kubectl apply -f .
```

### 6. 배포 상태 확인

```bash
# Namespace 확인
kubectl get namespace langchain-langgraph-agent

# Pod 상태 확인
kubectl get pods -n langchain-langgraph-agent

# Service 확인
kubectl get svc -n langchain-langgraph-agent

# Pod 로그 확인
kubectl logs -f deployment/backend -n langchain-langgraph-agent
kubectl logs -f deployment/frontend -n langchain-langgraph-agent
kubectl logs -f statefulset/postgres -n langchain-langgraph-agent
```

## 애플리케이션 접근

### 옵션 1: Port Forwarding (가장 간단)

```bash
# Backend 접근
kubectl port-forward svc/backend-service 8000:8000 -n langchain-langgraph-agent

# Frontend 접근 (다른 터미널)
kubectl port-forward svc/frontend-service 3000:80 -n langchain-langgraph-agent
```

브라우저에서:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**참고**: Frontend는 컨테이너 내부에서 포트 80을 사용하지만, 로컬에서는 3000 포트로 접근합니다.

### 옵션 2: NodePort Service 사용

Service 타입을 NodePort로 변경:

```yaml
# backend-deployment.yaml의 Service 부분 수정
spec:
  type: NodePort
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30080  # 30000-32767 범위
```

```bash
# minikube의 경우
minikube service backend-service -n langchain-langgraph-agent

# 또는 직접 접근
kubectl get svc backend-service -n langchain-langgraph-agent
# EXTERNAL-IP 또는 NodePort를 통해 접근
```

### 옵션 3: Ingress 사용 (권장 - Port Forwarding 불필요)

Ingress를 사용하면 Port Forwarding 없이 브라우저에서 직접 접근할 수 있습니다.

**1. Ingress Controller 설치 확인**
```bash
# Ingress Controller가 설치되어 있는지 확인
kubectl get ingressclass

# 설치되어 있지 않다면 (minikube)
minikube addons enable ingress

# 또는 kind/Docker Desktop의 경우
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

**2. Ingress 및 ConfigMap 적용**
```bash
# ConfigMap 업데이트 (CORS 및 VITE_API_BASE_URL 설정)
kubectl apply -f configmap.yaml

# Ingress 적용
kubectl apply -f ingress.yaml

# Frontend 재배포 (환경변수 변경 반영을 위해)
kubectl rollout restart deployment/frontend -n langchain-langgraph-agent
```

**3. /etc/hosts 파일 설정**
```bash
# 먼저 Ingress Controller의 IP 확인
kubectl get ingress -n langchain-langgraph-agent

# minikube 사용 시
MINIKUBE_IP=$(minikube ip)
echo "$MINIKUBE_IP langchain-agent.local" | sudo tee -a /etc/hosts
echo "$MINIKUBE_IP grafana.langchain-agent.local" | sudo tee -a /etc/hosts
echo "$MINIKUBE_IP prometheus.langchain-agent.local" | sudo tee -a /etc/hosts

# Docker Desktop 사용 시 (일반적으로 localhost 사용)
echo "127.0.0.1 langchain-agent.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 grafana.langchain-agent.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 prometheus.langchain-agent.local" | sudo tee -a /etc/hosts

# kind 사용 시
KIND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' langchain-agent-control-plane 2>/dev/null || echo "127.0.0.1")
echo "$KIND_IP langchain-agent.local" | sudo tee -a /etc/hosts
echo "$KIND_IP grafana.langchain-agent.local" | sudo tee -a /etc/hosts
echo "$KIND_IP prometheus.langchain-agent.local" | sudo tee -a /etc/hosts
```

**참고**: Ingress Controller가 LoadBalancer 타입이 아닌 경우 (예: minikube, kind), Ingress의 ADDRESS가 비어있을 수 있습니다. 
이 경우 Ingress Controller Service의 External IP를 확인하거나, NodePort를 사용해야 합니다.

**4. Ingress IP 확인 및 접근**
```bash
# Ingress 상태 확인
kubectl get ingress -n langchain-langgraph-agent

# minikube 사용 시
minikube service ingress-nginx-controller -n ingress-nginx

# 또는 직접 접근 (ADDRESS 컬럼의 IP 사용)
# 브라우저에서: http://langchain-agent.local
```

**5. 브라우저에서 접근**
- Frontend: http://langchain-agent.local
- Backend API: http://langchain-agent.local/api
- API Docs: http://langchain-agent.local/docs
- Grafana: http://grafana.langchain-agent.local
- Prometheus: http://prometheus.langchain-agent.local

**참고**: 
- ConfigMap의 `VITE_API_BASE_URL`이 빈 문자열로 설정되어 있어 상대 경로를 사용합니다
- 프론트엔드가 `/api/v1/...`로 요청하면 Ingress가 `/api` 경로로 백엔드를 라우팅합니다
- CORS_ORIGINS도 `http://langchain-agent.local`로 설정되어 있어야 합니다

## 문제 해결

### Pod가 시작되지 않는 경우

```bash
# Pod 상세 정보 확인
kubectl describe pod <pod-name> -n langchain-langgraph-agent

# Pod 이벤트 확인
kubectl get events -n langchain-langgraph-agent --sort-by='.lastTimestamp'

# 로그 확인
kubectl logs <pod-name> -n langchain-langgraph-agent
```

### 이미지를 찾을 수 없는 경우

```bash
# 이미지가 올바르게 로드되었는지 확인
kubectl describe pod <pod-name> -n langchain-langgraph-agent | grep -i image

# minikube의 경우
eval $(minikube docker-env)
docker images | grep langchain

# kind의 경우
docker exec -it langchain-agent-control-plane crictl images | grep langchain
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL Pod 상태 확인
kubectl get pods -l app=postgres -n langchain-langgraph-agent

# PostgreSQL 로그 확인
kubectl logs -l app=postgres -n langchain-langgraph-agent

# Service 확인
kubectl get svc postgres-service -n langchain-langgraph-agent

# 데이터베이스 연결 테스트 (Backend Pod에서)
kubectl exec -it deployment/backend -n langchain-langgraph-agent -- sh
# Pod 내부에서
psql postgresql://postgres:postgres@postgres-service:5432/rag_agent
```

### PVC 문제

```bash
# PVC 상태 확인
kubectl get pvc -n langchain-langgraph-agent

# PVC 상세 정보
kubectl describe pvc <pvc-name> -n langchain-langgraph-agent

# StorageClass 확인
kubectl get storageclass
```

### 리소스 부족

```bash
# 클러스터 리소스 확인
kubectl top nodes
kubectl top pods -n langchain-langgraph-agent

# minikube 리소스 증가
minikube config set memory 4096
minikube config set cpus 4
minikube delete
minikube start
```

## 리소스 정리

```bash
# 모든 리소스 삭제
kubectl delete namespace langchain-langgraph-agent

# 또는 개별 삭제
kubectl delete -f .

# 이미지 정리 (minikube)
eval $(minikube docker-env)
docker image prune -a
```

## 빠른 시작 스크립트

로컬 배포를 자동화하는 스크립트 예제:

```bash
#!/bin/bash
# deploy-local.sh

set -e

echo "🚀 로컬 Kubernetes 배포 시작..."

# 1. Secrets 확인
if [ ! -f "secrets.yaml" ]; then
    echo "❌ secrets.yaml 파일이 없습니다. secrets.yaml.example을 복사하여 생성하세요."
    exit 1
fi

# 2. 이미지 빌드 (minikube)
if command -v minikube &> /dev/null; then
    echo "📦 minikube 환경에서 이미지 빌드..."
    eval $(minikube docker-env)
    docker build -t langchain-langgraph-agent-backend:latest -f ../../backend/Dockerfile.prod ../..
    docker build -t langchain-langgraph-agent-frontend:latest -f ../../frontend/Dockerfile.prod ../../frontend
    eval $(minikube docker-env -u)
fi

# 3. 리소스 배포
echo "📋 Kubernetes 리소스 배포..."
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-init-configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres-statefulset.yaml

# 4. PostgreSQL 대기
echo "⏳ PostgreSQL 준비 대기..."
kubectl wait --for=condition=ready pod -l app=postgres -n langchain-langgraph-agent --timeout=300s

# 5. Backend/Frontend 배포
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml

# 6. 상태 확인
echo "✅ 배포 완료! 상태 확인 중..."
kubectl get pods -n langchain-langgraph-agent

echo ""
echo "🌐 접근 방법:"
echo "  Backend:  kubectl port-forward svc/backend-service 8000:8000 -n langchain-langgraph-agent"
echo "  Frontend: kubectl port-forward svc/frontend-service 3000:80 -n langchain-langgraph-agent"
```

## 다음 단계

- [ ] 모니터링 설정 (Prometheus, Grafana)
- [ ] 로깅 설정 (ELK, Loki)
- [ ] CI/CD 파이프라인 구성
- [ ] 프로덕션 배포 준비

