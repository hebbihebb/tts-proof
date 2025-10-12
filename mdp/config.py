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