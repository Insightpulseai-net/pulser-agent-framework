#!/usr/bin/env python3
"""
Knowledge Base Ingestion Pipeline
==================================

Crawls GitHub repositories, chunks content, generates embeddings,
and stores in Supabase pgvector for RAG + skill generation.

Usage:
    export SUPABASE_URL="https://xxx.supabase.co"
    export SUPABASE_SERVICE_ROLE_KEY="..."
    export OPENAI_API_KEY="..."
    export REPOS_JSON='[{"repo":"owner/name","url":"...","ref":"main"}]'

    python tools/knowledge/ingest_repos.py
"""

import os
import re
import json
import hashlib
import pathlib
import tempfile
import shutil
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

import yaml
import tiktoken
import requests
from git import Repo
from supabase import create_client, Client
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Filters:
    """File filtering configuration."""
    include_ext: Set[str]
    exclude_dir: Set[str]
    exclude_path_contains: List[str]
    include_files: Set[str]
    max_file_bytes: int
    chunk_tokens: int
    chunk_overlap: int


def load_filters(path: str) -> Filters:
    """Load filter configuration from YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    return Filters(
        include_ext=set(e.lower() for e in cfg.get('include_ext', [])),
        exclude_dir=set(cfg.get('exclude_dir', [])),
        exclude_path_contains=cfg.get('exclude_path_contains', []),
        include_files=set(cfg.get('include_files', [])),
        max_file_bytes=int(cfg.get('max_file_bytes', 800000)),
        chunk_tokens=int(cfg.get('chunk_tokens', 650)),
        chunk_overlap=int(cfg.get('chunk_overlap', 80)),
    )


# =============================================================================
# Utilities
# =============================================================================

def sha256_bytes(b: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(b).hexdigest()


def guess_lang(file_path: str) -> str:
    """Guess language from file extension."""
    ext = pathlib.Path(file_path).suffix.lower()
    name = pathlib.Path(file_path).name.lower()

    # Special cases
    if name == 'dockerfile':
        return 'dockerfile'
    if name == 'makefile':
        return 'makefile'

    lang_map = {
        '.py': 'python',
        '.pyi': 'python',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.mjs': 'javascript',
        '.md': 'markdown',
        '.mdx': 'mdx',
        '.rst': 'rst',
        '.sql': 'sql',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.toml': 'toml',
        '.go': 'go',
        '.java': 'java',
        '.kt': 'kotlin',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.sh': 'shell',
        '.bash': 'shell',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.txt': 'text',
    }
    return lang_map.get(ext, ext.replace('.', '') or 'text')


def should_skip(path_rel: str, filt: Filters) -> bool:
    """Check if a file should be skipped based on filters."""
    p = pathlib.Path(path_rel)

    # Check if it's a special include file
    if p.name in filt.include_files:
        return False

    # Check directory exclusions
    parts = p.parts
    if any(part in filt.exclude_dir for part in parts):
        return True

    # Check path substring exclusions
    if any(x in path_rel for x in filt.exclude_path_contains):
        return True

    # Check extension
    ext = p.suffix.lower()
    if p.name.lower() == 'dockerfile':
        return False

    return ext not in filt.include_ext


def normalize_text(s: str) -> str:
    """Normalize text content."""
    # Normalize line endings
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse excessive blank lines
    s = re.sub(r'\n{4,}', '\n\n\n', s)
    return s.strip()


def chunk_by_tokens(
    text: str,
    enc: tiktoken.Encoding,
    size: int,
    overlap: int
) -> List[Tuple[int, str]]:
    """Chunk text by token count with overlap."""
    tokens = enc.encode(text)
    if not tokens:
        return []

    chunks = []
    start = 0
    idx = 0

    while start < len(tokens):
        end = min(start + size, len(tokens))
        chunk_text = enc.decode(tokens[start:end])
        chunks.append((idx, chunk_text))
        idx += 1

        if end == len(tokens):
            break

        start = max(0, end - overlap)

    return chunks


# =============================================================================
# Embeddings
# =============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def embed_texts_openai(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using OpenAI API.

    Expects:
        OPENAI_API_KEY
        OPENAI_EMBEDDING_MODEL (optional, defaults to text-embedding-3-small)
    """
    api_key = os.environ['OPENAI_API_KEY']
    model = os.environ.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    url = 'https://api.openai.com/v1/embeddings'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    embeddings: List[List[float]] = []
    batch_size = int(os.environ.get('EMBED_BATCH_SIZE', '64'))

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        # Truncate texts if too long (max ~8k tokens for embedding model)
        batch = [t[:32000] for t in batch]

        response = requests.post(
            url,
            headers=headers,
            json={'model': model, 'input': batch},
            timeout=120
        )
        response.raise_for_status()

        data = response.json()['data']
        embeddings.extend([d['embedding'] for d in data])

    return embeddings


