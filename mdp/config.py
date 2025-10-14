import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Dict, Any, Iterable, Optional

import yaml

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
        'model': 'qwen/qwen3-4b-2507',
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
    'max_file_growth_ratio': 0.05,  # 5% cap on total file growth to align with fixer budget
        'enforce_backtick_parity': True,
        'enforce_bracket_parity': True,
        'enforce_fence_parity': True,
        'forbid_new_markdown_tokens': True,
        'dry_run': False,
    },
    'fixer': {
        'enabled': True,
        'model': 'qwen/qwen3-4b-2507',
        'api_base': 'http://127.0.0.1:1234/v1',
        'max_context_tokens': 1024,
        'max_output_tokens': 256,
    'timeout_s': 30,
    'retries': 2,
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

CONFIG_ROOT = Path(__file__).resolve().parent.parent / "config"
PRESETS_PATH = CONFIG_ROOT / "presets.json"
ACRONYMS_PATH = CONFIG_ROOT / "acronyms.txt"
SETTINGS_PATH = Path.home() / ".mdp" / "settings.json"


def _deep_merge(base: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not overrides:
        return base
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: str = None) -> Dict[str, Any]:
    """Load configuration from YAML file if provided, otherwise return defaults."""
    config = deepcopy(DEFAULT_CONFIG)
    if path:
        with open(path, 'r', encoding='utf-8') as handle:
            user_config = yaml.safe_load(handle) or {}
        config = _deep_merge(config, user_config)
    return config


def get_blessed_models() -> Dict[str, list[str]]:
    """
    Returns blessed model lists for detector and fixer roles.
    
    Phase 11 blessed models include Qwen2.5 1.5B, Qwen3 4B, and Qwen3 8B
    for both detector and fixer. These models have been tested and validated
    for the pipeline.
    
    Returns:
        Dictionary with 'detector' and 'fixer' keys, each containing
        a list of validated model names.
        
    Example:
        >>> models = get_blessed_models()
        >>> models['detector']
        ['qwen2.5-1.5b-instruct', 'qwen3-4b-instruct-2507', 'qwen3-8b']
        >>> models['fixer']
        ['qwen2.5-1.5b-instruct', 'qwen3-4b-instruct-2507', 'qwen3-8b']
    """
    return {
        'detector': [
            'qwen/qwen3-4b-2507',
            'qwen/qwen3-8b-instruct',
            'qwen/qwen3-8b'
        ],
        'fixer': [
            'qwen/qwen3-4b-2507',
            'qwen/qwen3-8b-instruct',
            'qwen/qwen3-8b'
        ]
    }


def load_presets(path: Path = PRESETS_PATH) -> Dict[str, Any]:
    """Load preset definitions from JSON file."""
    if not path.exists():
        return {"default": {}}
    with open(path, 'r', encoding='utf-8') as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid presets file at {path}: {exc}") from exc
    if "default" not in data:
        data["default"] = {}
    return data


def compute_effective_presets(presets: Dict[str, Any]) -> Dict[str, Any]:
    """Return presets merged with default baseline for display purposes."""
    effective: Dict[str, Any] = {}
    default_values = deepcopy(presets.get("default", {}))
    for name, values in presets.items():
        combined = deepcopy(default_values)
        if name == "default":
            combined = deepcopy(values)
        else:
            combined = _deep_merge(combined, deepcopy(values))
        effective[name] = combined
    return effective


def load_settings(path: Path = SETTINGS_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(settings: Dict[str, Any], path: Path = SETTINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(settings, handle, indent=2)


def set_active_preset(name: str, presets: Optional[Dict[str, Any]] = None) -> None:
    presets = presets or load_presets()
    if name not in presets:
        raise ValueError(f"Preset '{name}' not found")
    settings = load_settings()
    settings['active_preset'] = name
    save_settings(settings)


def load_acronyms(path: Path = ACRONYMS_PATH) -> list[str]:
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as handle:
        return [line.strip() for line in handle if line.strip()]


def save_acronyms(items: Iterable[str], path: Path = ACRONYMS_PATH) -> list[str]:
    normalized = []
    seen = set()
    for item in items:
        token = item.strip().upper()
        if not token or token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, 'w', encoding='utf-8') as handle:
        handle.write("\n".join(normalized))
        if normalized:
            handle.write("\n")
    temp_path.replace(path)
    return normalized


def resolve_model_preset(
    presets: Optional[Dict[str, Any]] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    presets = presets or load_presets()
    env = env or os.environ
    settings = load_settings()

    env_choice = env.get('MDP_PRESET')
    active = None
    if env_choice and env_choice in presets:
        active = env_choice
        source = 'env'
    else:
        stored = settings.get('active_preset')
        if stored in presets:
            active = stored
            source = 'settings'
    if not active:
        active = 'default' if 'default' in presets else next(iter(presets))
        source = 'default'

    default_values = deepcopy(presets.get('default', {}))
    resolved = deepcopy(default_values)
    if active != 'default' and active in presets:
        resolved = _deep_merge(resolved, deepcopy(presets[active]))
    elif active == 'default':
        resolved = deepcopy(presets.get('default', {}))

    env_overrides: Dict[str, str] = {}
    grammar_base = env.get('MDP_GRAMMAR_BASE_URL')
    grammar_model = env.get('MDP_GRAMMAR_MODEL')
    fix_base = env.get('MDP_FIX_BASE_URL')
    fix_model = env.get('MDP_FIX_MODEL')

    if grammar_base:
        resolved.setdefault('grammar', {})['base_url'] = grammar_base
        env_overrides['MDP_GRAMMAR_BASE_URL'] = grammar_base
    if grammar_model:
        resolved.setdefault('grammar', {})['model'] = grammar_model
        env_overrides['MDP_GRAMMAR_MODEL'] = grammar_model
    if fix_base:
        resolved.setdefault('fixer', {})['base_url'] = fix_base
        env_overrides['MDP_FIX_BASE_URL'] = fix_base
    if fix_model:
        resolved.setdefault('fixer', {})['model'] = fix_model
        env_overrides['MDP_FIX_MODEL'] = fix_model

    return {
        'active': active,
        'active_source': source,
        'resolved': resolved,
        'env_overrides': env_overrides,
        'settings_path': str(SETTINGS_PATH),
    }


def apply_model_preset(
    config: Dict[str, Any],
    preset_info: Dict[str, Any],
    request_overrides: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    request_overrides = request_overrides or {}
    resolved = deepcopy(preset_info.get('resolved', {}))

    # Apply request overrides to resolved view first
    for stage, overrides in request_overrides.items():
        if overrides:
            resolved.setdefault(stage, {})
            resolved[stage].update(overrides)

    model_routing = {
        'active': preset_info.get('active'),
        'active_source': preset_info.get('active_source'),
        'resolved': resolved,
        'env_overrides': preset_info.get('env_overrides', {}),
        'request_overrides': request_overrides,
    }

    def _apply_stage(stage: str, mapping: Dict[str, Any]) -> None:
        config.setdefault(stage, {})
        stage_config = config[stage]
        if 'model' in mapping:
            stage_config['model'] = mapping['model']
        if 'base_url' in mapping:
            key = 'api_base' if stage != 'grammar_assist' else 'base_url'
            stage_config[key] = mapping['base_url']
        if 'api_base' in mapping:
            stage_config['api_base'] = mapping['api_base']
        for key in ('temperature', 'top_p', 'timeout_s', 'max_context_tokens', 'max_output_tokens', 'seed'):
            if key in mapping:
                stage_config[key] = mapping[key]

    if 'detector' in resolved:
        _apply_stage('detector', resolved['detector'])
    if 'fixer' in resolved:
        _apply_stage('fixer', resolved['fixer'])

    # Store routing metadata for downstream consumers
    config['model_routing'] = model_routing
    return config