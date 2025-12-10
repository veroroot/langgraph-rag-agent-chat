# Kubernetes Deployment Guide

이 디렉토리는 온프레미스 또는 클라우드 매니지드 Kubernetes(EKS/GKE/AKS 등)에 LangChain LangGraph Agent를 배포하기 위한 매니페스트 파일을 포함합니다. 기본 워크플로우는 Docker 이미지를 레지스트리에 푸시한 뒤, 매니페스트를 적용하는 방식입니다.

## 구조

- `namespace.yaml`: Kubernetes Namespace
- `configmap.yaml`: 애플리케이션 설정 (환경 변수)
- `secrets.yaml.example`: 시크릿 예제 파일
- `secrets.yaml`: 시크릿 파일 (로컬에서 생성 필요, Git에 커밋하지 마세요)
- `postgres-statefulset.yaml`: PostgreSQL StatefulSet 및 Service
- `postgres-init-configmap.yaml`: PostgreSQL 초기화 스크립트
- `backend-deployment.yaml`: Backend Deployment, Service, PVC
- `frontend-deployment.yaml`: Frontend Deployment 및 Service
- `ingress.yaml`: Ingress 리소스 (외부 접근)
- `LOCAL_DEPLOYMENT.md`: 로컬 Kubernetes 배포 테스트 가이드
- `MONITORING.md` 및 `prometheus-*.yaml`, `loki-*.yaml`, `promtail-*.yaml`, `grafana-*.yaml`: 모니터링/로깅 스택 예제

## 빠른 시작

**로컬에서 Kubernetes 배포 테스트를 하시나요?**  
👉 [로컬 배포 가이드](./LOCAL_DEPLOYMENT.md)를 먼저 확인하세요!

**관측(Observability)을 켜고 싶다면?**  
👉 [MONITORING.md](./MONITORING.md)를 참고해 Prometheus/Grafana/Loki/Promtail을 함께 배포하세요.

## 사전 요구사항

1. Kubernetes 클러스터 (v1.24+)
2. kubectl 설치 및 클러스터 접근 권한
3. Ingress Controller 설치 (Nginx, Traefik 등) - 선택사항이지만 외부 노출 시 권장
4. StorageClass 구성 (PVC 사용을 위해). 필요 시 `postgres-statefulset.yaml`, `backend-deployment.yaml`의 `storageClassName`을 환경에 맞게 수정

## 사용 방법

### 1. 시크릿 파일 생성

```bash
cp secrets.yaml.example secrets.yaml
```

`secrets.yaml` 파일을 편집하여 실제 값들을 설정하세요:

```yaml
stringData:
  SECRET_KEY: "your-secret-key-here"
  POSTGRES_PASSWORD: "your-postgres-password"
  OPENAI_API_KEY: "your-openai-api-key"
```

### 2. Docker 이미지 빌드 및 레지스트리에 푸시

#### Backend 이미지

```bash
# 프로덕션 이미지 빌드 (Gunicorn + Uvicorn workers 사용)
docker build -t your-registry/langchain-langgraph-agent-backend:latest -f backend/Dockerfile.prod .
docker push your-registry/langchain-langgraph-agent-backend:latest
```

#### Frontend 이미지

```bash
# 프로덕션 이미지 빌드 (Nginx 사용)
docker build -t your-registry/langchain-langgraph-agent-frontend:latest -f frontend/Dockerfile.prod ./frontend
docker push your-registry/langchain-langgraph-agent-frontend:latest
```

### 3. Deployment 파일에서 이미지 경로 수정

`backend-deployment.yaml`과 `frontend-deployment.yaml`에서 이미지 경로를 실제 레지스트리 경로로 변경:

```yaml
image: your-registry/langchain-langgraph-agent-backend:latest
```

### 4. ConfigMap 및 Ingress 설정 수정

`configmap.yaml`과 `ingress.yaml`에서 환경에 맞게 설정을 수정하세요:

- `CORS_ORIGINS`: 실제 프론트엔드 URL
- `VITE_API_BASE_URL`: 실제 백엔드 API URL
- Ingress `host`: 실제 도메인 (예: `rag.example.com` 또는 로컬 테스트 `rag.local.test`)
- Ingress TLS: 인증서/비밀키를 쓸 경우 `tls.secretName`과 `hosts`를 함께 지정

예시 인그레스 호스트/TLS 설정:

```yaml
spec:
  tls:
    - hosts:
        - rag.example.com
      secretName: rag-tls
  rules:
    - host: rag.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

### 5. 리소스 배포

```bash
# Namespace 생성
kubectl apply -f namespace.yaml

# ConfigMap 생성
kubectl apply -f configmap.yaml
kubectl apply -f postgres-init-configmap.yaml

# Secrets 생성
kubectl apply -f secrets.yaml

# PostgreSQL 배포
kubectl apply -f postgres-statefulset.yaml

# Backend 배포
kubectl apply -f backend-deployment.yaml

# Frontend 배포
kubectl apply -f frontend-deployment.yaml