# =============================================================================
# Supabase Operations
# =============================================================================

def upsert_doc(sb: Client, doc: Dict) -> int:
    """Insert or update a document and return its ID."""
    # Upsert the document
    sb.table('knowledge_docs').upsert(
        doc,
        on_conflict='repo,ref,path,sha'
    ).execute()

    # Fetch the ID
    result = sb.table('knowledge_docs').select('id').eq(
        'repo', doc['repo']
    ).eq(
        'ref', doc['ref']
    ).eq(
        'path', doc['path']
    ).eq(
        'sha', doc['sha']
    ).limit(1).execute()

    return result.data[0]['id']


def upsert_chunks(sb: Client, rows: List[Dict]):
    """Upsert chunk rows."""
    if not rows:
        return

    # Upsert in batches
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        sb.table('knowledge_chunks').upsert(
            batch,
            on_conflict='doc_id,chunk_index'
        ).execute()


def delete_old_chunks(sb: Client, doc_id: int, max_chunk_index: int):
    """Delete chunks beyond the current max index (for file updates)."""
    sb.table('knowledge_chunks').delete().eq(
        'doc_id', doc_id
    ).gt(
        'chunk_index', max_chunk_index
    ).execute()


# =============================================================================
# Repository Operations
# =============================================================================

def clone_repo(repo_url: str, ref: str, workdir: str) -> str:
    """Clone a repository to a temporary directory."""
    # Create a safe local path
    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', repo_url)
    local_path = os.path.join(workdir, safe_name)

    # Remove if exists
    if os.path.exists(local_path):
        shutil.rmtree(local_path)

    logger.info(f'Cloning {repo_url} @ {ref}...')
    repo = Repo.clone_from(repo_url, local_path, depth=1)

    # Try to checkout specific ref
    try:
        repo.git.checkout(ref)
    except Exception:
        logger.warning(f'Could not checkout {ref}, using default branch')

    return local_path


def detect_license(repo_root: str) -> Optional[str]:
    """Detect license file in repository."""
    for name in ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING']:
        path = os.path.join(repo_root, name)
        if os.path.exists(path):
            return name
    return None


def iter_files(repo_root: str, filt: Filters):
    """Iterate over files in repository that pass filters."""
    root = pathlib.Path(repo_root)

    for path in root.rglob('*'):
        if path.is_dir():
            continue

        rel = str(path.relative_to(root)).replace('\\', '/')

        if should_skip(rel, filt):
            continue

        try:
            size = path.stat().st_size
        except Exception:
            continue

        if size > filt.max_file_bytes:
            continue

        yield rel, str(path), size


# =============================================================================
# Main Ingestion
# =============================================================================

