# Dockerfile 가이드

이 프로젝트는 개발용과 프로덕션용 Dockerfile을 분리하여 제공합니다.

## Backend Dockerfile

### 개발용: `backend/Dockerfile`
- Uvicorn 개발 서버 사용
- Hot reload 지원 (`--reload` 옵션)
- 로컬 개발 및 Docker Compose에서 사용

```bash
docker build -t backend:dev -f backend/Dockerfile .
```

### 프로덕션용: `backend/Dockerfile.prod`
- **Gunicorn + Uvicorn workers** 사용
- 프로덕션 환경에 최적화
- 워커 프로세스 관리 및 로드 밸런싱
- AWS ECS, Kubernetes 등 프로덕션 배포에 사용

```bash
docker build -t backend:prod -f backend/Dockerfile.prod .
```

#### Gunicorn 설정
- `backend/gunicorn.conf.py`: Gunicorn 설정 파일
- 워커 수: CPU 코어 수 * 2 + 1 (환경 변수 `GUNICORN_WORKERS`로 조정 가능)
- Worker 클래스: `uvicorn.workers.UvicornWorker`
- 타임아웃: 120초
- Graceful shutdown 지원

## Frontend Dockerfile

### 개발용: `frontend/Dockerfile`
- Vite 개발 서버 사용
- Hot Module Replacement (HMR) 지원
- 로컬 개발 및 Docker Compose에서 사용

```bash
docker build -t frontend:dev -f frontend/Dockerfile ./frontend
```

### 프로덕션용: `frontend/Dockerfile.prod`
- **Nginx**를 사용한 정적 파일 서빙
- Multi-stage build로 최적화된 이미지 크기
- 프로덕션 빌드 (`npm run build`)
- Gzip 압축 및 캐싱 설정
- SPA 라우팅 지원

```bash
docker build -t frontend:prod -f frontend/Dockerfile.prod ./frontend
```

#### Nginx 설정
- `frontend/nginx.conf`: Nginx 설정 파일
- SPA 라우팅: 모든 경로를 `index.html`로 리다이렉트
- 정적 파일 캐싱: 1년
- Gzip 압축 활성화
- 보안 헤더 설정

## 사용 시나리오

### 로컬 개발
```bash
# Docker Compose 사용 (개발용 Dockerfile 자동 사용)
docker-compose up
```

### 프로덕션 배포

#### AWS ECS
```bash
# 프로덕션 이미지 빌드
docker build -t <ECR_URL>/backend:latest -f backend/Dockerfile.prod .
docker build -t <ECR_URL>/frontend:latest -f frontend/Dockerfile.prod ./frontend

# ECR에 푸시
docker push <ECR_URL>/backend:latest
docker push <ECR_URL>/frontend:latest
```

#### Kubernetes
```bash
# 프로덕션 이미지 빌드
docker build -t <registry>/backend:latest -f backend/Dockerfile.prod .
docker build -t <registry>/frontend:latest -f frontend/Dockerfile.prod ./frontend

# 레지스트리에 푸시
docker push <registry>/backend:latest
docker push <registry>/frontend:latest
```

## 환경 변수

### Backend (Gunicorn)
- `GUNICORN_WORKERS`: 워커 프로세스 수 (기본값: CPU 코어 * 2 + 1)
- `PORT`: 서버 포트 (기본값: 8000)
- `LOG_LEVEL`: 로그 레벨 (기본값: info)

### Frontend (Nginx)
- Nginx는 환경 변수 대신 설정 파일 사용
- 빌드 시 `VITE_API_BASE_URL` 환경 변수 주입 필요

## 성능 최적화

### Backend
- Gunicorn 워커 수 조정: CPU 코어 수에 따라 최적화
- Preload app 활성화: 메모리 공유로 성능 향상
- Worker timeout 설정: 장시간 요청 처리

### Frontend
- 정적 파일 캐싱: 브라우저 캐싱으로 로딩 속도 향상
- Gzip 압축: 네트워크 전송량 감소
- Multi-stage build: 최종 이미지 크기 최소화

## 문제 해결

### Backend가 시작되지 않는 경우
1. `gunicorn.conf.py` 파일이 있는지 확인
2. `GUNICORN_WORKERS` 환경 변수 확인
3. 로그 확인: `docker logs <container>`

### Frontend 빌드 실패
1. `package.json`의 빌드 스크립트 확인
2. 환경 변수 `VITE_API_BASE_URL` 설정 확인
3. Nginx 설정 파일 경로 확인

