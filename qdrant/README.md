# Qdrant Vector Search

Self-hosted Qdrant deployment for semantic search across knowledge base.

## Quick Start

### 1. Start Qdrant
```bash
docker-compose up -d
```

### 2. Verify Health
```bash
curl http://localhost:6333/health
```

### 3. Create Collection
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)
```

### 4. Ingest Documents
```bash
cd ingest

# Chunk documents
python document_chunker.py \
  --input ../../docs/ \
  --output chunks.json \
  --category finance

# Generate embeddings and upload to Qdrant
python embedding_generator.py \
  --input chunks.json \
  --collection knowledge_base
```

## Collection Schema

**Collection**: `knowledge_base`
**Vector Size**: 1536 (OpenAI text-embedding-3-small)
**Distance**: Cosine

**Payload Schema**:
```json
{
  "text": "Document text content",
  "source": "path/to/document.md",
  "category": "finance",
  "created_at": 1702080000
}
```

## Usage

### Search
```python
from langgraph_agents.tools.qdrant_tool import QdrantTool

qdrant = QdrantTool("http://localhost:6333")

results = await qdrant.search(
    collection_name="knowledge_base",
    query_text="What are BIR filing requirements?",
    limit=5,
    score_threshold=0.7
)

for result in results:
    print(f"Score: {result['score']:.2f}")
    print(f"Text: {result['text'][:200]}...")
    print(f"Source: {result['source']}\n")
```

### Upsert
```python
documents = [
    {
        "id": 1,
        "text": "Document content here...",
        "source": "docs/bir-filing-guide.md",
        "category": "finance",
        "created_at": int(time.time())
    }
]

await qdrant.upsert_documents("knowledge_base", documents)
```

## Configuration

### docker-compose.yml
```yaml
services:
  qdrant:
    image: qdrant/qdrant:v1.7.4
    ports:
      - "6333:6333"  # REST API
      - "6334:6334"  # gRPC API
    volumes:
      - ./storage:/qdrant/storage
```

### Environment Variables
```bash
export QDRANT_URL="http://localhost:6333"
export OPENAI_API_KEY="your-openai-api-key"  # For embeddings
```

## Performance

- **Search Latency**: <100ms (p95)
- **Throughput**: 100+ searches/second
- **Index Size**: 10M+ vectors supported
- **Memory**: ~4GB for 1M vectors

## Monitoring

### Health Check
```bash
curl http://localhost:6333/health
```

### Collection Stats
```bash
curl http://localhost:6333/collections/knowledge_base
```

## Troubleshooting

### Qdrant Not Starting
**Symptom**: Container exits immediately

**Solutions**:
1. Check Docker logs: `docker logs qdrant`
2. Verify port availability: `lsof -i :6333`
3. Check storage permissions: `ls -la ./storage`

### Slow Search
**Symptom**: Search takes >500ms

**Solutions**:
1. Reduce search limit (default: 5)
2. Increase score_threshold (filter more results)
3. Check HNSW configuration in collection schema
4. Scale vertically (more CPU/RAM)

### Missing Results
**Symptom**: Expected documents not returned

**Solutions**:
1. Lower score_threshold (<0.7)
2. Check if documents were ingested: Collection stats
3. Verify query embedding generation
4. Check payload filters
