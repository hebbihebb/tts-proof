#!/usr/bin/env python3
"""
Unit tests for mdp.grammar_assist module (Phase 5).

Tests cover:
- Deterministic behavior (running twice yields identical output)
- Structural validation (masks, links, backticks, brackets preserved)
- Safe category filtering
- Locale support
- Text-node scoping
"""

import pytest
from mdp.grammar_assist import (
    apply_grammar_corrections,
    _validate_structural_integrity,
    _map_languagetool_category,
    GrammarSuggestion,
)
from mdp.config import load_config
from mdp.markdown_adapter import mask_protected, unmask


class TestGrammarAssist:
    """Test suite for Phase 5 Grammar Assist."""
    
    def test_deterministic_behavior(self):
        """Running grammar assist twice on same input produces identical output."""
        config = load_config()
        
        text = "This is a tets document with some erors."
        
        # Apply twice
        result1, stats1 = apply_grammar_corrections(text, config)
        result2, stats2 = apply_grammar_corrections(text, config)
        
        # Should be identical
        assert result1 == result2, "Grammar assist should be deterministic"
        assert stats1 == stats2, "Stats should be identical"
    
    def test_structural_validation_masks(self):
        """Mask counts must remain unchanged after corrections."""
        original = "This is a test with __MASKED_0__ and __MASKED_1__ sentinels."
        corrected = "This is a test with __MASKED_0__ and __MASKED_1__ sentinels."
        
        mask_table = {
            '__MASKED_0__': '[link](url)',
            '__MASKED_1__': '`code`'
        }
        
        is_valid, error = _validate_structural_integrity(original, corrected, mask_table)
        assert is_valid, f"Valid correction should pass: {error}"
        
        # Now test invalid case (mask removed)
        corrupted = "This is a test with __MASKED_0__ sentinels."
        is_valid, error = _validate_structural_integrity(original, corrupted, mask_table)
        assert not is_valid, "Should detect missing mask"
        assert '__MASKED_1__' in error, "Error should mention missing mask"
    
    def test_structural_validation_links(self):
        """Link bracket parity must be preserved."""
        original = "Check [this link](url) and [another](url2)."
        corrected = "Check [this link](url) and [another](url2)."
        
        is_valid, error = _validate_structural_integrity(original, corrected)
        assert is_valid, f"Valid correction should pass: {error}"
        
        # Broken bracket parity
        corrupted = "Check this link](url) and [another](url2)."
        is_valid, error = _validate_structural_integrity(original, corrupted)
        assert not is_valid, "Should detect broken link brackets"
        assert "bracket" in error.lower(), "Error should mention brackets"
    
    def test_structural_validation_backticks(self):
        """Backtick parity must be preserved."""
        original = "Use `code` and `more code` here."
        corrected = "Use `code` and `more code` here."
        
        is_valid, error = _validate_structural_integrity(original, corrected)
        assert is_valid, f"Valid correction should pass: {error}"
        
        # Broken backtick parity
        corrupted = "Use code` and `more code` here."
        is_valid, error = _validate_structural_integrity(original, corrupted)
        assert not is_valid, "Should detect broken backticks"
        assert "backtick" in error.lower(), "Error should mention backticks"
    
    def test_with_markdown_masking(self):
        """Grammar assist should work with Phase 1 masked content."""
        config = load_config()
        
        markdown_text = """
# Heading

This is a paragraf with a typo.

Check [this link](https://example.com) and some `code here`.

Another paragraf with erors.
"""
        
        # Apply Phase 1 masking
        masked_text, mask_table = mask_protected(markdown_text)
        
        # Apply grammar corrections
        corrected, stats = apply_grammar_corrections(masked_text, config, mask_table)
        
        # Unmask
        result = unmask(corrected, mask_table)
        
        # Verify masks are still present in result
        assert '[this link](https://example.com)' in result, "Link should be preserved"
        assert '`code here`' in result, "Code should be preserved"
        assert '# Heading' in result, "Heading should be preserved"
    
    def test_disabled_in_config(self):
        """Grammar assist should be skippable via config."""
        config = load_config()
        config['grammar_assist']['enabled'] = False
        
        text = "This has erors that wont be fixed."
        result, stats = apply_grammar_corrections(text, config)
        
        # Should return unchanged
        assert result == text, "Should return original text when disabled"
        assert all(v == 0 for v in stats.values()), "All stats should be zero when disabled"
    
    def test_locale_configuration(self):
        """Grammar assist should support different locales."""
        config = load_config()
        
        # English (default)
        assert config['grammar_assist']['language'] == 'en'
        
        # Test with custom locale
        config['grammar_assist']['language'] = 'is'  # Icelandic
        text = "Test text."
        
        # Should not crash with different locale
        result, stats = apply_grammar_corrections(text, config)
        assert isinstance(result, str), "Should return string even with non-English locale"
    
    def test_safe_category_filtering(self):
        """Only safe categories should be applied."""
        config = load_config()
        
        # Verify safe categories are configured
        safe_cats = config['grammar_assist']['safe_categories']
        assert 'TYPOS' in safe_cats
        assert 'PUNCTUATION' in safe_cats
        assert 'CASING' in safe_cats
        assert 'SPACING' in safe_cats
        assert 'SIMPLE_AGREEMENT' in safe_cats
    
    def test_category_mapping(self):
        """LanguageTool categories should map correctly to our safe categories."""
        # Spelling/typos
        assert _map_languagetool_category('MORFOLOGIK_RULE_EN', 'Possible Spelling Mistake') == 'TYPOS'
        
        # Spacing
        assert _map_languagetool_category('WHITESPACE_RULE', 'Whitespace') == 'SPACING'
        
        # Punctuation
        assert _map_languagetool_category('COMMA_RULE', 'Punctuation') == 'PUNCTUATION'
        
        # Casing
        assert _map_languagetool_category('UPPERCASE_SENTENCE_START', 'Casing') == 'CASING'
        
        # Unknown should return None (rejected)
        assert _map_languagetool_category('UNKNOWN_RULE', 'Unknown') is None
    
    def test_empty_text(self):
        """Should handle empty text gracefully."""
        config = load_config()
        result, stats = apply_grammar_corrections("", config)
        
        assert result == "", "Empty text should remain empty"
        assert all(v == 0 for v in stats.values()), "All stats should be zero for empty text"
    
    def test_text_with_only_markdown(self):
        """Should handle text with only Markdown syntax (no plain text)."""
        config = load_config()
        markdown_only = "# Heading\n\n## Subheading\n\n---\n"
        
        # Mask it
        masked, mask_table = mask_protected(markdown_only)
        result, stats = apply_grammar_corrections(masked, config, mask_table)
        final = unmask(result, mask_table)
        
        # Should preserve all Markdown
        assert '# Heading' in final
        assert '## Subheading' in final
        assert '---' in final
    
    @pytest.mark.llm
    def test_complex_corrections(self):
        """Test with more complex text requiring multiple corrections."""
        config = load_config()
        
        text = """
        This  text  has  double  spaces.
        It also has a typo: recieve instead of receive.
        And some  more spacing  issues here.
        """
        
        result, stats = apply_grammar_corrections(text, config)
        
        # Should have made some corrections
        total_fixes = sum(stats.get(k, 0) for k in 
                         ['typos_fixed', 'spacing_fixed', 'punctuation_fixed', 
                          'casing_fixed', 'agreement_fixed'])
        
        assert total_fixes > 0 or stats.get('rejected', 0) > 0, \
            "Should have attempted corrections or rejected some"


