#!/usr/bin/env python3
"""
Unit tests for mdp/config.py - Configuration and blessed models
"""

import pytest
from mdp.config import load_config, get_blessed_models, DEFAULT_CONFIG


class TestGetBlessedModels:
    """Tests for blessed model lists."""
    
    def test_returns_dict_with_correct_keys(self):
        """Should return dict with 'detector' and 'fixer' keys."""
        models = get_blessed_models()
        assert isinstance(models, dict)
        assert 'detector' in models
        assert 'fixer' in models
    
    def test_detector_models_is_list(self):
        """Detector models should be a list."""
        models = get_blessed_models()
        assert isinstance(models['detector'], list)
        assert len(models['detector']) > 0
    
    def test_fixer_models_is_list(self):
        """Fixer models should be a list."""
        models = get_blessed_models()
        assert isinstance(models['fixer'], list)
        assert len(models['fixer']) > 0
    
    def test_contains_qwen_model(self):
        """Should contain qwen2.5-1.5b-instruct for both roles."""
        models = get_blessed_models()
        assert 'qwen2.5-1.5b-instruct' in models['detector']
        assert 'qwen2.5-1.5b-instruct' in models['fixer']
    
    def test_models_are_strings(self):
        """All model names should be strings."""
        models = get_blessed_models()
        for model in models['detector']:
            assert isinstance(model, str)
            assert len(model) > 0
        for model in models['fixer']:
            assert isinstance(model, str)
            assert len(model) > 0
    
    def test_no_duplicate_models(self):
        """Model lists should not contain duplicates."""
        models = get_blessed_models()
        assert len(models['detector']) == len(set(models['detector']))
        assert len(models['fixer']) == len(set(models['fixer']))
    
    def test_deterministic_output(self):
        """Multiple calls should return identical results."""
        models1 = get_blessed_models()
        models2 = get_blessed_models()
        assert models1 == models2


class TestLoadConfig:
    """Tests for config loading (existing functionality)."""
    
    def test_load_default_config(self):
        """Loading without path should return default config."""
        config = load_config()
        assert config == DEFAULT_CONFIG
    
    def test_default_config_has_required_keys(self):
        """Default config should have all required sections."""
        config = load_config()
        assert 'unicode_form' in config
        assert 'scrubber' in config
        assert 'prepass_advanced' in config
        assert 'grammar_assist' in config
        assert 'detector' in config
        assert 'apply' in config
        assert 'fixer' in config
    
    def test_detector_config_structure(self):
        """Detector config should have expected fields."""
        config = load_config()
        detector = config['detector']
        assert 'enabled' in detector
        assert 'model' in detector
        assert 'api_base' in detector
        assert 'max_context_tokens' in detector
    
    def test_fixer_config_structure(self):
        """Fixer config should have expected fields."""
        config = load_config()
        fixer = config['fixer']
        assert 'enabled' in fixer
        assert 'model' in fixer
        assert 'api_base' in fixer
        assert 'max_context_tokens' in fixer


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
