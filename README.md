# Langgraph RAG Agent Chat

> Production-ready RAG (Retrieval-Augmented Generation) agent built with LangGraph and LangChain. Features document upload, vector search, and intelligent chat interface. FastAPI + React stack.

FastAPI + React 기반의 RAG(Retrieval-Augmented Generation) Agent 프로젝트입니다.

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
- 🚀 **Production Ready** - Docker Compose setup with PostgreSQL and optional Milvus
- ⚡ **Real-time Streaming** - Streaming chat responses for better UX
- 🔄 **Session Management** - Persistent chat sessions with conversation history

- 🔐 **사용자 인증** - JWT 기반 보안 인증
- 📄 **문서 업로드** - PDF, DOCX, TXT, MD 파일 지원
- 📚 **문서 관리** - 문서 목록, 검색, 삭제
- 💬 **RAG 기반 채팅** - LangGraph로 구동되는 지능형 대화
- 🔍 **벡터 검색** - pgvector 또는 Milvus를 사용한 의미 기반 검색
- 🚀 **프로덕션 준비** - PostgreSQL 및 선택적 Milvus를 포함한 Docker Compose 설정
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
│   └── package.json
├── docker-compose.yml     # Docker Compose configuration / Docker Compose 설정
└── pyproject.toml         # Python dependencies / Python 의존성
```

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