class TestGrammarSuggestion:
    """Test the GrammarSuggestion helper class."""
    
    def test_suggestion_creation(self):
        """Should create suggestion with correct attributes."""
        sug = GrammarSuggestion(
            offset=10,
            length=5,
            replacement="fixed",
            category="TYPOS",
            message="Spelling error"
        )
        
        assert sug.offset == 10
        assert sug.length == 5
        assert sug.replacement == "fixed"
        assert sug.category == "TYPOS"
        assert sug.message == "Spelling error"
    
    def test_suggestion_repr(self):
        """Should have useful string representation."""
        sug = GrammarSuggestion(
            offset=10,
            length=5,
            replacement="fixed",
            category="TYPOS",
            message="Spelling error"
        )
        
        repr_str = repr(sug)
        assert "offset=10" in repr_str
        assert "len=5" in repr_str
        assert "TYPOS" in repr_str
        assert "fixed" in repr_str


@pytest.mark.llm
class TestIntegrationWithPipeline:
    """Integration tests with other MDP phases."""
    
    def test_full_pipeline_chain(self):
        """Test mask → prepass-basic → grammar pipeline."""
        from mdp.prepass_basic import normalize_text_nodes
        from mdp.markdown_adapter import mask_protected, unmask
        
        config = load_config()
        
        text = """
# Test Document

This  has  double  spaces and a typo: recieve.

Check [this link](https://example.com) and `code`.
"""
        
        # Phase 1: Mask
        masked, mask_table = mask_protected(text)
        
        # Phase 2: Prepass basic
        normalized, prepass_stats = normalize_text_nodes(masked, config)
        
        # Phase 5: Grammar
        corrected, grammar_stats = apply_grammar_corrections(normalized, config, mask_table)
        
        # Unmask
        result = unmask(corrected, mask_table)
        
        # Verify structure preserved
        assert '# Test Document' in result
        assert '[this link](https://example.com)' in result
        assert '`code`' in result
        
        # Verify pipeline ran
        assert isinstance(prepass_stats, dict)
        assert isinstance(grammar_stats, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
