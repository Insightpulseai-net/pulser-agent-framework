# Eric Vyacheslav AI/ML Content Catalog

> **Generated:** 2025-12-31
> **Source:** [LinkedIn Profile](https://www.linkedin.com/in/eric-vyacheslav-156273169/)
> **Coverage:** 7 months (June 2025 - December 2025)
> **Posts Analyzed:** 140+

---

## Profile Overview

| Attribute | Value |
|-----------|-------|
| **Name** | Eric Vyacheslav |
| **Title** | AI/ML Engineer |
| **Background** | Ex-Google, Ex-MIT |
| **Followers** | 371,446 |
| **Newsletter** | [AlphaSignal.ai](https://alphasignal.ai) |
| **Focus** | AI tools, repos, papers, breakthrough models |

**About AlphaSignal:** A daily newsletter providing 5-minute summaries of breakthrough AI models, repos, and papers. Read by 200,000+ developers and researchers.

---

## Table of Contents

1. [Agent Frameworks & Orchestration](#1-agent-frameworks--orchestration)
2. [Claude/Anthropic Ecosystem](#2-claudeanthropic-ecosystem)
3. [Developer Tools & Productivity](#3-developer-tools--productivity)
4. [AI/ML Training & Optimization](#4-aiml-training--optimization)
5. [Document Processing & OCR](#5-document-processing--ocr)
6. [Vision & Multimodal AI](#6-vision--multimodal-ai)
7. [Educational Resources](#7-educational-resources)
8. [Data Infrastructure & Scaling](#8-data-infrastructure--scaling)
9. [Industry Insights & Predictions](#9-industry-insights--predictions)
10. [Design Improvements for Pulser Framework](#10-design-improvements-for-pulser-framework)

---

## 1. Agent Frameworks & Orchestration

### Vibe Kanban - Multi-Agent Orchestrator
| Attribute | Details |
|-----------|---------|
| **Date** | 3 days ago |
| **Type** | Open Source Tool |
| **Stars** | High engagement (1,348 likes) |
| **Description** | Orchestrates multiple AI coding agents in parallel |

**Key Features:**
- Switch between Claude Code, Gemini CLI, and Codex instantly
- Track all task status from a single dashboard
- 100% open source
- Single interface for multiple AI tools

**Relevance to Pulser:** Direct competitor/reference for multi-agent orchestration layer.

---

### AgentScope by Alibaba
| Attribute | Details |
|-----------|---------|
| **Date** | 4 days ago |
| **Type** | Open Source Framework |
| **Platform** | Python |
| **Description** | Multi-agent AI app framework with visual tools |

**Key Features:**
- Works with any LLM provider
- Real-time steering and control
- MCP tool integration
- Visual development interface
- Memory, RAG, and reasoning capabilities

**Relevance to Pulser:** Reference architecture for multi-agent systems with MCP integration.

---

### LangChain Deep Agents
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week ago |
| **Type** | Open Source Library |
| **Description** | Python library that turns any LLM into a deep thinking agent |

**Key Features:**
- Reverse-engineered Claude Code and Manus AI
- MCP tools for enhanced functionality
- Deep reasoning framework
- Production-ready implementation

**Relevance to Pulser:** Pattern for adding reasoning capabilities to existing models.

---

### IBM watsonx Orchestrate
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks ago |
| **Type** | Enterprise Platform |
| **Use Cases** | Ferrari (40% deployment time reduction), UFC (70% automation) |

**Key Features:**
- Single control plane connecting agents across OpenAI, Anthropic, etc.
- Visual workflow builder for non-technical teams
- Real-time monitoring for compliance
- No rip-and-replace required

**Enterprise Pattern:** Control plane + visual builders + monitoring.

---

### Sim - Open Source n8n Alternative
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks ago |
| **Type** | Open Source Platform |
| **URL** | github.com (referenced) |

**Key Features:**
- Drag-and-drop platform for agentic workflows
- Runs entirely on local machine
- Works with any local LLM
- MCP integration for APIs and tools

**Relevance to Pulser:** Alternative architecture for visual workflow building.

---

### OpenAI A-SWE (Agentic Software Engineer)
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week ago |
| **Source** | CFO Sarah Friar |

**Capabilities:**
- Builds complete applications
- Manages pull requests
- Conducts quality assurance
- Fixes bugs automatically
- Writes documentation

**Trend:** Full SDLC automation, not just code completion.

---

### Steve - Minecraft AI Agent
| Attribute | Details |
|-----------|---------|
| **Date** | 3 days ago |
| **Creator** | Peak AI |
| **Type** | Open Source Mod |

**Key Features:**
- Natural language commands in Minecraft
- Supports Groq, OpenAI, and Gemini models
- Multi-step task planning
- Autonomous mining, building, exploration

**Pattern:** Natural language → game action sequences.

---

## 2. Claude/Anthropic Ecosystem

### Claude Code for Product Managers
| Attribute | Details |
|-----------|---------|
| **Date** | 2 days ago |
| **Type** | Open Source Tool |
| **Workflow** | PRD → Epics → GitHub Issues → Production Code |

**Key Features:**
- Transforms PRDs into epics automatically
- Converts epics into GitHub issues
- Generates production code from issues
- Full traceability across every step

**Relevance to Pulser:** PRD-to-code pipeline pattern.

---

### Claude CLI with 100+ Pre-made Agents
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks ago |
| **Type** | Open Source Repository |

**Included Agents:**
- File management agents
- Code generation templates
- Data analysis tools
- Custom MCP connectors

**Key Feature:** Single command installation, works with Claude Desktop.

---

### MCP-UI - UI Components for MCP Servers
| Attribute | Details |
|-----------|---------|
| **Date** | 1 month ago |
| **Type** | Open Source SDK |

**SDKs Available:**
- `@mcp-ui/server` (TypeScript) - generates UI resources
- `@mcp-ui/client` (TypeScript) - renders UI in clients
- `mcp_ui_server` (Ruby)
- `mcp-ui-server` (Python)

**Features:** Interactive tables, charts, buttons for Claude/Cursor.

---

### Local RAG with 97% Storage Reduction
| Attribute | Details |
|-----------|---------|
| **Date** | 5 days ago |
| **Type** | MCP Server |
| **Platform** | Ollama + Claude Desktop |

**Key Features:**
- Index millions of documents on laptop
- No cloud dependencies or subscription fees
- Drop-in semantic search MCP for Claude Desktop
- 100% open source with no usage limits

**Technical Advantage:** 97% less storage than traditional vector databases.

---

### Anthropic Prompt Engineering Course
| Attribute | Details |
|-----------|---------|
| **Date** | 7 months ago |
| **Type** | Free Educational Resource |
| **Format** | 9 chapters with exercises |

**Learning Outcomes:**
- Master basic prompt structure
- Recognize common failure modes
- 80/20 techniques for addressing issues
- Build prompts from scratch for common use cases

---

### Claude 4 System Prompt Leak
| Attribute | Details |
|-----------|---------|
| **Date** | 7 months ago |
| **Length** | 10,000 - 24,000 tokens |

**Revealed Patterns:**
- Declarative Intent for explaining limitations
- Boundary Signaling and conditional logic
- Hallucination mitigation via fallback rules
- XML-like protocols for tool invocation
- Positional Reinforcement to reduce drift

---

## 3. Developer Tools & Productivity

### DeepWiki - GitHub Repository Encyclopedia
| Attribute | Details |
|-----------|---------|
| **Date** | 4-7 months ago (multiple posts) |
| **Creator** | Cognition AI (Devin team) |
| **Repos Indexed** | 50,000+ |
| **Code Processed** | 4 billion+ lines |
| **Compute Cost** | $300k+ |

**How to Use:** Replace `github.com` with `deepwiki.com` in any repo URL.

**Features:**
- Quick file scanning
- Deep Research mode
- Free for open source projects
- Interactive wiki documentation

---

### Gemini Code Wiki
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week ago |
| **Type** | Free Tool |

**Features:**
- Generate interactive documentation from any GitHub URL
- Visualize code structure
- Chat with Gemini to understand repositories

---

### GitDiagram
| Attribute | Details |
|-----------|---------|
| **Date** | 7 months ago |
| **Engagement** | 3,579 likes |

**How to Use:** Replace `github` with `gitdiagram` in any GitHub URL.
**Output:** Interactive diagrams of the codebase.

---

### GitSearchAI + GitToDoc → Cursor MVP Pipeline
| Attribute | Details |
|-----------|---------|
| **Date** | 4-6 months ago |
| **Workflow** | GitHub README → Documentation → Working MVP |

**Pipeline:**
1. `gitsearchai.com` - search repositories with AI
2. `gittodoc.com` - turn repository into documentation
3. Cursor - add documentation and execute

---

### Deepnote - Open Source Notebooks
| Attribute | Details |
|-----------|---------|
| **Date** | 3 weeks - 1 month ago |
| **License** | Apache 2.0 |
| **Users** | 500,000+ data professionals |

**Key Features:**
- 23 new block types
- 100+ native data connectors
- Works in VS Code, Cursor, Antigravity
- Reactive execution in cloud
- Real-time collaboration with AI agents

**Command:** `npx @deepnote/convert notebook.ipynb`

---

### Microsoft Data Formulator
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week ago |
| **Type** | Open Source |

**Features:**
- AI-powered no-code data analysis
- Drag-and-drop visualization
- Iterative chart creation

---

## 4. AI/ML Training & Optimization

### Unsloth - Train Large Models on Consumer Hardware
| Attribute | Details |
|-----------|---------|
| **Date** | 6 days ago |
| **Model** | GPT-OSS-20B |
| **VRAM Required** | 15GB |

**Performance:**
- 3x faster inference than any implementation
- 50% memory reduction with zero accuracy loss
- Full RLHF pipeline fits in standard Colab instances

---

### Tiny Recursive Model (TRM)
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks ago |
| **Parameters** | 7M |
| **Training Cost** | Under $500 (2 H100s, 2 days) |
| **Inference Cost** | Less than $0.01 per task |

**Performance:** Surpasses DeepSeek R1, Gemini 2.5 Pro, and o3-mini on reasoning tasks.

**Recursive Reasoning Loop (5 steps):**
1. Drafts initial answer
2. Builds reasoning scratchpad
3. Compares logic and finds errors
4. Revises the answer
5. Repeats up to 16 times

**Key Insight:** "Architecture, not scale, is driving the next AI shift."

---

### GRPO for Robotics (DeepSeek Algorithm)
| Attribute | Details |
|-----------|---------|
| **Date** | 2-3 weeks ago |
| **Type** | RL Algorithm |

**How it Works:**
- Group Relative Policy Optimization
- Evaluates multiple outputs and assigns relative rewards
- Enables scalable, adaptive learning

**Impact:** Robots can refine skills like humans by comparing experiences.

---

### TabPFN-2.5
| Attribute | Details |
|-----------|---------|
| **Date** | 1 month ago |
| **Creator** | Prior Labs |
| **Downloads** | 2.3M+ |

**Performance:**
- #1 on TabArena (classification and regression)
- Beats tuned tree models and AutoGluon 1.4
- Handles up to 50k data points in single forward pass
- Results in seconds, not hours

---

## 5. Document Processing & OCR

### Best OCR Stack for Invoice Extraction
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks / 4 months ago |
| **Source** | @pontusab |

**Layered Approach:**
1. **Mistral OCR** - Primary extractor (high accuracy on structured layouts)
2. **Gemini 2.5 Flash** - Secondary pass (catches edge cases)
3. **Tesseract/PDF text layer** - Fallback when both OCR passes fail
4. **LLM Reconciliation** - Merge fields, resolve conflicts, produce clean output

---

### Google LangExtract
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week ago |
| **Type** | Python Library |
| **Engagement** | 2,342 likes |

**Features:**
- Extracts structured data from unstructured documents
- Precise source citations for every extracted piece
- Works with PDFs, text files, web content
- Handles tables, lists, complex structures
- No API keys or usage limits

---

### ByteDance Dolphin
| Attribute | Details |
|-----------|---------|
| **Date** | 1 month ago |
| **Model Size** | 0.3B multimodal VLM |

**Features:**
- Converts PDFs to Markdown, HTML, LaTeX, JSON
- Two-stage analyze-then-parse method
- Natural reading order generation
- Heterogeneous anchor prompting
- Parallel parsing for efficiency

---

### Chinese AI OCR Model
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week ago |
| **Type** | Open Source |

**Features:**
- Parse complex documents (text, tables, formulas, figures) in parallel
- Task-specific prompts
- 100% open source

---

## 6. Vision & Multimodal AI

### SmolVLM + llama.cpp Webcam Demo
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week - 7 months ago |
| **Engagement** | 3,479 - 9,017 likes |
| **Platform** | MacBook M3 |

**Capabilities:**
- Live video processing without cloud dependencies
- Visual understanding on consumer hardware
- Privacy-first computer vision
- Real-time processing

---

### NVIDIA PartPacker
| Attribute | Details |
|-----------|---------|
| **Date** | 3 months ago |
| **Engagement** | 1,286 likes |

**Features:**
- Generate 3D models from single image
- Dual-volume packing for clean, non-overlapping parts
- Outputs are animation-ready and editable
- Live demo on Hugging Face

---

### DeepSeek Desktop Automation Agent
| Attribute | Details |
|-----------|---------|
| **Date** | 1 day ago |
| **Type** | Local Agent |
| **Engagement** | 842 likes |

**Capabilities:**
- Controls any desktop app through vision models
- Opens files, browses websites, automates tasks
- Zero data leaves your machine
- Works with any installed software

---

### FLUX LoRA - Google Earth to Drone Photos
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks / 5 months ago |
| **Creator** | Reddit user (Ismail Seleit) |

**Features:**
- Converts low-res satellite images to professional aerial photography
- Maintains geographical accuracy
- Free download on Hugging Face

---

### BAGEL by ByteDance
| Attribute | Details |
|-----------|---------|
| **Date** | 7 months ago |
| **Type** | Open Source GPT-4o Alternative |

**Capabilities:**
- Image reasoning, editing
- Video generation
- Style transfer
- 3D rotation
- Outpainting

---

## 7. Educational Resources

### Stanford CS230 by Andrew Ng (Autumn 2025)
| Attribute | Details |
|-----------|---------|
| **Date** | 1 month ago |
| **Format** | Lecture Notes (227 pages) |

**Topics Covered:**
- CNNs, RNNs, LSTMs, Adam, Dropout, BatchNorm
- Reinforcement Learning, Agents, RAG, Multimodality
- Research reading and AI career lessons

---

### Stanford Agentic AI Lecture
| Attribute | Details |
|-----------|---------|
| **Date** | 7 months ago |
| **Duration** | 1 hour |
| **Engagement** | 2,813 likes |

**Topics:**
- Reflection, planning, tool use
- Memory and iterative reasoning
- Autonomous agents

---

### 424-Page Agentic AI Book by Google Engineer
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks ago |
| **Engagement** | 1,639 likes |

**Contents:**
- Multi-agent framework design
- RAG implementation strategies
- Agent tool integration patterns
- Model Context Protocol (MCP) usage
- Practical code examples

---

### 300+ ML System Design Case Studies
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week / 4 months ago |
| **Companies** | 80+ (Stripe, Spotify, Netflix, Meta, Airbnb, DoorDash) |

**Topics:**
- Fraud detection (Stripe)
- Recommendation engines (Netflix)
- Search algorithms (Airbnb)
- Ad targeting (Meta)
- NLP systems

---

### Context Engineering Repository
| Attribute | Details |
|-----------|---------|
| **Date** | 4 months ago |

**Topics:**
- Static prompting to dynamic context-aware systems
- Memory systems, RAG, MCP
- Context persistence
- Implementation guides and benchmarks

---

## 8. Data Infrastructure & Scaling

### MindsDB MCP Server
| Attribute | Details |
|-----------|---------|
| **Date** | 3 months ago |
| **Stars** | 30k+ |
| **Data Sources** | 200+ |

**Capabilities:**
- Query Slack, Gmail, databases, warehouses, SaaS apps
- SQL or natural language queries
- Knowledge Bases for unstructured data
- Federated query engine with embedded MCP server

---

### E2B Sandboxes (How Manus Scales Agents)
| Attribute | Details |
|-----------|---------|
| **Date** | 6 months ago |
| **Startup Time** | ~150ms |

**Architecture:**
- Every agent runs in own secure sandbox
- Fresh Linux VM with 27+ tools
- Browser access, file handling
- Sessions persist for hours
- Firecracker microVMs

---

### Encord E-MM1 Dataset
| Attribute | Details |
|-----------|---------|
| **Date** | 2 months ago |
| **Size** | 107 million multimodal data groups |
| **Scale** | 100x larger than existing datasets |

**Contents:**
- Images, videos, audio, text, 3D data
- 1 million pre-labeled examples
- Natural language search

---

### Nscale Inference
| Attribute | Details |
|-----------|---------|
| **Date** | 6 months ago |
| **Cost** | $0.03 for 75,000-word novel |

**Features:**
- No setup, cold starts, or servers
- Instant AI API endpoints
- Advanced fine-tuning (QLORA, DeepSpeed, FSDP)
- Private cloud and dedicated GPU clusters

---

## 9. Industry Insights & Predictions

### Ilya Sutskever: LLM Scaling Has Plateaued
| Attribute | Details |
|-----------|---------|
| **Date** | 3 weeks - 3 months ago |

**Key Points:**
- Compute continues to scale, but data is not keeping up
- Synthetic data hasn't significantly improved performance
- Progress will come from agents and tools built on top of LLMs
- Focus areas: Sequence-to-sequence learning, agentic behavior, self-awareness

---

### Sam Altman: Job Market Shift
| Attribute | Details |
|-----------|---------|
| **Date** | 1 week - 4 months ago |

**Key Points:**
- Cognitive roles (coding, design, writing) losing value
- Physical skills (plumbers, surgeons) gaining value
- "It's not about how smart you are; it's about what you can build or fix"

---

### Andrej Karpathy: AI Agents Not Ready
| Attribute | Details |
|-----------|---------|
| **Date** | 2 days ago |

**Five Critical Gaps:**
1. Limited intelligence for complex reasoning
2. Poor computer interaction skills
3. Insufficient multimodal processing
4. No continual learning ability
5. Memory issues with instructions

**Timeline:** Estimates fixing these problems will take a decade.

---

### Sergey Brin: Google's Transformer Mistake
| Attribute | Details |
|-----------|---------|
| **Date** | 2 weeks ago |

**Key Points:**
- Google invented transformers but held back on scaling compute
- Feared releasing chatbots that might "say dumb things"
- "We didn't take it very seriously"
- OpenAI took Google's research and scaled it

---

### Meta CEO Zuckerberg on AI Coding
| Attribute | Details |
|-----------|---------|
| **Date** | 8 months ago |

**Prediction:** "Within 12-18 months, most of the code is written by AI."

**Future State:**
- AI agents will set goals, run tests, find problems
- Write better code than top engineers
- Not just autocomplete

---

### Google AI Writing Code
| Attribute | Details |
|-----------|---------|
| **Date** | 1 month ago |

**Statistics:**
- AI tools now autocomplete 50% of all new code at Google
- Engineers accept 37% of AI-generated suggestions
- Next: Expand to debugging, testing, maintenance

---

## 10. Design Improvements for Pulser Framework

Based on 7 months of Eric Vyacheslav's curated AI/ML content, here are recommended improvements for the Pulser Agent Framework:

### 10.1 Multi-Agent Orchestration Layer

**Reference:** Vibe Kanban, IBM watsonx Orchestrate, AgentScope

```yaml
Recommended Features:
  - Single dashboard for multiple AI agents (Claude, Gemini, Codex)
  - Visual workflow builder for non-technical teams
  - Real-time monitoring and compliance auditing
  - Agent switching without context loss
  - Task status tracking across all agents
```

**Implementation Priority:** HIGH

---

### 10.2 MCP Integration Hub

**Reference:** MindsDB, MCP-UI, AgentScope, Sim

```yaml
Recommended Features:
  - Unified MCP server supporting 200+ data sources
  - UI component rendering for MCP tools
  - Visual development interface
  - SQL and natural language query support
  - Knowledge Base integration for RAG
```

**Implementation Priority:** HIGH

---

### 10.3 Local RAG with Storage Efficiency

**Reference:** 97% storage reduction MCP, Ollama integration

```yaml
Recommended Features:
  - Local semantic search with minimal storage
  - Drop-in MCP for Claude Desktop
  - Million-document indexing on consumer hardware
  - Zero cloud dependencies
  - Privacy-first architecture
```

**Implementation Priority:** MEDIUM

---

### 10.4 Document Processing Pipeline

**Reference:** OCR Stack, LangExtract, Dolphin

```yaml
Recommended Architecture:
  Primary:    Mistral OCR (structured layouts)
  Secondary:  Gemini 2.5 Flash (edge cases)
  Fallback:   Tesseract/PDF text layer
  Reconcile:  LLM-based field merging

Output Formats: Markdown, HTML, LaTeX, JSON
Features: Source citations, parallel parsing, reading order
```

**Implementation Priority:** MEDIUM

---

### 10.5 PRD-to-Code Pipeline

**Reference:** Claude Code for PMs

```yaml
Pipeline Stages:
  1. PRD → Epics (automatic transformation)
  2. Epics → GitHub Issues (with context)
  3. Issues → Production Code (with tests)
  4. Full Traceability (requirements to deployment)
```

**Implementation Priority:** HIGH

---

### 10.6 Repository Intelligence

**Reference:** DeepWiki, Gemini Code Wiki, GitDiagram

```yaml
Recommended Features:
  - Automatic wiki generation from any repo
  - Interactive code visualization
  - Chat-based repository exploration
  - Deep research mode for complex analysis
  - URL-based instant access (github → deepwiki pattern)
```

**Implementation Priority:** MEDIUM

---

### 10.7 Efficient Model Training

**Reference:** Unsloth, Tiny Recursive Model, GRPO

```yaml
Patterns to Adopt:
  - Consumer hardware training (15GB VRAM for 20B models)
  - Recursive reasoning loops (5-step refinement)
  - Relative reward evaluation (GRPO)
  - Architecture over scale philosophy
```

**Implementation Priority:** LOW (research)

---

### 10.8 Real-Time Vision Processing

**Reference:** SmolVLM + llama.cpp, DeepSeek Desktop Agent

```yaml
Recommended Features:
  - Local webcam/screen processing
  - Vision-based desktop automation
  - No cloud dependencies
  - Consumer hardware compatibility (M3/similar)
```

**Implementation Priority:** LOW

---

### 10.9 Agent Sandbox Architecture

**Reference:** E2B (Manus infrastructure)

```yaml
Recommended Features:
  - Isolated Firecracker microVMs per agent
  - 150ms startup time
  - 27+ tools per sandbox
  - Browser access and file handling
  - Multi-hour session persistence
```

**Implementation Priority:** MEDIUM

---

### 10.10 Compliance & Monitoring

**Reference:** IBM watsonx, Galileo evaluations

```yaml
Recommended Features:
  - Real-time visibility into agent actions
  - Audit trails for compliance
  - 20+ metrics for agent evaluation
  - Session-level summaries
  - Automatic issue detection
```

**Implementation Priority:** HIGH

---

## Key Repositories to Track

| Repository | Category | Purpose |
|------------|----------|---------|
| AgentScope | Agent Framework | Multi-agent apps with MCP |
| LangChain Deep Agents | Agent Framework | Deep reasoning for any LLM |
| Vibe Kanban | Orchestration | Multi-agent task management |
| Sim | Workflow | Open source n8n alternative |
| DeepWiki | Documentation | Repo wiki generation |
| MindsDB | Data | 200+ source MCP server |
| Unsloth | Training | Efficient large model training |
| LangExtract | Document | Structured data extraction |
| SmolVLM | Vision | Local real-time vision |
| MCP-UI | UI | MCP component rendering |

---

## Newsletter & Community

| Resource | URL | Description |
|----------|-----|-------------|
| **AlphaSignal** | https://alphasignal.ai | Daily AI breakthrough summaries |
| **LinkedIn** | Eric Vyacheslav | 371k+ followers, daily posts |
| **Substack** | alphasignalai.substack.com | Newsletter archive |

---

## Post Engagement Statistics (Sample)

| Post Topic | Likes | Comments | Reposts |
|------------|-------|----------|---------|
| SmolVLM Webcam Demo | 9,017 | 346 | 609 |
| Mathematicians throw shade | 6,918 | 110 | 138 |
| SmolVLM (repeat) | 6,653 | 184 | 372 |
| Claude 4 System Prompt Leak | 3,865 | 139 | 216 |
| Tiny Recursive Model (TRM) | 3,579 | 102 | 244 |
| GitDiagram | 3,579 | 115 | 375 |
| Claude kills document wrappers | 1,729 | 86 | 138 |

---

*This catalog is part of the Pulser Agent Framework documentation. Updated: 2025-12-31*
