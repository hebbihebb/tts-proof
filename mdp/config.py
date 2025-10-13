import yaml
from typing import Dict, Any

DEFAULT_CONFIG = {
    'unicode_form': 'NFKC',
    'normalize_punctuation': True,
    'quotes_policy': 'straight',  # 'straight' or 'curly'
    'dashes_policy': 'em',      # 'em', 'en', or 'hyphen'
    'nbsp_handling': 'space',     # 'space' or 'keep'
    'scrubber': {
        'enabled': True,
        'move_to_appendix': True,
        'edge_block_window': 6,
        'link_density_threshold': 0.50,
        'min_chars_to_strip': 12,
        'categories': {
            'authors_notes': True,
            'translators_notes': False,
            'editors_notes': True,
            'navigation': True,
            'promos_ads_social': True,
            'link_farms': True,
        },
        'whitelist': {
            'headings_keep': ["Translator's Cultural Notes"],
            'domains_keep': ["yourblog.is", "project-notes.local"],
        },
        'keywords': {
            'promos': ["patreon", "ko-fi", "buy me a coffee", "discord", "reddit", "substack"],
            'navigation': ["previous chapter", "next chapter", "table of contents", "back to top"],
            'watermarks': ["read on", "original at", "source on"],
        },
    },
    'prepass_advanced': {
        'enabled': True,
        'casing': {
            'normalize_shouting': True,
            'shouting_min_len': 4,
            'acronym_whitelist': ["NASA", "GPU", "JSON", "HTML", "TTS", "API", "URL", "HTTP", "HTTPS", "CSS", "SQL"],
            'titlecase_headings': False,
            'protected_lexicon': ["Aaahahaha", "BLUH", "Reykjavík", "Þór", "AAAAAA"],
        },
        'punctuation': {
            'collapse_runs': True,
            'runs_policy': 'first-of-each',  # "first-only" | "first-of-each"
            'ellipsis': 'three-dots',        # "three-dots" | "unicode"
            'quotes': 'straight',            # "straight" | "curly"
            'apostrophe': 'straight',        # "straight" | "curly"
            'space_after_sentence': 'single', # "single" | "double"
        },
        'numbers_units': {
            'join_percent': True,
            'space_before_unit': 'normal',   # "normal" | "nbsp" | "none"
            'time_style': 'p.m.',            # "p.m." | "PM" | "pm"
            'locale': 'en',
        },
        'footnotes': {
            'remove_inline_markers': False,
        },
    },
    'grammar_assist': {
        'enabled': True,
        'language': 'en',
        'safe_categories': ['TYPOS', 'PUNCTUATION', 'CASING', 'SPACING', 'SIMPLE_AGREEMENT'],
        'interactive': False,  # Always non-interactive (auto-apply)
    },
    'detector': {
        'enabled': True,
        'api_base': 'http://192.168.8.104:1234/v1',  # Network LM Studio server
        'model': 'qwen2.5-1.5b-instruct',  # Qwen/Qwen2.5-1.5B-Instruct-GGUF Q4_K_M
        'max_context_tokens': 1024,
        'max_output_chars': 2000,
        'timeout_s': 8,
        'retries': 1,
        'temperature': 0.2,
        'top_p': 0.9,
        'json_max_items': 16,
        'max_reason_chars': 64,
        'allow_categories': ['TTS_SPACED', 'UNICODE_STYLIZED', 'CASE_GLITCH', 'SIMPLE_PUNCT'],
        'block_categories': ['STYLE', 'REWRITE', 'MEANING_CHANGE'],
        'locale': 'en',
        # Chunking parameters
        'max_chunk_size': 600,
        'overlap_size': 50,
        'max_non_alpha_ratio': 0.5,
    },
    'apply': {
        'enabled': True,
        'max_file_growth_ratio': 0.01,  # 1% cap on total file growth
        'enforce_backtick_parity': True,
        'enforce_bracket_parity': True,
        'enforce_fence_parity': True,
        'forbid_new_markdown_tokens': True,
        'dry_run': False,
    },
    'fixer': {
        'enabled': True,
        'model': 'qwen2.5-1.5b-instruct',
        'api_base': 'http://127.0.0.1:1234/v1',
        'max_context_tokens': 1024,
        'max_output_tokens': 256,
        'timeout_s': 10,
        'retries': 1,
        'temperature': 0.2,
        'top_p': 0.9,
        'node_max_growth_ratio': 0.20,   # 20% per node
        'file_max_growth_ratio': 0.05,   # 5% per file
        'forbid_markdown_tokens': True,
        'locale': 'en',
        'batch_size': 1,
        'seed': 7,
    },
}

def load_config(path: str = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file, providing default values.
    """
    if path:
        with open(path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
        config = {**DEFAULT_CONFIG, **user_config}
    else:
        config = DEFAULT_CONFIG
    return config


def get_blessed_models() -> Dict[str, list[str]]:
    """
    Returns blessed model lists for detector and fixer roles.
    
    MVP Phase 11 focuses on Qwen2.5-1.5B-Instruct for both roles.
    These models have been tested and validated for the pipeline.
    
    Returns:
        Dictionary with 'detector' and 'fixer' keys, each containing
        a list of validated model names.
        
    Example:
        >>> models = get_blessed_models()
        >>> models['detector']
        ['qwen2.5-1.5b-instruct']
        >>> models['fixer']
        ['qwen2.5-1.5b-instruct']
    """
    return {
        'detector': ['qwen2.5-1.5b-instruct'],
        'fixer': ['qwen2.5-1.5b-instruct']
    }