# Ingress 배포
kubectl apply -f ingress.yaml
```

또는 한 번에 배포:

```bash
kubectl apply -f .
```

### 6. 배포 상태 확인

```bash
# Pod 상태 확인
kubectl get pods -n langchain-langgraph-agent

# Service 확인
kubectl get svc -n langchain-langgraph-agent

# Ingress 확인
kubectl get ingress -n langchain-langgraph-agent

# 로그 확인
kubectl logs -f deployment/backend -n langchain-langgraph-agent
kubectl logs -f deployment/frontend -n langchain-langgraph-agent
```

### 7. 애플리케이션 접근

Ingress에 설정한 호스트로 접근:

```bash
# /etc/hosts에 추가 (로컬 테스트용 예시)
<ingress-ip> rag.local.test

# 브라우저에서 접근
http://rag.local.test
```

## 업데이트

### 이미지 업데이트

```bash
# 새 이미지 빌드 및 푸시
docker build -t your-registry/langchain-langgraph-agent-backend:v1.1.0 -f backend/Dockerfile .
docker push your-registry/langchain-langgraph-agent-backend:v1.1.0

# Deployment 업데이트
kubectl set image deployment/backend backend=your-registry/langchain-langgraph-agent-backend:v1.1.0 -n langchain-langgraph-agent

# 롤아웃 상태 확인
kubectl rollout status deployment/backend -n langchain-langgraph-agent
```

### 설정 업데이트

```bash
# ConfigMap 수정
kubectl edit configmap app-config -n langchain-langgraph-agent

# Pod 재시작 (설정 적용)
kubectl rollout restart deployment/backend -n langchain-langgraph-agent
kubectl rollout restart deployment/frontend -n langchain-langgraph-agent
```

## 스케일링

```bash
# Backend Pod 수 증가
kubectl scale deployment backend --replicas=3 -n langchain-langgraph-agent

# Frontend Pod 수 증가
kubectl scale deployment frontend --replicas=3 -n langchain-langgraph-agent
```

## 문제 해결

### Pod가 시작되지 않는 경우

```bash
# Pod 이벤트 확인
kubectl describe pod <pod-name> -n langchain-langgraph-agent

# 로그 확인
kubectl logs <pod-name> -n langchain-langgraph-agent
```

### 데이터베이스 연결 실패

1. PostgreSQL Pod가 실행 중인지 확인:
   ```bash
   kubectl get pods -n langchain-langgraph-agent | grep postgres
   ```

2. Service가 올바르게 생성되었는지 확인:
   ```bash
   kubectl get svc postgres-service -n langchain-langgraph-agent
   ```

3. Secrets의 DATABASE_URL이 올바른지 확인:
   ```bash
   kubectl get secret app-secrets -n langchain-langgraph-agent -o yaml
   ```

### PVC 문제

StorageClass가 올바르게 설정되어 있는지 확인:

```bash
kubectl get storageclass
```

필요한 경우 `postgres-statefulset.yaml`과 `backend-deployment.yaml`에서 `storageClassName`을 수정하세요.

## 리소스 삭제

```bash
# 모든 리소스 삭제
kubectl delete namespace langchain-langgraph-agent

# 또는 개별 삭제
kubectl delete -f .
```

## 프로덕션 고려사항

1. **리소스 제한**: 프로덕션 환경에서는 적절한 `requests`와 `limits` 설정
2. **고가용성**: PostgreSQL은 가능하면 외부 관리형 DB(RDS, CloudSQL 등) 사용 고려
3. **백업**: PostgreSQL 데이터 정기 백업 설정
4. **모니터링/로깅**: Prometheus, Grafana, Loki/Promtail 등을 활성화 (예제 제공)
5. **SSL/TLS**: Ingress에 SSL 인증서 설정 (Cert-Manager 등)
6. **네트워크 정책**: NetworkPolicy로 트래픽 제어
7. **이미지 서명/스캔**: 레지스트리의 이미지 서명/취약점 스캔 정책 활용 권장

## Helm은 어떻게 쓰나요? (선택 사항, 차트는 포함되어 있지 않음)
- Helm은 매니페스트를 템플릿화해 배포/업그레이드를 단순화하는 도구입니다.
- 이 레포지토리에는 Helm 차트가 포함되어 있지 않습니다. 필요하면 `helm create langgraph-agent`로 베이스 차트를 생성한 뒤, 이 디렉토리의 매니페스트를 `templates/`로 옮기고 이미지/도메인/리소스 값을 `values.yaml` 변수로 치환하는 방식을 권장합니다.
- 일반적인 흐름:
  1) Helm 설치 후 베이스 차트 생성: `helm create langgraph-agent`
  2) `templates/`에 현재 매니페스트를 옮기고 값들을 템플릿화 (`{{ .Values.image.repository }}` 등)
  3) 환경별 오버라이드 파일 준비(e.g., `values.prod.yaml`에서 이미지 태그, 도메인, 리소스 설정)
  4) 배포: `helm upgrade --install langgraph-agent ./langgraph-agent -f values.prod.yaml -n langchain-langgraph-agent`
- 차트를 만들지 않아도 `kubectl apply -f .` 또는 Kustomize로 충분히 운영할 수 있습니다.