def ingest_repo(
    sb: Client,
    enc: tiktoken.Encoding,
    repo_name: str,
    repo_url: str,
    ref: str,
    repo_root: str,
    filt: Filters
) -> Dict:
    """Ingest a single repository."""
    license_file = detect_license(repo_root)
    stats = {'files': 0, 'chunks': 0, 'tokens': 0}

    files = list(iter_files(repo_root, filt))
    logger.info(f'Processing {len(files)} files from {repo_name}')

    for rel, abspath, size in tqdm(files, desc=repo_name, unit='file'):
        try:
            raw = open(abspath, 'rb').read()
        except Exception as e:
            logger.warning(f'Could not read {rel}: {e}')
            continue

        sha = sha256_bytes(raw)

        try:
            text = raw.decode('utf-8', errors='replace')
        except Exception:
            continue

        text = normalize_text(text)
        if not text:
            continue

        lang = guess_lang(rel)
        url = repo_url.rstrip('.git') + f'/blob/{ref}/{rel}'

        # Upsert document
        doc = {
            'repo': repo_name,
            'ref': ref,
            'path': rel,
            'sha': sha,
            'url': url,
            'license': license_file,
            'lang': lang,
            'bytes': size,
        }
        doc_id = upsert_doc(sb, doc)

        # Chunk the content
        chunks = chunk_by_tokens(text, enc, filt.chunk_tokens, filt.chunk_overlap)
        if not chunks:
            continue

        # Generate embeddings
        contents = [c for _, c in chunks]
        try:
            embeddings = embed_texts_openai(contents)
        except Exception as e:
            logger.error(f'Embedding failed for {rel}: {e}')
            continue

        # Prepare chunk rows
        rows = []
        for (idx, content), embedding in zip(chunks, embeddings):
            token_count = len(enc.encode(content))
            rows.append({
                'doc_id': doc_id,
                'chunk_index': idx,
                'content': content,
                'content_tokens': token_count,
                'embedding': embedding,
                'meta': {
                    'repo': repo_name,
                    'ref': ref,
                    'path': rel,
                    'lang': lang,
                    'url': url,
                },
            })
            stats['tokens'] += token_count

        # Upsert chunks
        upsert_chunks(sb, rows)
        stats['chunks'] += len(rows)

        # Clean up old chunks if file was updated
        if chunks:
            max_idx = max(idx for idx, _ in chunks)
            delete_old_chunks(sb, doc_id, max_idx)

        stats['files'] += 1

    return stats


def main():
    """Main entry point."""
    # Load configuration
    supabase_url = os.environ['SUPABASE_URL']
    supabase_key = os.environ['SUPABASE_SERVICE_ROLE_KEY']

    # Load repos from environment or config
    repos_json = os.environ.get('REPOS_JSON')
    if repos_json:
        repos = json.loads(repos_json)
    else:
        # Load from filters.yaml
        filters_path = os.environ.get(
            'FILTERS_YAML',
            'tools/knowledge/filters.yaml'
        )
        with open(filters_path, 'r') as f:
            cfg = yaml.safe_load(f)
        repos = cfg.get('default_repos', [])

    if not repos:
        raise SystemExit('No repositories configured. Set REPOS_JSON or add default_repos to filters.yaml')

    logger.info(f'Will process {len(repos)} repositories')

    # Load filters
    filters_path = os.environ.get('FILTERS_YAML', 'tools/knowledge/filters.yaml')
    filt = load_filters(filters_path)

    # Initialize clients
    sb = create_client(supabase_url, supabase_key)
    enc = tiktoken.get_encoding('cl100k_base')

    # Process each repository
    total_stats = {'files': 0, 'chunks': 0, 'tokens': 0}

    with tempfile.TemporaryDirectory() as workdir:
        for item in repos:
            repo_name = item['repo']
            repo_url = item['url']
            ref = item.get('ref', 'main')

            try:
                repo_root = clone_repo(repo_url, ref, workdir)
                stats = ingest_repo(
                    sb, enc, repo_name, repo_url, ref, repo_root, filt
                )

                total_stats['files'] += stats['files']
                total_stats['chunks'] += stats['chunks']
                total_stats['tokens'] += stats['tokens']

                logger.info(
                    f'[OK] {repo_name}: {stats["files"]} files, '
                    f'{stats["chunks"]} chunks, {stats["tokens"]:,} tokens'
                )

            except Exception as e:
                logger.error(f'[FAIL] {repo_name}: {e}')
                continue

    # Summary
    logger.info('=' * 60)
    logger.info('INGESTION COMPLETE')
    logger.info(f'Total files:  {total_stats["files"]}')
    logger.info(f'Total chunks: {total_stats["chunks"]}')
    logger.info(f'Total tokens: {total_stats["tokens"]:,}')
    logger.info('=' * 60)


if __name__ == '__main__':
    main()
