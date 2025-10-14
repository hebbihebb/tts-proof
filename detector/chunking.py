#!/usr/bin/env python3
"""
detector/chunking.py - Node Chunking Policy

Splits long text nodes into overlapping spans for detector processing.
"""

import re
from typing import List, Tuple, Dict, Any


def split_into_sentences(text: str) -> List[str]:
    """
    Simple sentence splitter on .?! while preserving delimiters.
    
    Args:
        text: Input text
    
    Returns:
        List of sentences (including trailing punctuation)
    """
    # Split on sentence boundaries but keep the delimiter
    sentences = re.split(r'([.!?]+\s*)', text)
    
    # Recombine sentences with their punctuation
    result = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        punct = sentences[i + 1] if i + 1 < len(sentences) else ''
        combined = sentence + punct
        if combined.strip():
            result.append(combined)
    
    # Handle last sentence if no trailing punctuation
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1])
    
    return result


def chunk_text_node(node_text: str, config: Dict[str, Any]) -> List[Tuple[str, int, int]]:
    """
    Chunk a text node into overlapping spans.
    
    Args:
        node_text: Text content of a single node
        config: Configuration dict with chunking parameters
    
    Returns:
        List of (span_text, start_offset, end_offset) tuples
    """
    max_chunk_size = config.get('max_chunk_size', 600)
    overlap_size = config.get('overlap_size', 50)
    
    # Short node - return as single chunk
    if len(node_text) <= max_chunk_size:
        return [(node_text, 0, len(node_text))]
    
    # Split into sentences
    sentences = split_into_sentences(node_text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    current_offset = 0
    
    for sentence in sentences:
        sentence_len = len(sentence)
        
        # If adding this sentence would exceed max size, finalize current chunk
        if current_length + sentence_len > max_chunk_size and current_chunk:
            # Finalize current chunk
            chunk_text = ''.join(current_chunk)
            chunks.append((chunk_text, current_offset, current_offset + len(chunk_text)))
            
            # Start new chunk with overlap
            # Find sentences to include in overlap
            overlap_text = ''
            overlap_sentences = []
            for s in reversed(current_chunk):
                if len(overlap_text) + len(s) <= overlap_size:
                    overlap_sentences.insert(0, s)
                    overlap_text = ''.join(overlap_sentences)
                else:
                    break
            
            # Update offset and start new chunk
            current_offset += len(chunk_text) - len(overlap_text)
            current_chunk = overlap_sentences + [sentence]
            current_length = len(overlap_text) + sentence_len
        else:
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_len
    
    # Add final chunk if any
    if current_chunk:
        chunk_text = ''.join(current_chunk)
        chunks.append((chunk_text, current_offset, current_offset + len(chunk_text)))
    
    return chunks


def should_skip_node(node_text: str, config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Pre-flight check: decide if a node should be skipped.
    
    Args:
        node_text: Text content
        config: Configuration dict
    
    Returns:
        Tuple of (should_skip, reason)
    """
    # Skip empty or whitespace-only
    if not node_text or not node_text.strip():
        return True, "empty"
    
    # Skip if looks like a URL
    if re.match(r'^https?://', node_text) or '//' in node_text:
        return True, "url"
    
    # Allow uppercase-heavy or symbol-heavy spans through; the downstream validator will reject bad plans.
    
    return False, ""
