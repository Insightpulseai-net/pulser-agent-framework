#!/usr/bin/env python3
"""
Skill Builder from Knowledge Base
==================================

Queries the knowledge base (Supabase pgvector) and generates
skill files in the Anthropic skills format.

Usage:
    export SUPABASE_URL="https://xxx.supabase.co"
    export SUPABASE_SERVICE_ROLE_KEY="..."
    export OPENAI_API_KEY="..."

    python tools/knowledge/build_skills.py
"""

import os
import json
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

import requests
from supabase import create_client, Client


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SkillIntent:
    """A skill intent to generate from knowledge base."""
    name: str
    description: str
    queries: List[str]  # Search queries to find relevant chunks
    category: str
    tags: List[str]


# Default skill intents (can be overridden via SKILLS_JSON env var)
DEFAULT_SKILLS = [
    SkillIntent(
        name='odoo-module-creation',
        description='How to create a new Odoo 18 module from scratch',
        queries=[
            'How to create Odoo module',
            'Odoo __manifest__.py structure',
            'Odoo model definition example',
            'Odoo view XML definition',
        ],
        category='odoo',
        tags=['odoo', 'python', 'erp', 'module'],
    ),
    SkillIntent(
        name='odoo-testing',
        description='Testing patterns for Odoo modules',
        queries=[
            'Odoo TransactionCase example',
            'Odoo test tagged decorator',
            'Odoo HttpCase testing',
            'Odoo test fixtures setup',
        ],
        category='odoo',
        tags=['odoo', 'testing', 'python'],
    ),
    SkillIntent(
        name='superset-dashboard',
        description='Creating Apache Superset dashboards',
        queries=[
            'Superset dashboard creation',
            'Superset chart configuration',
            'Superset SQL query dataset',
            'Superset visualization types',
        ],
        category='analytics',
        tags=['superset', 'analytics', 'dashboard'],
    ),
    SkillIntent(
        name='n8n-workflow',
        description='Building n8n automation workflows',
        queries=[
            'n8n workflow creation',
            'n8n node configuration',
            'n8n webhook trigger',
            'n8n code node JavaScript',
        ],
        category='automation',
        tags=['n8n', 'automation', 'workflow'],
    ),
    SkillIntent(
        name='fastapi-endpoint',
        description='Creating FastAPI REST endpoints',
        queries=[
            'FastAPI endpoint definition',
            'FastAPI Pydantic model',
            'FastAPI dependency injection',
            'FastAPI authentication JWT',
        ],
        category='backend',
        tags=['fastapi', 'python', 'api', 'rest'],
    ),
    SkillIntent(
        name='supabase-rls',
        description='Row Level Security in Supabase/PostgreSQL',
        queries=[
            'Supabase RLS policy example',
            'PostgreSQL row level security',
            'Supabase auth.uid() policy',
            'RLS enable table policy',
        ],
        category='database',
        tags=['supabase', 'postgresql', 'security', 'rls'],
    ),
]


# =============================================================================
# Embedding
# =============================================================================

