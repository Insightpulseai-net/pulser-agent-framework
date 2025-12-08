# n8n Automation Hub - Implementation Plan

## Document Control
- **Version**: 1.0.0
- **Status**: Draft
- **Last Updated**: 2025-12-08
- **Author**: InsightPulseAI Platform Team

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           External Systems                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Slack    │  │   GitHub    │  │    Email    │  │  External   │        │
│  │             │  │             │  │   (SMTP)    │  │    APIs     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┼────────────────┼────────────────┘
                           │                │
                    ┌──────▼────────────────▼──────┐
                    │      n8n Automation Hub      │
                    │   (n8n.insightpulseai.net)   │
                    └──────────────┬───────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Odoo CE/OCA    │    │    Supabase     │    │ MCP Coordinator │
│  159.223.75.148 │    │   PostgreSQL    │    │   (Agents)      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Partners      │    │ • bronze.*      │    │ • Task Router   │
│ • Products      │    │ • silver.*      │    │ • Agent Pool    │
│ • Invoices      │    │ • gold.*        │    │ • Results Store │
│ • Attachments   │    │ • public.*      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 Container Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        n8n Docker Stack                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           nginx (proxy)                              │   │
│  │                         Port: 80, 443                                │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                          │
│                    ┌─────────────┴─────────────┐                           │
│                    │                           │                            │
│           ┌────────▼────────┐        ┌────────▼────────┐                   │
│           │    n8n-main     │        │   n8n-worker    │                   │
│           │   Port: 5678    │        │   (executor)    │                   │
│           │   • Web UI      │        │   • Workflows   │                   │
│           │   • API         │        │   • Webhooks    │                   │
│           │   • Scheduler   │        │                 │                   │
│           └────────┬────────┘        └────────┬────────┘                   │
│                    │                          │                             │
│                    └────────────┬─────────────┘                            │
│                                 │                                           │
│              ┌──────────────────┼──────────────────┐                       │
│              │                  │                  │                        │
│     ┌────────▼────────┐ ┌──────▼───────┐ ┌───────▼───────┐                │
│     │   PostgreSQL    │ │    Redis     │ │    backup     │                │
│     │   Port: 5432    │ │  Port: 6379  │ │   (cron)      │                │
│     │   • Workflows   │ │  • Queue     │ │   • Exports   │                │
│     │   • Executions  │ │  • Pub/Sub   │ │   • DB dumps  │                │
│     │   • Credentials │ │  • Cache     │ │               │                │
│     └─────────────────┘ └──────────────┘ └───────────────┘                │
│                                                                             │
│  Volumes:                                                                   │
│    n8n-data       → /home/node/.n8n                                        │
│    postgres-data  → /var/lib/postgresql/data                               │
│    redis-data     → /data                                                  │
│    backup-data    → /backups                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Network Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DigitalOcean VPC                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Private Network (10.116.0.0/20)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │   ┌───────────────┐     ┌───────────────┐     ┌───────────────┐    │   │
│  │   │  n8n Droplet  │     │ Odoo Droplet  │     │ Supabase DB   │    │   │
│  │   │  10.116.0.X   │────▶│ 10.116.0.Y    │     │ 10.116.0.Z    │    │   │
│  │   │               │     │               │     │               │    │   │
│  │   └───────┬───────┘     └───────────────┘     └───────────────┘    │   │
│  │           │                                           ▲             │   │
│  │           │                                           │             │   │
│  │           └───────────────────────────────────────────┘             │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Public Network                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │   n8n.insightpulseai.net ─────► nginx (443) ─────► n8n (5678)      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Core Components

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Automation Engine | n8n | 1.70+ | Workflow execution |
| Database | PostgreSQL | 15 | Workflow/execution storage |
| Queue | Redis | 7 | Execution queue, pub/sub |
| Reverse Proxy | nginx | 1.24 | TLS termination, routing |
| Container Runtime | Docker | 24+ | Service isolation |
| Orchestration | Docker Compose | 2.20+ | Multi-container management |

### 2.2 Integration Libraries

