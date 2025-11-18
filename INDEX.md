# AEC RAG System - Project Index

## Table of Contents
- [Project Overview](#project-overview)
- [Quick Links](#quick-links)
- [Directory Structure](#directory-structure)
- [Key Components](#key-components)
- [Documentation](#documentation)
- [Development](#development)

## Project Overview
**Name:** AEC Design Management RAG System  
**Version:** 0.1.0  
**License:** MIT  
**Python:** 3.9+  
**Status:** Development

### Purpose
GraphRAG-powered intelligent document management system for Architecture, Engineering, and Construction (AEC) design workflows. Enables version tracking, impact analysis, and code compliance verification using local LLMs.

## Quick Links
- 📖 [README](./README.md) - Project introduction and quick start
- 📋 [Project Journal](./PROJECT_JOURNAL.md) - Development log and decisions
- 🤝 [Contributing Guidelines](./CONTRIBUTING.md) - How to contribute
- 📜 [Code of Conduct](./CODE_OF_CONDUCT.md) - Community standards
- ⚖️ [License](./LICENSE) - MIT License
- 🔧 [API Documentation](http://localhost:8000/api/docs) - Interactive API docs (when running)
- 📊 [Architecture Docs](./docs/architecture.md) - System design
- 🐛 [Issue Tracker](https://github.com/yourusername/aec-rag-system/issues)

## Directory Structure

```
aec-rag-system/
├── README.md                      # Project introduction and setup guide
├── PROJECT_JOURNAL.md             # Development log and decisions
├── INDEX.md                       # This file - project navigation
├── LICENSE                        # MIT License
├── CONTRIBUTING.md                # Contribution guidelines
├── CODE_OF_CONDUCT.md             # Community standards
├── pyproject.toml                 # Python project configuration
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Multi-service orchestration
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore patterns
├── .pre-commit-config.yaml        # Pre-commit hooks configuration
│
├── src/                           # Source code (application logic)
│   ├── __init__.py
│   ├── api/                       # REST API layer
│   │   ├── __init__.py
│   │   └── main.py                # FastAPI application and endpoints
│   ├── core/                      # Core business logic
│   │   ├── __init__.py
│   │   ├── embeddings.py          # Embedding model interface
│   │   ├── graphrag.py            # GraphRAG implementation
│   │   └── llm.py                 # LLM interface (Ollama)
│   ├── ingestion/                 # Document processing pipeline
│   │   ├── __init__.py
│   │   ├── cad_parser.py          # CAD file parsing (DWG/DXF)
│   │   └── pdf_parser.py          # PDF processing and OCR
│   ├── retrieval/                 # Query and retrieval logic
│   │   └── __init__.py
│   ├── schema/                    # Data models and schemas
│   │   ├── __init__.py
│   │   └── aec_schema.py          # AEC-specific data models
│   └── utils/                     # Utility functions
│       └── __init__.py
│
├── tests/                         # Test suite
│   ├── fixtures/                  # Test data and fixtures
│   ├── integration/               # Integration tests
│   └── unit/                      # Unit tests
│
├── config/                        # Configuration files
│   ├── settings.yaml              # Application settings
│   └── logging.yaml               # Logging configuration
│
├── docs/                          # Documentation
│   ├── architecture.md            # System architecture
│   ├── api.md                     # API reference
│   ├── deployment.md              # Deployment guide
│   └── user-guide.md              # User documentation
│
├── scripts/                       # Utility scripts
│   ├── setup.sh                   # Initial setup script
│   ├── pull_models.sh             # Download Ollama models
│   └── run_tests.sh               # Test runner
│
└── deployment/                    # Deployment configurations
    ├── kubernetes/                # K8s manifests
    ├── terraform/                 # Infrastructure as Code
    └── nginx/                     # Reverse proxy config
```

## Key Components

### Core Services
| Component | Technology | Purpose | Location |
|-----------|-----------|---------|----------|
| REST API | FastAPI | HTTP endpoints | `src/api/main.py` |
| GraphRAG | nano-graphrag | Knowledge graph | `src/core/graphrag.py` |
| Embeddings | nomic-embed-text | Vector encoding | `src/core/embeddings.py` |
| LLM | Llama-3.1-8B | Text generation | `src/core/llm.py` |
| CAD Parser | ezdxf | DWG/DXF parsing | `src/ingestion/cad_parser.py` |
| PDF Parser | PyMuPDF | PDF extraction | `src/ingestion/pdf_parser.py` |

### Infrastructure
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| Ollama | `ollama/ollama:latest` | 11434 | LLM inference |
| API | Custom build | 8000 | REST API |
| ChromaDB | Embedded | - | Vector storage |
| Redis | `redis:7-alpine` | 6379 | Caching |
| PostgreSQL | `postgres:15-alpine` | 5432 | Metadata |

## Documentation

### For Users
- 📖 [User Guide](./docs/user-guide.md) - How to use the system
- 🔍 [Query Examples](./docs/query-examples.md) - Sample queries
- 📊 [Dashboard Guide](./docs/dashboard.md) - UI walkthrough

### For Developers
- 🏗️ [Architecture](./docs/architecture.md) - System design
- 🔌 [API Reference](./docs/api.md) - Endpoint documentation
- 🧪 [Testing Guide](./docs/testing.md) - How to test
- 🚀 [Deployment](./docs/deployment.md) - Production deployment

### Technical Specs
- 📐 [Data Schema](./src/schema/aec_schema.py) - Data models
- 🔧 [Configuration](./config/settings.yaml) - Settings reference
- 🐳 [Docker Setup](./docker-compose.yml) - Container orchestration

## Development

### Getting Started
```bash
# 1. Clone and setup
git clone https://github.com/yourusername/aec-rag-system.git
cd aec-rag-system
cp .env.example .env

# 2. Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start services
docker-compose up -d

# 4. Run tests
pytest tests/
```

### Development Tools
- **Formatting:** `black src/ tests/` (100 char lines)
- **Linting:** `ruff check src/ tests/`
- **Type Checking:** `mypy src/`
- **Testing:** `pytest tests/ -v --cov`
- **Pre-commit:** `pre-commit install`

### Standards
- **Coding Style:** PEP 8, black, type hints required
- **Directory Naming:** FSH 3.0 compliant (lowercase, hyphens)
- **File Naming:** ISO 8000 compliant (descriptive, versioned)
- **Git Workflow:** Feature branches, PR reviews, conventional commits
- **Testing:** >80% code coverage target

### Environment Variables
See `.env.example` for required configuration. Key variables:
- `OLLAMA_BASE_URL` - Ollama service endpoint
- `VECTOR_DB_TYPE` - Vector database choice
- `LOG_LEVEL` - Logging verbosity

## Version History
- **0.1.0** (2025-11-18) - Initial development version

## Support
- 📧 Email: your.email@example.com
- 💬 Issues: [GitHub Issues](https://github.com/yourusername/aec-rag-system/issues)
- 📖 Docs: [Project Documentation](./docs/)

---
*Generated: 2025-11-18 | Maintained by: Project Team*