def get_embedding(text: str) -> List[float]:
    """Get embedding for a single text."""
    api_key = os.environ['OPENAI_API_KEY']
    model = os.environ.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')

    response = requests.post(
        'https://api.openai.com/v1/embeddings',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={'model': model, 'input': text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()['data'][0]['embedding']


# =============================================================================
# Knowledge Search
# =============================================================================

def search_knowledge(
    sb: Client,
    query: str,
    match_count: int = 10,
    repo_filter: Optional[str] = None
) -> List[Dict]:
    """Search knowledge base using semantic search."""
    embedding = get_embedding(query)

    result = sb.rpc(
        'knowledge_search',
        {
            'query_embedding': embedding,
            'match_count': match_count,
            'repo_filter': repo_filter,
        }
    ).execute()

    return result.data


def dedupe_chunks(chunks: List[Dict], max_per_path: int = 2) -> List[Dict]:
    """Deduplicate chunks by path, keeping top N per file."""
    by_path: Dict[str, List[Dict]] = {}

    for chunk in chunks:
        path = chunk['path']
        if path not in by_path:
            by_path[path] = []
        if len(by_path[path]) < max_per_path:
            by_path[path].append(chunk)

    result = []
    for path_chunks in by_path.values():
        result.extend(path_chunks)

    return sorted(result, key=lambda x: x['score'], reverse=True)


# =============================================================================
# Skill Generation
# =============================================================================

def generate_skill_content(intent: SkillIntent, chunks: List[Dict]) -> str:
    """Generate skill.md content from intent and chunks."""
    lines = [
        f'# {intent.name}',
        '',
        f'> {intent.description}',
        '',
        '## Overview',
        '',
        f'This skill covers {intent.description.lower()}.',
        '',
        '## When to Use',
        '',
        f'Use this skill when you need to:',
    ]

    # Add use cases based on queries
    for query in intent.queries[:3]:
        lines.append(f'- {query}')

    lines.extend([
        '',
        '## Key Concepts',
        '',
    ])

    # Extract key concepts from chunks
    seen_content = set()
    for i, chunk in enumerate(chunks[:5]):
        content = chunk['content'][:500]
        if content not in seen_content:
            seen_content.add(content)
            lines.extend([
                f'### Source: {chunk["repo"]} - {chunk["path"]}',
                '',
                '```',
                content,
                '```',
                '',
            ])

    lines.extend([
        '## Examples',
        '',
    ])

    # Add code examples from chunks
    code_chunks = [c for c in chunks if c.get('meta', {}).get('lang') in ['python', 'javascript', 'typescript', 'sql']]
    for chunk in code_chunks[:3]:
        lang = chunk.get('meta', {}).get('lang', 'text')
        lines.extend([
            f'### From {chunk["path"]}',
            '',
            f'```{lang}',
            chunk['content'][:800],
            '```',
            '',
        ])

    lines.extend([
        '## Sources',
        '',
    ])

    # Add source references
    seen_urls = set()
    for chunk in chunks:
        url = chunk.get('meta', {}).get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            lines.append(f'- [{chunk["repo"]} / {chunk["path"]}]({url})')

    lines.extend([
        '',
        '---',
        '',
        f'*Generated from knowledge base on {datetime.now().strftime("%Y-%m-%d")}*',
        f'*Category: {intent.category}*',
        f'*Tags: {", ".join(intent.tags)}*',
    ])

    return '\n'.join(lines)


def write_skill(skill_name: str, content: str, examples: List[Dict]):
    """Write skill files to disk."""
    skill_dir = pathlib.Path(f'skills/{skill_name}')
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Write main skill file
    (skill_dir / 'skill.md').write_text(content, encoding='utf-8')

    # Write examples
    examples_dir = skill_dir / 'examples'
    examples_dir.mkdir(exist_ok=True)

    for i, example in enumerate(examples[:5]):
        example_file = examples_dir / f'example_{i+1}.md'
        example_content = f"""# Example {i+1}

Source: {example.get('repo', 'unknown')} / {example.get('path', 'unknown')}

```
{example.get('content', '')}
```

[View source]({example.get('meta', {}).get('url', '#')})
"""
        example_file.write_text(example_content, encoding='utf-8')

    # Write eval checklist
    eval_dir = skill_dir / 'eval'
    eval_dir.mkdir(exist_ok=True)

    checklist = f"""# Evaluation Checklist for {skill_name}

## Accuracy
- [ ] Code examples compile/run correctly
- [ ] Instructions match current API/version
- [ ] No deprecated patterns used

## Completeness
- [ ] Covers common use cases
- [ ] Includes error handling
- [ ] Has working examples

## Sources
- [ ] All sources properly attributed
- [ ] Links are valid
- [ ] License compliance verified
"""
    (eval_dir / 'checklist.md').write_text(checklist, encoding='utf-8')


# =============================================================================
# Main
# =============================================================================

def main():
    """Build skills from knowledge base."""
    supabase_url = os.environ['SUPABASE_URL']
    supabase_key = os.environ['SUPABASE_SERVICE_ROLE_KEY']

    sb = create_client(supabase_url, supabase_key)

    # Load skill intents
    skills_json = os.environ.get('SKILLS_JSON')
    if skills_json:
        skills_data = json.loads(skills_json)
        skills = [SkillIntent(**s) for s in skills_data]
    else:
        skills = DEFAULT_SKILLS

    print(f'Building {len(skills)} skills from knowledge base...')

    for intent in skills:
        print(f'\n[{intent.name}] Searching for relevant content...')

        # Search for each query
        all_chunks = []
        for query in intent.queries:
            chunks = search_knowledge(sb, query, match_count=10)
            all_chunks.extend(chunks)

        # Dedupe and rank
        chunks = dedupe_chunks(all_chunks, max_per_path=2)
        print(f'  Found {len(chunks)} unique chunks')

        if not chunks:
            print(f'  [SKIP] No content found')
            continue

        # Generate skill content
        content = generate_skill_content(intent, chunks)

        # Write skill files
        write_skill(intent.name, content, chunks[:5])
        print(f'  [OK] Generated skills/{intent.name}/')

        # Store in database
        try:
            chunk_ids = [c.get('id') for c in chunks[:20] if c.get('id')]
            sb.table('skills').upsert({
                'name': intent.name,
                'description': intent.description,
                'category': intent.category,
                'tags': intent.tags,
                'content': content,
                'source_chunks': chunk_ids,
            }, on_conflict='name').execute()
        except Exception as e:
            print(f'  [WARN] Could not save to database: {e}')

    print('\n' + '=' * 60)
    print('SKILL GENERATION COMPLETE')
    print(f'Generated {len(skills)} skills in skills/ directory')
    print('=' * 60)


if __name__ == '__main__':
    main()
