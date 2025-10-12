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