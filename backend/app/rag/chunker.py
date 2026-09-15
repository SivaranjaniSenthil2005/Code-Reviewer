"""Markdown and section-based document chunker."""

import re
from dataclasses import dataclass
from typing import List
from app.rag.loaders import KnowledgeDocument


@dataclass
class DocumentChunk:
    """A single chunk of a knowledge document."""
    chunk_id: str
    doc_id: str
    title: str
    category: str
    language: str
    heading: str
    content: str


def chunk_document(doc: KnowledgeDocument) -> List[DocumentChunk]:
    """Split a knowledge document into chunks based on markdown section headers (##)."""
    lines = doc.content.strip().split("\n")
    chunks: List[DocumentChunk] = []

    current_heading = doc.title
    current_lines: List[str] = []
    chunk_index = 0

    for line in lines:
        if line.startswith("## ") or line.startswith("# "):
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc.doc_id}-chunk-{chunk_index}",
                        doc_id=doc.doc_id,
                        title=doc.title,
                        category=doc.category,
                        language=doc.language,
                        heading=current_heading,
                        content=chunk_text,
                    ))
                    chunk_index += 1
                current_lines = []
            current_heading = line.lstrip("#").strip()
        current_lines.append(line)

    # Flush final chunk
    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append(DocumentChunk(
                chunk_id=f"{doc.doc_id}-chunk-{chunk_index}",
                doc_id=doc.doc_id,
                title=doc.title,
                category=doc.category,
                language=doc.language,
                heading=current_heading,
                content=chunk_text,
            ))

    return chunks


def chunk_all_documents(docs: List[KnowledgeDocument]) -> List[DocumentChunk]:
    """Chunk all loaded documents."""
    all_chunks: List[DocumentChunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks
