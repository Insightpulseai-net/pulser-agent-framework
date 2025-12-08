# Open WebUI LLM Runtime - Spec Kit

## Objective
Self-hosted Open WebUI providing a ChatGPT-style interface for interacting with local LLMs (Ollama) and external providers, integrated with RAG pipelines and MCP agents.

## Status
- **Phase**: Planning
- **Priority**: P1
- **Dependencies**: opensearch-enterprise-search (RAG)

## Quick Links
- [Constitution](./constitution.md) - Guiding principles
- [PRD](./prd.md) - Requirements document
- [Plan](./plan.md) - Implementation plan
- [Tasks](./tasks.md) - Task breakdown

## Integration Points

| System | Type | Purpose |
|--------|------|---------|
| Ollama | Backend | Local LLM hosting |
| OpenAI API | Backend | Cloud LLM option |
| OpenSearch | RAG | Document retrieval |
| MCP Coordinator | Tools | Agent capabilities |
| Supabase | Storage | Chat history |

## Key Features
- Multi-model support (local + cloud)
- RAG pipeline integration
- Document upload and chat
- Conversation history
- User management
- Custom system prompts
- Function calling / tools
- Model fine-tuning UI

## Use Cases
- Internal ChatGPT alternative
- Document Q&A
- Code assistance
- Data analysis chat
- Agent interaction

## Tech Stack
- Open WebUI
- Ollama (local inference)
- PostgreSQL (metadata)
- ChromaDB / OpenSearch (vectors)
- Docker
