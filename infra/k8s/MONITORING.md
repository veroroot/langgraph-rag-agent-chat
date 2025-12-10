# 모니터링 및 로깅 가이드

이 문서는 Kubernetes 환경에서 로깅과 모니터링을 설정하고 사용하는 방법을 설명합니다.

## 개요

이 프로젝트는 다음 모니터링 스택을 사용합니다:

- **Loki**: 로그 집계 및 저장
- **Promtail**: 로그 수집 에이전트
- **Prometheus**: 메트릭 수집 및 저장
- **Grafana**: 로그 및 메트릭 시각화

## 배포

### 1. 모니터링 스택 배포

```bash
# Loki 배포
kubectl apply -f loki-config.yaml
kubectl apply -f loki-deployment.yaml

# Promtail 배포
kubectl apply -f promtail-config.yaml
kubectl apply -f promtail-daemonset.yaml

# Prometheus 배포
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus-deployment.yaml

# Grafana 배포
kubectl apply -f grafana-deployment.yaml
```

### 2. 접근 방법

#### Port Forwarding 사용

```bash
# Grafana 접근
kubectl port-forward -n langchain-langgraph-agent svc/grafana 3000:3000
# 브라우저에서 http://localhost:3000 접근
# 기본 계정: admin / admin

# Prometheus 접근
kubectl port-forward -n langchain-langgraph-agent svc/prometheus 9090:9090
# 브라우저에서 http://localhost:9090 접근

# Loki 접근 (직접 접근은 일반적으로 필요 없음)
kubectl port-forward -n langchain-langgraph-agent svc/loki 3100:3100
```

#### Ingress 사용

Ingress 설정에 다음을 추가:

```yaml
- host: grafana.langchain-agent.local
  http:
    paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 3000
- host: prometheus.langchain-agent.local
  http:
    paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus
            port:
              number: 9090
```

## 로깅 개선 사항

### 1. Health Check 로그 필터링

Health check 엔드포인트(`/health`, `/`)는 이제 DEBUG 레벨로만 로깅됩니다. 
일반 INFO 레벨에서는 보이지 않아 로그 노이즈가 크게 줄어듭니다.

### 2. 구조화된 JSON 로깅

프로덕션 환경에서는 JSON 형식의 구조화된 로그를 사용합니다:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "logger": "backend.core.middleware",
  "message": "Request completed",
  "method": "POST",
  "path": "/api/v1/chat",
  "status_code": 200,
  "duration": "0.123s",
  "request_id": "abc-123-def"
}
```

이 형식은 Loki에서 파싱하기 쉽고, 필터링과 쿼리가 용이합니다.

### 3. 로그 레벨 설정

ConfigMap에서 `LOG_LEVEL`을 조정할 수 있습니다:
- `DEBUG`: 모든 로그 (개발 환경)
- `INFO`: 일반 정보 로그 (프로덕션 권장)
- `WARNING`: 경고 이상
- `ERROR`: 에러 이상

## Grafana 사용법

### 1. 로그 쿼리 (Loki)

Grafana에서 Explore 메뉴로 이동하여 Loki 데이터소스를 선택합니다.

#### 기본 쿼리 예시

```
# 모든 백엔드 로그
{app="backend", namespace="langchain-langgraph-agent"}

# 에러 로그만
{app="backend", level="ERROR"}

# 특정 요청 ID로 필터링
{app="backend"} |= "request_id: abc-123"

# 특정 경로의 요청
{app="backend"} |= "path: /api/v1/chat"

# Health check 제외
{app="backend"} != "path: /health"
```

#### 로그 레이블

- `app`: 애플리케이션 이름 (backend, frontend)
- `pod`: Pod 이름
- `namespace`: 네임스페이스
- `level`: 로그 레벨 (INFO, ERROR, WARNING 등)

### 2. 메트릭 쿼리 (Prometheus)

#### 주요 메트릭

```
# HTTP 요청 수
rate(langchain_agent_http_request_duration_seconds_count[5m])

# HTTP 응답 시간 (평균)
rate(langchain_agent_http_request_duration_seconds_sum[5m]) / rate(langchain_agent_http_request_duration_seconds_count[5m])

# HTTP 상태 코드별 요청 수
sum(rate(langchain_agent_http_request_duration_seconds_count[5m])) by (status_code)

# 진행 중인 요청 수
langchain_agent_http_requests_inprogress
```

### 3. 대시보드 생성

Grafana에서 대시보드를 생성하여 다음을 모니터링할 수 있습니다:

1. **요청 통계**
   - 초당 요청 수 (RPS)
   - 응답 시간 (평균, P50, P95, P99)
   - 상태 코드 분포

2. **에러 모니터링**
   - 에러율
   - 에러 로그 수
   - 최근 에러 목록

3. **리소스 사용량**
   - CPU 사용률
   - 메모리 사용률
   - Pod 재시작 횟수

## 로그 확인 방법

### kubectl 사용 (기존 방법)

```bash
# 백엔드 로그 확인
kubectl logs -n langchain-langgraph-agent -l app=backend --tail=100

