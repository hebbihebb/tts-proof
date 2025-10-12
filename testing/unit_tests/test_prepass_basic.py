import unittest
from pathlib import Path
from collections import defaultdict
from mdp import prepass_basic, config, markdown_adapter
import yaml

class TestPrepassBasic(unittest.TestCase):

    def setUp(self):
        self.test_data_path = Path(__file__).parent.parent / "test_data" / "prepass"
        self.default_config = config.load_config()

    def test_full_run_with_report(self):
        """Tests a full run of the prepass-basic step, including the report."""
        md_content = (self.test_data_path / "punct_policy.md").read_text("utf-8")

        # Create a temporary config file
        config_data = {
            'normalize_punctuation': True,
            'quotes_policy': 'straight',
            'dashes_policy': 'em',
        }
        with open("temp_config.yaml", "w") as f:
            yaml.dump(config_data, f)

        cfg = config.load_config("temp_config.yaml")

        # Use the same logic as in md_proof.py
        text_spans = markdown_adapter.extract_text_spans(md_content)
        new_content_parts = []
        last_end = 0
        total_report = defaultdict(int)

        for span in text_spans:
            new_content_parts.append(md_content[last_end:span['start']])
            normalized_text, report = prepass_basic.normalize_text_nodes(span['text'], cfg)
            new_content_parts.append(normalized_text)
            for k, v in report.items():
                total_report[k] += v
            last_end = span['end']

        new_content_parts.append(md_content[last_end:])
        normalized_content = "".join(new_content_parts)

        self.assertIn('Here are some "curly quotes" and \'single curly quotes\'.', normalized_content)
        self.assertIn("Here is an ellipsis...", normalized_content)
        self.assertEqual(total_report['curly_quotes_straightened'], 4)
        self.assertEqual(total_report['ellipses_standardized'], 1)
        self.assertEqual(total_report['dashes_normalized'], 1)


        # Clean up the temporary config file
        Path("temp_config.yaml").unlink()

    def test_unicode_strip(self):
        """Tests removal of ZWSP, soft hyphens, and bidi controls."""
        md_content = (self.test_data_path / "unicode_zwsp.md").read_text("utf-8")
        normalized, report = prepass_basic.normalize_text_nodes(md_content, self.default_config)
        self.assertNotIn('\u200b', normalized)
        self.assertNotIn('\u00ad', normalized)
        self.assertNotIn('\u202c', normalized)
        self.assertNotIn('\ufeff', normalized)
        self.assertEqual(report['control_chars_stripped'], 4)

    def test_join_spaced_letters(self):
        """Tests joining of spaced-out letters."""
        md_content = (self.test_data_path / "spaced_letters.md").read_text("utf-8")
        normalized, report = prepass_basic.normalize_text_nodes(md_content, self.default_config)
        self.assertIn("Spaced out letters.", normalized)
        self.assertIn("Another example.", normalized)
        self.assertIn("And FLASH.", normalized)
        self.assertIn("This should not be changed: a b c.", normalized)
        self.assertEqual(report['spaced_words_joined'], 3)

    def test_hyphenation_heal(self):
        """Tests healing of hyphenation at line breaks."""
        md_content = (self.test_data_path / "hyphen_wrap.md").read_text("utf-8")
        normalized, report = prepass_basic.normalize_text_nodes(md_content, self.default_config)
        self.assertIn("creative sentence.", normalized)
        self.assertIn("state-of-the-art", normalized)
        self.assertEqual(report.get('hyphenation_healed', 0), 1)

    def test_punctuation_normalization(self):
        """Tests normalization of punctuation."""
        md_content = (self.test_data_path / "punct_policy.md").read_text("utf-8")

        # Test with straight quotes policy
        normalized, report = prepass_basic.normalize_text_nodes(md_content, self.default_config)
        self.assertIn('Here are some "curly quotes" and \'single curly quotes\'.', normalized)
        self.assertIn("Here is an ellipsis...", normalized)

        # Test with curly quotes policy (no change expected as it's not implemented)
        curly_config = config.load_config()
        curly_config['quotes_policy'] = 'curly'
        normalized, report = prepass_basic.normalize_text_nodes(md_content, curly_config)
        self.assertIn('Here are some “curly quotes” and ‘single curly quotes’.', normalized)

if __name__ == '__main__':
    unittest.main()