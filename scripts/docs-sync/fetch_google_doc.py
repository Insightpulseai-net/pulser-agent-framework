#!/usr/bin/env python3
"""
Google Docs to GitHub Sync - Document Fetcher

This script fetches a Google Doc and exports it to HTML for conversion to Markdown.
Used by the GitHub Actions workflow for automated documentation sync.

Usage:
    python fetch_google_doc.py

Environment Variables:
    GOOGLE_CREDENTIALS: JSON string of service account credentials
    DOCUMENT_ID: Google Doc document ID to fetch

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Required packages not installed. Run:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# Scopes required for Google Docs/Drive API
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_credentials():
    """Load Google Service Account credentials from environment."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not set")

    try:
        creds_dict = json.loads(creds_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in GOOGLE_CREDENTIALS: {e}")

    return service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )


def fetch_document_metadata(docs_service, doc_id: str) -> dict:
    """Fetch document metadata from Google Docs API."""
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        return {
            "title": doc.get("title", "Untitled"),
            "revision_id": doc.get("revisionId", "unknown"),
            "document_id": doc_id,
        }
    except HttpError as e:
        raise RuntimeError(f"Failed to fetch document metadata: {e}")


def export_as_html(drive_service, doc_id: str) -> bytes:
    """Export Google Doc as HTML using Drive API."""
    try:
        response = drive_service.files().export(
            fileId=doc_id, mimeType="text/html"
        ).execute()
        return response
    except HttpError as e:
        raise RuntimeError(f"Failed to export document as HTML: {e}")


def convert_html_to_markdown(html_content: bytes, metadata: dict) -> str:
    """Convert HTML content to Markdown with frontmatter."""
    # Basic HTML to Markdown conversion
    # For production, consider using pandoc or html2text
    content = html_content.decode("utf-8")

    # Remove HTML tags (basic conversion)
    # Strip style and script tags
    content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
    content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)

    # Convert common HTML elements to Markdown
    conversions = [
        (r"<h1[^>]*>(.*?)</h1>", r"# \1\n"),
        (r"<h2[^>]*>(.*?)</h2>", r"## \1\n"),
        (r"<h3[^>]*>(.*?)</h3>", r"### \1\n"),
        (r"<h4[^>]*>(.*?)</h4>", r"#### \1\n"),
        (r"<h5[^>]*>(.*?)</h5>", r"##### \1\n"),
        (r"<h6[^>]*>(.*?)</h6>", r"###### \1\n"),
        (r"<strong[^>]*>(.*?)</strong>", r"**\1**"),
        (r"<b[^>]*>(.*?)</b>", r"**\1**"),
        (r"<em[^>]*>(.*?)</em>", r"*\1*"),
        (r"<i[^>]*>(.*?)</i>", r"*\1*"),
        (r"<code[^>]*>(.*?)</code>", r"`\1`"),
        (r"<br\s*/?>", "\n"),
        (r"<p[^>]*>(.*?)</p>", r"\1\n\n"),
        (r"<li[^>]*>(.*?)</li>", r"- \1\n"),
        (r"<ul[^>]*>", ""),
        (r"</ul>", "\n"),
        (r"<ol[^>]*>", ""),
        (r"</ol>", "\n"),
        (r"<a[^>]*href=[\"']([^\"']*)[\"'][^>]*>(.*?)</a>", r"[\2](\1)"),
        (r"<[^>]+>", ""),  # Remove remaining tags
        (r"&nbsp;", " "),
        (r"&amp;", "&"),
        (r"&lt;", "<"),
        (r"&gt;", ">"),
        (r"&quot;", '"'),
        (r"\n{3,}", "\n\n"),  # Normalize multiple newlines
    ]

    for pattern, replacement in conversions:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)

    # Clean up whitespace
    content = content.strip()

    # Add frontmatter
    timestamp = datetime.utcnow().isoformat() + "Z"
    frontmatter = f"""---
title: "{metadata['title']}"
document_id: "{metadata['document_id']}"
revision_id: "{metadata['revision_id']}"
synced_at: "{timestamp}"
source: "Google Docs"
---

"""

    # Add footer
    footer = f"""

---

*This document was automatically synced from Google Docs on {timestamp}*
*Document ID: {metadata['document_id']}*
"""

    return frontmatter + content + footer


def main():
    """Main entry point for the script."""
    # Get configuration from environment
    doc_id = os.environ.get("DOCUMENT_ID")
    if not doc_id:
        print("Error: DOCUMENT_ID environment variable not set")
        sys.exit(1)

    output_dir = Path(os.environ.get("OUTPUT_DIR", "output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching document: {doc_id}")

    try:
        # Get credentials
        creds = get_credentials()

        # Build API clients
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        # Fetch document metadata
        metadata = fetch_document_metadata(docs_service, doc_id)
        print(f"Document title: {metadata['title']}")

        # Export as HTML
        html_content = export_as_html(drive_service, doc_id)

        # Save HTML
        html_path = output_dir / "document.html"
        with open(html_path, "wb") as f:
            f.write(html_content)
        print(f"HTML saved to: {html_path}")

        # Convert to Markdown
        markdown_content = convert_html_to_markdown(html_content, metadata)

        # Save Markdown
        md_path = output_dir / "document.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Markdown saved to: {md_path}")

        # Save metadata
        metadata["synced_at"] = datetime.utcnow().isoformat() + "Z"
        meta_path = output_dir / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_path}")

        # Set GitHub Actions outputs
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"title={metadata['title']}\n")
                f.write(f"revision_id={metadata['revision_id']}\n")
                f.write(f"timestamp={metadata['synced_at']}\n")

        print("Document fetch complete!")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
