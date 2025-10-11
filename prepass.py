#!/usr/bin/env python3
"""
Prepass Detector for TTS-Proof
Scans Markdown files to identify words/patterns likely to break TTS.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import requests

# Import from md_proof for LLM communication and chunking
from md_proof import call_lmstudio, chunk_paragraphs, mask_urls, unmask_urls, Spinner

DETECTOR_PROMPT = """You are a TTS preprocessing detector. Find problematic patterns and suggest specific replacements.

Analyze the text and return JSON with problem words AND their recommended TTS-friendly replacements:
- Stylized/spaced letters: "F ʟ ᴀ s ʜ" → "Flash"
- Hyphenated letters: "U-N-I-T-E-D" → "United" 
- ALL-CAPS titles: "REALLY LONG TITLE" → "Really Long Title"
- Underscore caps: "WEIRD_CAPS_THING" → "Weird Caps Thing"
- Bracket stylized: "[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip valid acronyms (NASA, GPU, API, etc.) and preserve code blocks.

Return JSON only:
{ "replacements": [ { "find": "<exact_text>", "replace": "<tts_friendly_version>", "reason": "<why>" } ] }"""

def detect_tts_problems(api_base: str, model: str, text: str, show_spinner: bool = False) -> List[Dict[str, str]]:
    """
    Call LLM with detector prompt to find TTS problems and get replacement suggestions.
    
    Args:
        api_base: LLM API base URL
        model: Model name
        text: Text chunk to analyze
        show_spinner: Whether to show spinner during processing
        
    Returns:
        List of replacement dictionaries with 'find', 'replace', and 'reason' keys
    """
    masked_text, urls = mask_urls(text)
    
    sp = Spinner("Detecting TTS problems") if show_spinner else None
    if sp:
        sp.start()
        
    try:
        response = call_lmstudio(api_base, model, DETECTOR_PROMPT, masked_text)
        
        # Parse JSON response
        try:
            # Extract JSON from response if it contains extra text
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                replacements = data.get('replacements', [])
                
                # Unmask any URLs that might be in find/replace strings
                for replacement in replacements:
                    if 'find' in replacement:
                        replacement['find'] = unmask_urls(replacement['find'], urls)
                    if 'replace' in replacement:
                        replacement['replace'] = unmask_urls(replacement['replace'], urls)
                
                return replacements
            else:
                return []
        except json.JSONDecodeError:
            print(f"Warning: Could not parse LLM response as JSON: {response[:100]}...")
            return []
            
    finally:
        if sp:
            sp.stop(clear_line=True)


def run_prepass(input_path: Path, api_base: str, model: str, chunk_chars: int = 8000, 
                show_progress: bool = True) -> Dict[str, Any]:
    """
    Run prepass detection on a Markdown file.
    
    Args:
        input_path: Path to input Markdown file
        api_base: LLM API base URL
        model: Model name
        chunk_chars: Characters per chunk
        show_progress: Whether to show progress
        
    Returns:
        Prepass report dictionary
    """
    # Load and chunk the file
    markdown_text = input_path.read_text(encoding="utf-8")
    chunks = chunk_paragraphs(markdown_text, chunk_chars)
    
    # Filter to text chunks only (skip code blocks)
    text_chunks = [(i, content) for i, (kind, content) in enumerate(chunks) if kind == "text"]
    
    if show_progress:
        print(f"Processing {len(text_chunks)} text chunks for TTS problem detection...")
    
    # Process each chunk
    report_chunks = []
    all_problems = []
    current_byte = 0
    
    for chunk_idx, (original_idx, content) in enumerate(text_chunks):
        if show_progress:
            print(f"Chunk {chunk_idx + 1}/{len(text_chunks)}", end=" ", flush=True)
            
        # Find byte range (approximate)
        start_byte = current_byte
        end_byte = current_byte + len(content.encode('utf-8'))
        current_byte = end_byte
        
        # Detect problems in this chunk
        replacements = detect_tts_problems(api_base, model, content, show_spinner=show_progress)
        
        # Add to report
        chunk_report = {
            "id": chunk_idx + 1,
            "range": {
                "start_byte": start_byte,
                "end_byte": end_byte
            },
            "replacements": replacements
        }
        report_chunks.append(chunk_report)
        
        # Collect all find words for summary
        for replacement in replacements:
            if replacement.get('find'):
                all_problems.append(replacement['find'])
    
    # Create summary with deduplicated problems and collect all replacements
    unique_problems = list(dict.fromkeys(all_problems))  # Preserves order while removing duplicates
    
    # Collect all replacement mappings for grammar pass
    all_replacements = {}
    for chunk in report_chunks:
        for replacement in chunk['replacements']:
            find_text = replacement.get('find')
            replace_text = replacement.get('replace')
            if find_text and replace_text:
                all_replacements[find_text] = replace_text
    
    # Build final report
    report = {
        "source": str(input_path.name),
        "created_at": datetime.now().isoformat(),
        "chunks": report_chunks,
        "summary": {
            "unique_problem_words": unique_problems,
            "replacement_map": all_replacements
        }
    }
    
    if show_progress:
        print(f"\nFound {len(unique_problems)} unique problem words across {len(text_chunks)} chunks")
    
    return report


def write_prepass_report(report: Dict[str, Any], output_path: Path):
    """Write prepass report to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def load_prepass_report(report_path: Path) -> Dict[str, Any]:
    """Load prepass report from JSON file."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_replacement_map_for_grammar(report: Dict[str, Any], max_replacements: int = 100) -> Dict[str, str]:
    """
    Extract replacement map from prepass report for grammar pass injection.
    
    Args:
        report: Prepass report dictionary
        max_replacements: Maximum number of replacements to return
        
    Returns:
        Dictionary mapping problem text to TTS-friendly replacements
    """
    replacement_map = report.get('summary', {}).get('replacement_map', {})
    # Limit to max_replacements
    limited_map = dict(list(replacement_map.items())[:max_replacements])
    return limited_map


def get_problem_words_for_grammar(report: Dict[str, Any], max_words: int = 200) -> List[str]:
    """
    Legacy function: Extract unique problem words from prepass report for grammar pass injection.
    
    Args:
        report: Prepass report dictionary
        max_words: Maximum number of words to return
        
    Returns:
        List of problem words, deduplicated and trimmed to max_words
    """
    unique_words = report.get('summary', {}).get('unique_problem_words', [])
    return unique_words[:max_words]


def inject_prepass_into_grammar_prompt(base_prompt: str, replacement_map: Dict[str, str]) -> str:
    """
    Inject prepass replacement instructions into grammar prompt.
    
    Args:
        base_prompt: Original grammar prompt
        replacement_map: Dictionary mapping problem text to TTS-friendly replacements
        
    Returns:
        Modified prompt with specific replacement instructions
    """
    if not replacement_map:
        return base_prompt
        
    # Limit number of replacements to prevent prompt overflow
    limited_replacements = dict(list(replacement_map.items())[:100])
    
    # Format as specific replacement instructions
    replacement_lines = []
    for find_text, replace_text in limited_replacements.items():
        replacement_lines.append(f'"{find_text}" → "{replace_text}"')
    
    replacement_instructions = "\n".join(replacement_lines)
    
    injection = f"""

PREPASS REPLACEMENTS: Apply these specific TTS-friendly substitutions exactly as shown:
{replacement_instructions}

These replacements were pre-identified by TTS analysis. Apply them precisely while preserving all Markdown structure."""
    
    return base_prompt + injection


def inject_prepass_into_grammar_prompt_legacy(base_prompt: str, problem_words: List[str]) -> str:
    """
    Legacy function for backward compatibility with old problem word lists.
    """
    if not problem_words:
        return base_prompt
        
    # Convert to replacement map format (without specific replacements)
    word_list = ", ".join(problem_words[:200])
    
    injection = f"""

PRIORITY: Pay special attention to these TTS problem patterns and normalize them:
{word_list}

Guidelines for these problems:
- Spaced/stylized letters: Convert to normal words (e.g., "F ʟ ᴀ s ʜ" → "Flash")
- ALL-CAPS titles: Use title case unless it's a known acronym
- Hyphenated letters: Remove hyphens and normalize case (e.g., "U-N-I-T-E-D" → "United")
- Underscore_caps: Convert to normal words with proper spacing
Keep all Markdown structure intact."""
    
    return base_prompt + injection