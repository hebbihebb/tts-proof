import unittest
from pathlib import Path
from collections import defaultdict
from mdp import scrubber, config, appendix


class TestScrubber(unittest.TestCase):

    def setUp(self):
        self.test_data_path = Path(__file__).parent.parent / "test_data" / "scrubber"
        self.default_config = config.load_config()
        self.scrubber_config = self.default_config.get('scrubber', {})

    def test_top_authors_note_detection(self):
        """Test detection of author's note at the beginning."""
        md_content = (self.test_data_path / "top_authors_note.md").read_text("utf-8")
        
        # Dry-run to see what would be detected
        _, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=True)
        
        # Should detect the author's note
        self.assertGreater(len(candidates), 0, "Should detect at least one candidate")
        
        # Check that author's note was detected
        authors_notes = [c for c in candidates if c.category == 'authors_note']
        self.assertEqual(len(authors_notes), 1, "Should detect exactly one author's note")
        
        # Verify it's in the edge-top position
        self.assertEqual(authors_notes[0].position, 'edge-top')

    def test_top_authors_note_removal(self):
        """Test actual removal of author's note."""
        md_content = (self.test_data_path / "top_authors_note.md").read_text("utf-8")
        
        # Apply scrubbing
        processed, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Author's note should be removed
        self.assertNotIn("Author's Note:", processed)
        self.assertNotIn("Don't forget to leave a review", processed)
        
        # Story content should be preserved
        self.assertIn("The Adventure Begins", processed)
        self.assertIn("Sir Roland", processed)
        
        # Check report
        self.assertEqual(report['authors_note'], 1)
        self.assertGreater(report['kept'], 0)

    def test_bottom_promo_nav_detection(self):
        """Test detection of promotional content and navigation at the end."""
        md_content = (self.test_data_path / "bottom_promo_nav.md").read_text("utf-8")
        
        _, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=True)
        
        # Should detect navigation and promo
        navigation = [c for c in candidates if c.category == 'navigation']
        promos = [c for c in candidates if c.category == 'promo_ad_social']
        
        self.assertGreater(len(navigation), 0, "Should detect navigation blocks")
        self.assertGreater(len(promos), 0, "Should detect promotional blocks")
        
        # All should be in edge-bottom position
        for candidate in candidates:
            self.assertIn(candidate.position, ['edge-bottom', 'edge-top'])

    def test_bottom_promo_nav_removal(self):
        """Test removal of promotional and navigation content."""
        md_content = (self.test_data_path / "bottom_promo_nav.md").read_text("utf-8")
        
        processed, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Promo and nav should be removed
        self.assertNotIn("Patreon", processed)
        self.assertNotIn("Discord", processed)
        self.assertNotIn("Table of Contents", processed)
        
        # Story content preserved
        self.assertIn("The Great Journey", processed)
        self.assertIn("remarkable adventure", processed)
        
        # Check report
        self.assertGreaterEqual(report['promo_ad_social'], 1)
        self.assertGreaterEqual(report['navigation'], 1)

    def test_mid_story_note_preserved_edge_bias(self):
        """Test that middle notes are preserved due to edge bias."""
        md_content = (self.test_data_path / "mid_story_letter.md").read_text("utf-8")
        
        processed, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Middle author's note should be preserved (edge bias)
        self.assertIn("A/N:", processed)
        self.assertIn("magic system", processed)
        
        # Story content preserved
        self.assertIn("The Quest for Knowledge", processed)
        
        # Check that middle bias kept the note
        self.assertGreaterEqual(report.get('kept_middle_bias', 0), 1)

    def test_link_farm_detection(self):
        """Test detection of link-heavy paragraphs."""
        md_content = (self.test_data_path / "link_farm.md").read_text("utf-8")
        
        _, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=True)
        
        # Should detect link farms
        link_farms = [c for c in candidates if c.category == 'link_farm']
        self.assertGreater(len(link_farms), 0, "Should detect link farm blocks")
        
        # Check link density was calculated
        for farm in link_farms:
            self.assertIn("Link density", farm.reason)

    def test_link_farm_removal(self):
        """Test removal of link farms while preserving story."""
        md_content = (self.test_data_path / "link_farm.md").read_text("utf-8")
        
        processed, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Link farm paragraphs should be reduced
        link_count_original = md_content.count('[')
        link_count_processed = processed.count('[')
        self.assertLess(link_count_processed, link_count_original, "Should have fewer links after scrubbing")
        
        # Story content preserved
        self.assertIn("Story Content", processed)
        self.assertIn("valuable narrative information", processed)
        
        # Check report
        self.assertGreaterEqual(report.get('link_farm', 0), 1)

    def test_whitelist_headings_preserved(self):
        """Test that whitelisted headings are not removed."""
        md_content = (self.test_data_path / "whitelist_headings.md").read_text("utf-8")
        
        processed, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Translator's Cultural Notes should be preserved (whitelisted)
        self.assertIn("Translator's Cultural Notes", processed)
        self.assertIn("Matsuri", processed)
        self.assertIn("cultural significance", processed)
        
        # Story content preserved
        self.assertIn("The Festival", processed)
        self.assertIn("lanterns were lit", processed)

    def test_dry_run_no_changes(self):
        """Test that dry-run mode doesn't modify the text."""
        md_content = (self.test_data_path / "top_authors_note.md").read_text("utf-8")
        
        processed, candidates, report = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=True)
        
        # Text should be unchanged in dry-run
        self.assertEqual(processed, md_content, "Dry-run should not modify text")
        
        # But candidates should still be detected
        self.assertGreater(len(candidates), 0, "Dry-run should detect candidates")

    def test_disabled_category_not_removed(self):
        """Test that disabled categories are not removed."""
        md_content = (self.test_data_path / "top_authors_note.md").read_text("utf-8")
        
        # Disable authors_notes category
        modified_config = self.scrubber_config.copy()
        modified_config['categories'] = modified_config['categories'].copy()
        modified_config['categories']['authors_notes'] = False
        
        processed, candidates, report = scrubber.scrub_text(md_content, modified_config, dry_run=False)
        
        # Author's note should NOT be removed when category is disabled
        self.assertIn("Author's Note:", processed)

    def test_appendix_format(self):
        """Test appendix generation."""
        md_content = (self.test_data_path / "top_authors_note.md").read_text("utf-8")
        
        _, candidates, _ = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Generate appendix
        appendix_content = appendix.format_appendix(candidates, "top_authors_note.md")
        
        # Check appendix structure
        self.assertIn("# Appendix", appendix_content)
        self.assertIn("Removed Author's Notes", appendix_content)
        self.assertIn("Block", appendix_content)
        self.assertIn("Reason:", appendix_content)

    def test_markdown_structure_preservation(self):
        """Test that Markdown structure remains valid after scrubbing."""
        md_content = (self.test_data_path / "bottom_promo_nav.md").read_text("utf-8")
        
        processed, _, _ = scrubber.scrub_text(md_content, self.scrubber_config, dry_run=False)
        
        # Check that headings are preserved
        self.assertIn("# The Great Journey", processed)
        self.assertIn("## Chapter One", processed)
        
        # Check that paragraphs are properly separated
        paragraphs = [p.strip() for p in processed.split('\n\n') if p.strip()]
        self.assertGreater(len(paragraphs), 0, "Should have paragraphs")
        
        # No excessive blank lines
        self.assertNotIn('\n\n\n\n', processed, "Should not have excessive blank lines")

    def test_block_splitting(self):
        """Test that block splitting works correctly."""
        test_text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        blocks = scrubber.split_into_blocks(test_text)
        
        self.assertEqual(len(blocks), 3, "Should split into 3 blocks")
        self.assertEqual(blocks[0], "Paragraph one.")
        self.assertEqual(blocks[1], "Paragraph two.")
        self.assertEqual(blocks[2], "Paragraph three.")

    def test_link_density_calculation(self):
        """Test the link density calculation function."""
        # High link density
        high_density = "Check [link one](http://example.com) and [link two](http://example.com)"
        density = scrubber.calculate_link_density(high_density)
        self.assertGreater(density, 0.2, "Should have measurable link density")
        self.assertLess(density, 0.5, "Should not exceed 50% with this example")
        
        # Low link density
        low_density = "This is a long paragraph with lots of text and only [one link](http://example.com) in it."
        density = scrubber.calculate_link_density(low_density)
        self.assertLess(density, 0.3, "Should have low link density")
        
        # No links
        no_links = "This paragraph has no links at all."
        density = scrubber.calculate_link_density(no_links)
        self.assertEqual(density, 0.0, "Should have zero link density")

    def test_scrubber_disabled(self):
        """Test that scrubber can be completely disabled."""
        md_content = (self.test_data_path / "top_authors_note.md").read_text("utf-8")
        
        # Disable scrubber
        disabled_config = self.scrubber_config.copy()
        disabled_config['enabled'] = False
        
        processed, candidates, report = scrubber.scrub_text(md_content, disabled_config, dry_run=False)
        
        # Nothing should be removed
        self.assertEqual(processed, md_content, "Disabled scrubber should not modify text")
        self.assertEqual(len(candidates), 0, "Disabled scrubber should detect no candidates")
        self.assertEqual(report.get('scrubber_disabled', 0), 1)

    def test_min_chars_threshold(self):
        """Test that blocks below minimum character threshold are not scrubbed."""
        # Short author's note (below default 12 char threshold)
        short_text = "A/N: Hi"
        
        _, candidates, _ = scrubber.scrub_text(short_text, self.scrubber_config, dry_run=True)
        
        # Should not be detected due to length
        self.assertEqual(len(candidates), 0, "Short blocks should not be detected")


if __name__ == '__main__':
    unittest.main()