| Integration | Method | Library/Node |
|-------------|--------|--------------|
| Odoo CE/OCA 18 | XML-RPC | Custom HTTP node |
| Supabase | REST API | HTTP Request node |
| PostgreSQL | Direct | PostgreSQL node |
| MCP Coordinator | HTTP | HTTP Request node |
| Slack | Webhook | Slack node |
| Email | SMTP | Email node |
| Files | S3-compatible | S3 node (MinIO) |

### 2.3 Monitoring Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Metrics | Prometheus | n8n metrics collection |
| Dashboards | Grafana | Visualization |
| Alerting | Alertmanager | Notification routing |
| Logging | Docker logs + Loki | Centralized logging |

---

## 3. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Objective**: Deploy n8n with core infrastructure

| Task ID | Task | Owner | Status |
|---------|------|-------|--------|
| P1-001 | Provision DigitalOcean droplet | DevOps | TODO |
| P1-002 | Configure DNS (n8n.insightpulseai.net) | DevOps | TODO |
| P1-003 | Create Docker Compose stack | DevOps | TODO |
| P1-004 | Deploy PostgreSQL + Redis | DevOps | TODO |
| P1-005 | Deploy n8n main + worker | DevOps | TODO |
| P1-006 | Configure nginx + TLS | DevOps | TODO |
| P1-007 | Set up backup automation | DevOps | TODO |
| P1-008 | Configure environment variables | DevOps | TODO |
| P1-009 | Test basic workflow execution | DevOps | TODO |
| P1-010 | Document deployment process | DevOps | TODO |

**Deliverables**:
- n8n accessible at https://n8n.insightpulseai.net
- Automated daily backups
- Basic health monitoring

### Phase 2: Odoo Integration (Week 3-4)

**Objective**: Enable bidirectional Odoo sync workflows

| Task ID | Task | Owner | Status |
|---------|------|-------|--------|
| P2-001 | Create Odoo XML-RPC credentials | Integration | TODO |
| P2-002 | Build partner sync workflow | Integration | TODO |
| P2-003 | Build product sync workflow | Integration | TODO |
| P2-004 | Build invoice sync workflow | Integration | TODO |
| P2-005 | Configure Odoo webhooks | Integration | TODO |
| P2-006 | Test webhook reliability | Integration | TODO |
| P2-007 | Implement retry logic | Integration | TODO |
| P2-008 | Set up Slack error alerts | Integration | TODO |
| P2-009 | Create workflow documentation | Integration | TODO |
| P2-010 | Performance benchmark | Integration | TODO |

**Deliverables**:
- Partner/Product/Invoice sync workflows
- < 5 minute sync latency
- Error alerting operational

### Phase 3: Agent Orchestration (Week 5-6)

**Objective**: Enable AI agent workflow integration

| Task ID | Task | Owner | Status |
|---------|------|-------|--------|
| P3-001 | Create MCP coordinator credentials | Integration | TODO |
| P3-002 | Build agent task submission workflow | Integration | TODO |
| P3-003 | Implement polling for results | Integration | TODO |
| P3-004 | Build document processing workflow | Integration | TODO |
| P3-005 | Implement human-in-loop gates | Integration | TODO |
| P3-006 | Create agent error handling | Integration | TODO |
| P3-007 | Build multi-agent routing | Integration | TODO |
| P3-008 | Test timeout scenarios | Integration | TODO |
| P3-009 | Create agent workflow templates | Integration | TODO |
| P3-010 | Document agent patterns | Integration | TODO |

**Deliverables**:
- Agent orchestration workflows
- Human approval workflow
- Agent failure handling

### Phase 4: Medallion Pipeline (Week 7-8)

**Objective**: Automate data pipeline transformations

| Task ID | Task | Owner | Status |
|---------|------|-------|--------|
| P4-001 | Create PostgreSQL credentials (Supabase) | Data | TODO |
| P4-002 | Build Bronze ingestion workflows | Data | TODO |
| P4-003 | Build Silver transformation triggers | Data | TODO |
| P4-004 | Build Gold aggregation triggers | Data | TODO |
| P4-005 | Implement pipeline scheduling | Data | TODO |
| P4-006 | Create data quality workflows | Data | TODO |
| P4-007 | Build lineage tracking | Data | TODO |
| P4-008 | Create pipeline monitoring dashboard | Data | TODO |
| P4-009 | Test pipeline recovery | Data | TODO |
| P4-010 | Document pipeline patterns | Data | TODO |

