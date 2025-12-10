# Langgraph RAG Agent Chat

> Production-ready RAG (Retrieval-Augmented Generation) agent built with LangGraph and LangChain. Features document upload, vector search, and intelligent chat interface. FastAPI + React stack, deployable to on-prem or cloud Kubernetes with Docker-first workflow.

FastAPI + React 기반의 RAG(Retrieval-Augmented Generation) Agent 프로젝트입니다. Kubernetes 기반으로 온프레미스/클라우드 어디서나 프로덕션 운영이 가능하며 Docker 중심의 워크플로우를 제공합니다.

## Table of Contents / 목차

- [Features](#features--주요-기능)
- [Tech Stack](#tech-stack--기술-스택)
- [Project Structure](#project-structure--프로젝트-구조)
- [Getting Started](#getting-started--시작하기)
  - [Prerequisites](#prerequisites--사전-요구사항)
  - [Environment Variables](#environment-variables--환경-변수-설정)
  - [Running with Docker Compose](#running-with-docker-compose--docker-compose로-실행)
  - [Local Development](#local-development--로컬-개발)
- [API Endpoints](#api-endpoints--api-엔드포인트)
- [Development Guide](#development-guide--개발-가이드)
- [License](#license--라이선스)

## Features / 주요 기능

- 🔐 **User Authentication** - JWT-based secure authentication
- 📄 **Document Upload** - Support for PDF, DOCX, TXT, and MD files
- 📚 **Document Management** - List, search, and delete uploaded documents
- 💬 **RAG-based Chat Interface** - Intelligent conversations powered by LangGraph
- 🔍 **Vector Search** - Semantic search using pgvector or Milvus
- 🚀 **Production Ready** - Docker Compose + Kubernetes manifests for on-prem/cloud
- ⚡ **Real-time Streaming** - Streaming chat responses for better UX
- 🔄 **Session Management** - Persistent chat sessions with conversation history

- 🔐 **사용자 인증** - JWT 기반 보안 인증
- 📄 **문서 업로드** - PDF, DOCX, TXT, MD 파일 지원
- 📚 **문서 관리** - 문서 목록, 검색, 삭제
- 💬 **RAG 기반 채팅** - LangGraph로 구동되는 지능형 대화
- 🔍 **벡터 검색** - pgvector 또는 Milvus를 사용한 의미 기반 검색
- 🚀 **프로덕션 준비** - 온프레미스/클라우드용 Kubernetes 매니페스트와 Compose
- ⚡ **실시간 스트리밍** - 향상된 UX를 위한 스트리밍 채팅 응답
- 🔄 **세션 관리** - 대화 기록이 있는 지속적인 채팅 세션

## Tech Stack / 기술 스택

### Backend / 백엔드
- **FastAPI** - Modern, fast web framework
- **SQLModel** - SQL databases with Pydantic
- **PostgreSQL** - Relational database with pgvector extension
- **LangChain** - LLM application framework
- **LangGraph** - Stateful, multi-actor applications with LLMs
- **slowapi** - Rate limiting middleware
- **JWT** - Secure token-based authentication
- **Milvus** (Optional) - Vector database for large-scale similarity search

### Frontend / 프론트엔드
- **React 18** - UI library
- **Vite** - Fast build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client

## Project Structure / 프로젝트 구조

이 프로젝트는 **Monorepo 패턴**을 사용합니다. 모든 서비스(backend, frontend, infra)가 하나의 저장소에서 관리됩니다.

This project uses a **Monorepo pattern**, where all services (backend, frontend, infra) are managed in a single repository.

### Why Monorepo? / Monorepo를 사용하는 이유

1. **통합 개발 환경 / Unified Development Environment**
   - `docker-compose.yml`로 전체 스택을 한 번에 실행 가능
   - All services can be run together with `docker-compose.yml`

2. **의존성 관리 / Dependency Management**
   - Python 의존성(`pyproject.toml`, `uv.lock`)은 루트에 위치하여 `uv` 패키지 매니저와 Docker 빌드 프로세스와 호환
   - Python dependencies (`pyproject.toml`, `uv.lock`) are at the root for compatibility with `uv` package manager and Docker build process

3. **공유 설정 / Shared Configuration**
   - `.env`, `docker-compose.yml` 등 공통 설정 파일을 한 곳에서 관리
   - Common configuration files like `.env` and `docker-compose.yml` are managed in one place

4. **인프라 코드 통합 / Infrastructure Code Integration**
   - Terraform, Kubernetes 설정이 프로젝트와 함께 버전 관리됨
   - Terraform and Kubernetes configurations are version-controlled with the project

### Directory Structure / 디렉토리 구조

```
langgraph-rag-agent-chat/
├── backend/                # FastAPI backend / FastAPI 백엔드
│   ├── main.py            # FastAPI entry point / FastAPI 엔트리포인트
│   ├── core/              # Configuration, DB, middleware / 설정, DB, 미들웨어
│   │   ├── langgraph/    # LangGraph agent implementation / LangGraph 에이전트 구현
│   │   └── prompts/      # System prompts / 시스템 프롬프트
│   ├── api/v1/            # API routers / API 라우터
│   ├── models/            # SQLModel models / SQLModel 모델
│   ├── crud/              # Database CRUD operations / 데이터베이스 CRUD
│   ├── services/          # Business logic / 비즈니스 로직
│   └── utils/             # Utility functions / 유틸리티 함수
├── frontend/              # React frontend / React 프론트엔드
│   ├── src/
│   │   ├── pages/        # Page components / 페이지 컴포넌트
│   │   ├── components/   # Reusable components / 재사용 컴포넌트
│   │   └── services/     # API services / API 서비스
│   └── package.json      # Frontend dependencies (Node.js) / 프론트엔드 의존성
├── infra/                 # Infrastructure as Code / 인프라 코드
│   ├── terraform/         # AWS infrastructure (ECS, RDS, etc.) / AWS 인프라
│   ├── k8s/               # Kubernetes manifests / Kubernetes 매니페스트
│   └── ci-cd/             # CI/CD pipelines (GitHub Actions) / CI/CD 파이프라인
├── data/                  # Local data (PostgreSQL, uploads) / 로컬 데이터
│   ├── postgres/          # PostgreSQL data directory / PostgreSQL 데이터 디렉토리
│   └── uploads/           # Uploaded documents / 업로드된 문서
├── docker-compose.yml     # Docker Compose configuration / Docker Compose 설정
├── pyproject.toml         # Python dependencies (backend) / Python 의존성 (백엔드)
├── uv.lock                # Python dependency lock file / Python 의존성 락 파일
└── .python-version        # Python version specification / Python 버전 명시
```

### Important Notes for Developers / 개발자를 위한 중요 사항

#### For Frontend Developers / 프론트엔드 개발자

- **Python 파일 무시 가능 / Python files can be ignored**
  - 루트의 `pyproject.toml`, `uv.lock`, `.python-version`은 백엔드 전용입니다
  - `pyproject.toml`, `uv.lock`, `.python-version` at root are backend-only
  - 프론트엔드 개발 시 `frontend/` 디렉토리만 작업하시면 됩니다
  - For frontend development, you only need to work in the `frontend/` directory

- **독립적인 의존성 관리 / Independent dependency management**
  - 프론트엔드는 `frontend/package.json`으로 의존성을 관리합니다
  - Frontend manages dependencies with `frontend/package.json`
  - Python 의존성과는 완전히 분리되어 있습니다
  - It's completely separate from Python dependencies

#### For Infrastructure Engineers / 인프라 담당자

- **루트의 Python 설정 파일 / Python config files at root**
  - `pyproject.toml`, `uv.lock`이 루트에 있는 이유: Docker 빌드 시 `backend/Dockerfile`이 루트를 빌드 컨텍스트로 사용하기 때문입니다
  - `pyproject.toml` and `uv.lock` are at root because `backend/Dockerfile` uses root as build context
  - `uv` 패키지 매니저가 루트의 `pyproject.toml`을 기준으로 의존성을 설치합니다
  - `uv` package manager installs dependencies based on `pyproject.toml` at root

- **데이터 디렉토리 / Data directory**
  - `data/` 디렉토리는 로컬 개발용 PostgreSQL 데이터와 업로드된 파일을 저장합니다
  - `data/` directory stores PostgreSQL data and uploaded files for local development
  - `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다
  - It's in `.gitignore` and won't be committed to Git

- **인프라 코드 위치 / Infrastructure code location**
  - 모든 인프라 관련 코드는 `infra/` 디렉토리에 있습니다
  - All infrastructure-related code is in the `infra/` directory
  - Terraform, Kubernetes, CI/CD 설정이 각 하위 디렉토리에 분리되어 있습니다
  - Terraform, Kubernetes, and CI/CD configurations are separated in subdirectories

## Getting Started / 시작하기

### Prerequisites / 사전 요구사항

- Docker & Docker Compose
- Python 3.13+ (for local development / 로컬 개발 시)
- Node.js 18+ (for frontend development / 프론트엔드 개발 시)
- OpenAI API key (required / 필수)

### Environment Variables / 환경 변수 설정

Create a `.env` file and configure the following settings:

`.env` 파일을 생성하고 다음 내용을 설정하세요:

```bash
# Copy .env.sample to .env
# .env.sample을 참고하여 .env 파일 생성
cp .env.sample .env
```

Then open the `.env` file and set the following required values:

그 다음 `.env` 파일을 열어서 다음 필수 값들을 설정하세요:

**Required Environment Variables / 필수 환경 변수:**
- `SECRET_KEY`: JWT secret key (use a strong key in production / 프로덕션에서는 강력한 키 사용)
  - Generate with: `openssl rand -hex 32` / 생성 방법: `openssl rand -hex 32`
- `OPENAI_API_KEY`: OpenAI API key
  - Get from: https://platform.openai.com/api-keys / https://platform.openai.com/api-keys 에서 발급

**Note / 참고:**
- `DATABASE_URL` is automatically configured in docker-compose.yml
- `DATABASE_URL`은 docker-compose.yml에서 자동으로 설정됩니다
- With Docker Compose: `postgresql://postgres:postgres@db:5432/rag_agent`
- Docker Compose 사용 시: `postgresql://postgres:postgres@db:5432/rag_agent`
- Local development: `postgresql://postgres:postgres@localhost:5432/rag_agent`
- 로컬 개발 시: `postgresql://postgres:postgres@localhost:5432/rag_agent`

#### Vector Store Configuration / 벡터 스토어 설정

- `VECTOR_STORE_TYPE`: `pgvector` (default / 기본) or `milvus`
- `VECTOR_COLLECTION_NAME`: Collection/table name for embeddings / 임베딩이 저장될 컬렉션/테이블 이름
- `VECTOR_DIMENSION`: Embedding dimension (OpenAI text-embedding-3-small → 1536) / 임베딩 차원 수

**Additional Milvus Settings / Milvus 사용 시 추가 설정**

- `MILVUS_HOST`, `MILVUS_PORT`: Milvus connection info (default: localhost, 19530) / Milvus 접속 정보
- `MILVUS_USER`, `MILVUS_PASSWORD`: Authentication if required / 인증이 필요한 경우 입력
- `MILVUS_DB_NAME`, `MILVUS_CONSISTENCY_LEVEL`, `MILVUS_SECURE` and other detailed settings / 세부 설정
- To run Milvus with Docker Compose: `docker compose --profile milvus up -d`
- Docker Compose로 Milvus를 실행할 경우: `docker compose --profile milvus up -d`

### Running with Docker Compose / Docker Compose로 실행

```bash
# Start all services / 모든 서비스 시작
docker-compose up -d

# (Optional) Start with Milvus / (선택) Milvus까지 함께 실행
docker-compose --profile milvus up -d

# View logs / 로그 확인
docker-compose logs -f

# Stop services / 서비스 중지
docker-compose down
```

Service URLs / 서비스 URL:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Milvus Dashboard (Optional): http://localhost:9091

### Local Development / 로컬 개발

#### Backend / 백엔드

```bash
# Install dependencies / 의존성 설치
uv sync

# Initialize database / 데이터베이스 초기화
uv run python -c "from backend.core.db import init_db; init_db()"

# Run server / 서버 실행
uv run uvicorn backend.main:app --reload
```

#### Frontend / 프론트엔드

```bash
cd frontend

# Install dependencies / 의존성 설치
npm install

# Run development server / 개발 서버 실행
npm run dev
```

## API Endpoints / API 엔드포인트

### Authentication / 인증
- `POST /api/v1/auth/register` - User registration / 회원가입
- `POST /api/v1/auth/login` - User login / 로그인
- `GET /api/v1/auth/me` - Get current user info / 현재 사용자 정보

### Documents / 문서
- `POST /api/v1/upload/` - Upload document / 문서 업로드
- `GET /api/v1/docs/` - List documents / 문서 목록
- `GET /api/v1/docs/{id}` - Get document details / 문서 상세
- `PATCH /api/v1/docs/{id}` - Update document / 문서 수정
- `DELETE /api/v1/docs/{id}` - Delete document / 문서 삭제

### Chat / 채팅
- `POST /api/v1/chat/` - Send message (streaming) / 메시지 전송 (스트리밍)
- `GET /api/v1/chat/sessions` - List chat sessions / 채팅 세션 목록
- `GET /api/v1/chat/sessions/{id}/messages` - Get messages / 메시지 목록

## Infrastructure Deployment / 인프라 배포

이 프로젝트는 온프레미스와 클라우드 환경 모두에서 프로덕션 운영을 목표로 하며, 기본 배포 경로는 Kubernetes입니다. 로컬/스테이징에서는 Docker Compose로도 동일한 스택을 구동할 수 있습니다.

### Kubernetes (On-premise & Cloud)

- `infra/k8s/` 매니페스트를 사용해 온프레미스 클러스터 또는 클라우드 매니지드 Kubernetes(EKS/GKE/AKS 등)에 배포 가능합니다.
- 인그레스, 로깅, 모니터링 예제가 포함되어 있어 바로 적용 후 확장할 수 있습니다.

```bash
kubectl apply -f infra/k8s/
```

자세한 내용은 [infra/k8s/README.md](./infra/k8s/README.md)를 참고하세요.

### AWS Cloud (Terraform configs provided, full validation pending)

- `infra/terraform/`에 AWS ECS Fargate용 Terraform 예제가 포함되어 있습니다.
- 아직 개인 환경에서 엔드투엔드로 완전히 검증하진 않았으므로, 사용 전에 `terraform plan` 결과를 검토하고 필요한 변수/리소스 제약을 확인하세요.

```bash
cd infra/terraform
terraform init
terraform plan
# terraform apply  # 계획을 충분히 검토한 뒤 적용
```

자세한 내용은 [infra/terraform/README.md](./infra/terraform/README.md)를 참고하세요.

### CI/CD 자동 배포

GitHub Actions를 사용한 자동 배포 설정은 [infra/ci-cd/README.md](./infra/ci-cd/README.md)를 참고하세요.

## Development Guide / 개발 가이드

작성 중

## 참고 레퍼런스

* 레퍼런스 템플릿: [https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template)
* LangChain docs: [https://langchain.readthedocs.io/](https://langchain.readthedocs.io/)
* LangGraph: [https://langgraph.org/](https://langgraph.org/) (또는 공식 repo)
* slowapi: [https://pypi.org/project/slowapi/](https://pypi.org/project/slowapi/)
* SQLModel: [https://sqlmodel.tiangolo.com/](https://sqlmodel.tiangolo.com/)
* pgvector: [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)

## License / 라이선스

MIT

