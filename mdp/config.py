import yaml
from typing import Dict, Any

DEFAULT_CONFIG = {
    'unicode_form': 'NFKC',
    'normalize_punctuation': True,
    'quotes_policy': 'straight',  # 'straight' or 'curly'
    'dashes_policy': 'em',      # 'em', 'en', or 'hyphen'
    'nbsp_handling': 'space',     # 'space' or 'keep'
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