**Deliverables**:
- Automated Medallion transforms
- Pipeline scheduling
- Data quality checks

---

## 4. Infrastructure Specifications

### 4.1 Droplet Requirements

| Specification | Minimum | Recommended |
|---------------|---------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| Memory | 4 GB | 8 GB |
| Storage | 80 GB SSD | 160 GB SSD |
| Network | 1 Gbps | 1 Gbps |
| Region | NYC3 | NYC3 (same as Odoo) |

### 4.2 Docker Resource Limits

```yaml
services:
  n8n-main:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  n8n-worker:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  postgres:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redis:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### 4.3 Volume Configuration

| Volume | Mount Path | Size | Backup |
|--------|------------|------|--------|
| n8n-data | /home/node/.n8n | 10 GB | Daily |
| postgres-data | /var/lib/postgresql/data | 50 GB | Hourly |
| redis-data | /data | 5 GB | Daily |
| backup-data | /backups | 50 GB | Weekly rotation |

---

## 5. Configuration Templates

### 5.1 Docker Compose

```yaml
# docker-compose.n8n.yml
version: '3.8'

services:
  n8n-postgres:
    image: postgres:15-alpine
    container_name: n8n-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${N8N_DB_USER}
      POSTGRES_PASSWORD: ${N8N_DB_PASSWORD}
      POSTGRES_DB: ${N8N_DB_NAME}
    volumes:
      - n8n-postgres-data:/var/lib/postgresql/data
    networks:
      - n8n-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${N8N_DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n-redis:
    image: redis:7-alpine
    container_name: n8n-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - n8n-redis-data:/data
    networks:
      - n8n-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n-main:
    image: n8nio/n8n:latest
    container_name: n8n-main
    restart: unless-stopped
    environment:
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://${N8N_HOST}/
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=n8n-postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${N8N_DB_NAME}
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=n8n-redis
      - QUEUE_BULL_REDIS_PORT=6379
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - GENERIC_TIMEZONE=${TIMEZONE}
      - N8N_LOG_LEVEL=info
      - N8N_METRICS=true
    volumes:
      - n8n-data:/home/node/.n8n
    networks:
      - n8n-network
    ports:
      - "127.0.0.1:5678:5678"
    depends_on:
      n8n-postgres:
        condition: service_healthy
      n8n-redis:
        condition: service_healthy

  n8n-worker:
    image: n8nio/n8n:latest
    container_name: n8n-worker
    restart: unless-stopped
    command: worker
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=n8n-postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${N8N_DB_NAME}
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=n8n-redis
      - QUEUE_BULL_REDIS_PORT=6379
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - GENERIC_TIMEZONE=${TIMEZONE}
    volumes:
      - n8n-data:/home/node/.n8n
    networks:
      - n8n-network
    depends_on:
      - n8n-main

volumes:
  n8n-data:
  n8n-postgres-data:
  n8n-redis-data:

networks:
  n8n-network:
    driver: bridge
```

### 5.2 Environment Variables

```bash
# .env.n8n.example

# n8n Configuration
N8N_HOST=n8n.insightpulseai.net
N8N_ENCRYPTION_KEY=generate-32-char-key
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password

# Database
N8N_DB_NAME=n8n
N8N_DB_USER=n8n
N8N_DB_PASSWORD=secure-db-password

# Timezone
TIMEZONE=America/New_York

# Odoo Integration
ODOO_URL=https://odoo.insightpulseai.net
ODOO_DB=odoo
ODOO_USER=api-user
ODOO_API_KEY=odoo-api-key

# Supabase Integration
SUPABASE_URL=https://supabase.insightpulseai.net
SUPABASE_SERVICE_KEY=service-role-key

# MCP Coordinator
MCP_COORDINATOR_URL=http://mcp-coordinator:8080
MCP_COORDINATOR_TOKEN=internal-token

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Backup
BACKUP_ENCRYPTION_KEY=backup-encryption-key
```

### 5.3 nginx Configuration

```nginx
# /etc/nginx/sites-available/n8n.conf

upstream n8n {
    server 127.0.0.1:5678;
    keepalive 32;
}

server {
    listen 80;
    server_name n8n.insightpulseai.net;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name n8n.insightpulseai.net;

    ssl_certificate /etc/letsencrypt/live/n8n.insightpulseai.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/n8n.insightpulseai.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Webhook endpoints (no rate limit)
    location /webhook/ {
        proxy_pass http://n8n;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
    }

    location /webhook-test/ {
        proxy_pass http://n8n;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
    }

    # WebSocket support for editor
    location / {
        proxy_pass http://n8n;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Rate limiting for API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://n8n;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 6. Workflow Patterns

### 6.1 Odoo Sync Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    Odoo Partner Sync Pattern                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [Webhook Trigger]                                             │
│         │                                                       │
│         ▼                                                       │
│   [Validate Signature] ─── Invalid ──► [Return 401]            │
│         │                                                       │
│         ▼ Valid                                                 │
│   [Parse Payload]                                               │
│         │                                                       │
│         ▼                                                       │
│   [Map to Bronze Schema]                                        │
│         │                                                       │
│         ▼                                                       │
│   [Upsert bronze.raw_odoo_partners]                            │
│         │                                                       │
│         ├─── Success ──► [Trigger Silver Transform]            │
│         │                        │                              │
│         │                        ▼                              │
│         │               [Execute SQL Transform]                 │
│         │                        │                              │
│         │                        ▼                              │
│         │               [Log Success] ──► [End]                │
│         │                                                       │
│         └─── Error ──► [Log Error] ──► [Alert Slack]           │
│                               │                                 │
│                               ▼                                 │
│                        [Return 500]                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Agent Orchestration Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Task Orchestration                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [Schedule/Manual Trigger]                                     │
│         │                                                       │
│         ▼                                                       │
│   [Prepare Task Payload]                                        │
│         │                                                       │
│         ▼                                                       │
│   [Submit to MCP Coordinator]                                   │
│         │                                                       │
│         ▼                                                       │
│   [Get Task ID]                                                 │
│         │                                                       │
│         ▼                                                       │
│   ┌─────────────────────────────────────────┐                  │
│   │           Polling Loop (max 10 min)     │                  │
│   │                                         │                  │
│   │   [Wait 30s] ──► [Check Status]         │                  │
│   │                        │                │                  │
│   │                        ├── Pending ─────┘                  │
│   │                        │                                   │
│   │                        ├── Success ──► [Parse Results]     │
│   │                        │                     │              │
│   │                        │                     ▼              │
│   │                        │              [Store Results]      │
│   │                        │                     │              │
│   │                        │                     ▼              │
│   │                        │              [Trigger Next]       │
│   │                        │                                   │
│   │                        └── Failed ──► [Error Handler]      │
│   │                                            │               │
│   └────────────────────────────────────────────┼───────────────┘
│                                                │                │
│                                                ▼                │
│                                         [Alert Slack]          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Error Handling Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    Standard Error Handler                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [Error Trigger]                                               │
│         │                                                       │
│         ▼                                                       │
│   [Capture Error Details]                                       │
│         │                                                       │
│         ▼                                                       │
│   [Categorize Error]                                            │
│         │                                                       │
│         ├── Transient (network, timeout)                        │
│         │         │                                             │
│         │         ▼                                             │
│         │   [Check Retry Count]                                 │
│         │         │                                             │
│         │         ├── < 3 ──► [Schedule Retry]                  │
│         │         │                                             │
│         │         └── >= 3 ──► [Dead Letter]                   │
│         │                                                       │
│         ├── Permanent (validation, auth)                        │
│         │         │                                             │
│         │         ▼                                             │
│         │   [Log Permanent Error]                               │
│         │         │                                             │
│         │         ▼                                             │
│         │   [Alert Slack]                                       │
│         │                                                       │
│         └── Critical (data loss risk)                           │
│                   │                                             │
│                   ▼                                             │
│             [Halt Processing]                                   │
│                   │                                             │
│                   ▼                                             │
│             [Page On-Call]                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Authentication Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   External Request                                              │
│         │                                                       │
│         ▼                                                       │
│   ┌─────────────────┐                                          │
│   │  nginx (TLS)    │                                          │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ├── /webhook/* ──► [HMAC Validation] ──► n8n        │
│            │                                                    │
│            ├── /api/* ──► [Basic Auth] ──► n8n                 │
│            │                                                    │
│            └── /* ──► [Basic Auth + Session] ──► n8n           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Credential Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                   Credential Security                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [User Creates Credential]                                     │
│            │                                                    │
│            ▼                                                    │
│   [n8n Encrypts with N8N_ENCRYPTION_KEY]                       │
│            │                                                    │
│            ▼                                                    │
│   [Store in PostgreSQL credentials_entity]                      │
│            │                                                    │
│            ▼                                                    │
│   [On Use: Decrypt in Memory]                                   │
│            │                                                    │
│            ▼                                                    │
│   [Execute with Credential]                                     │
│            │                                                    │
│            ▼                                                    │
│   [Clear from Memory]                                           │
│                                                                 │
│   Notes:                                                        │
│   - N8N_ENCRYPTION_KEY stored in .env (not in DB)              │
│   - Credentials never logged                                    │
│   - Export excludes decrypted values                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Monitoring and Alerting

### 8.1 Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `n8n_workflow_executions_total` | Total executions | N/A (tracking) |
| `n8n_workflow_execution_duration_seconds` | Execution time | P95 > 60s |
| `n8n_workflow_execution_errors_total` | Failed executions | Rate > 5% |
| `n8n_active_executions` | Running workflows | > 50 |
| `n8n_webhook_requests_total` | Webhook calls | N/A (tracking) |

### 8.2 Health Checks

```yaml
# prometheus/n8n-targets.yml
- targets:
  - n8n-main:5678
  labels:
    job: n8n
    __metrics_path__: /metrics
```

### 8.3 Alert Rules

```yaml
# prometheus/rules/n8n.yml
groups:
  - name: n8n
    rules:
      - alert: N8nHighErrorRate
        expr: |
          sum(rate(n8n_workflow_execution_errors_total[5m]))
          / sum(rate(n8n_workflow_executions_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High n8n error rate"

      - alert: N8nExecutionBacklog
        expr: n8n_active_executions > 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "n8n execution backlog growing"
```

---

## 9. Backup and Recovery

### 9.1 Backup Schedule

| Component | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| PostgreSQL | Hourly | 7 days | pg_dump |
| Workflows (JSON) | Daily | 30 days | API export |
| Credentials | Daily | 30 days | Encrypted dump |
| Configuration | Daily | 90 days | File backup |

### 9.2 Recovery Procedures

```bash
# Database restore
docker exec -i n8n-postgres psql -U n8n -d n8n < backup.sql

# Workflow restore
curl -X POST "http://localhost:5678/api/v1/workflows" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d @workflows.json
```

---

## 10. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Credential exposure | High | Encryption + access logging |
| Workflow infinite loop | Medium | Execution timeout + loop detection |
| Database corruption | High | Hourly backups + replication |
| Integration failure | Medium | Retry logic + circuit breaker |
| Resource exhaustion | Medium | Container limits + monitoring |

---

## Appendix A: Deployment Checklist

- [ ] Droplet provisioned with required specs
- [ ] DNS configured (n8n.insightpulseai.net)
- [ ] TLS certificate obtained
- [ ] Docker Compose stack deployed
- [ ] Environment variables configured
- [ ] nginx reverse proxy configured
- [ ] Health checks passing
- [ ] Backup automation verified
- [ ] Monitoring configured
- [ ] First workflow tested

## Appendix B: Useful Commands

```bash
# Start stack
docker compose -f docker-compose.n8n.yml up -d

# View logs
docker compose -f docker-compose.n8n.yml logs -f n8n-main

# Export workflows
curl -X GET "https://n8n.insightpulseai.net/api/v1/workflows" \
  -H "Authorization: Basic $AUTH" | jq '.' > workflows.json

# Database backup
docker exec n8n-postgres pg_dump -U n8n n8n > n8n_backup.sql
```