# 특정 Pod 로그
kubectl logs -n langchain-langgraph-agent <pod-name>

# Health check 제외하고 로그 확인
kubectl logs -n langchain-langgraph-agent -l app=backend | grep -v "/health"
```

### Grafana 사용 (권장)

Grafana의 Explore 기능을 사용하면:
- 실시간 로그 스트리밍
- 강력한 필터링 및 검색
- 로그 시각화
- 여러 Pod의 로그 통합 보기

## 문제 해결

### Promtail이 로그를 수집하지 않는 경우

```bash
# Promtail Pod 상태 확인
kubectl get pods -n langchain-langgraph-agent -l app=promtail

# Promtail 로그 확인
kubectl logs -n langchain-langgraph-agent -l app=promtail

# Promtail 설정 확인
kubectl get configmap promtail-config -n langchain-langgraph-agent -o yaml
```

### Loki에 로그가 없는 경우

```bash
# Loki Pod 상태 확인
kubectl get pods -n langchain-langgraph-agent -l app=loki

# Loki 로그 확인
kubectl logs -n langchain-langgraph-agent -l app=loki

# Loki 서비스 확인
kubectl get svc loki -n langchain-langgraph-agent
```

### Prometheus가 메트릭을 수집하지 않는 경우

```bash
# Backend Pod의 /metrics 엔드포인트 확인
kubectl port-forward -n langchain-langgraph-agent <backend-pod> 8000:8000
curl http://localhost:8000/metrics

# Prometheus 타겟 확인
# Prometheus UI에서 Status > Targets 메뉴 확인
```

## 프로덕션 고려사항

1. **리소스 제한**: 모니터링 컴포넌트에 적절한 리소스 제한 설정
2. **로그 보관**: Loki의 보관 기간 설정 (현재 7일)
3. **메트릭 보관**: Prometheus의 보관 기간 설정 (현재 15일)
4. **알림 설정**: Grafana Alerting 또는 Alertmanager 설정
5. **보안**: Grafana 및 Prometheus 접근 제어 설정
6. **백업**: Grafana 대시보드 및 설정 백업

## Grafana 대시보드

### 자동 프로비저닝된 대시보드

시스템 모니터링 대시보드가 자동으로 프로비저닝됩니다:

```bash
# 대시보드 ConfigMap 배포
kubectl apply -f grafana-dashboard-configmap.yaml
kubectl apply -f grafana-dashboard-provisioning.yaml

# Grafana 재시작 (대시보드 자동 로드)
kubectl rollout restart deployment/grafana -n langchain-langgraph-agent
```

### 대시보드 패널

대시보드에는 다음 패널들이 포함되어 있습니다:

1. **HTTP 요청 수 (RPS) - Method별**: GET, POST 등 HTTP 메서드별 요청 수
2. **전체 RPS**: 전체 초당 요청 수
3. **평균 응답 시간**: 평균 HTTP 응답 시간
4. **HTTP 응답 시간 (P50, P95, P99, 평균)**: 백분위수별 응답 시간
5. **HTTP 상태 코드 분포**: 200, 400, 500 등 상태 코드별 분포
6. **에러율 (5xx)**: 5xx 에러 비율
7. **진행 중인 요청 수**: 현재 처리 중인 요청 수
8. **Pod별 요청 수**: 각 Pod별 요청 분산
9. **최근 에러 로그**: Loki에서 수집한 최근 에러 로그
10. **로그 레벨별 분포**: INFO, ERROR, WARNING 등 로그 레벨별 분포
11. **엔드포인트별 요청 수**: API 엔드포인트별 요청 수

### 대시보드 접근

Grafana에 로그인 후 "Dashboards" 메뉴에서 "LangChain Agent - 시스템 모니터링" 대시보드를 찾을 수 있습니다.

### 대시보드 수정

대시보드는 편집 가능하도록 설정되어 있습니다. Grafana UI에서 직접 수정하거나, ConfigMap을 수정한 후 Grafana를 재시작할 수 있습니다.

## 추가 개선 사항

향후 고려할 사항:

1. **Alertmanager**: 알림 관리 및 라우팅
2. **Jaeger**: 분산 추적 (Distributed Tracing)
3. **Custom Metrics**: 비즈니스 메트릭 추가
4. **SLI/SLO 모니터링**: 서비스 수준 지표 모니터링

