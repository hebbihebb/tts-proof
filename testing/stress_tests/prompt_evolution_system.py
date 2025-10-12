#!/usr/bin/env python3
"""
Prompt Evolution System for TTS-Proof

Interactive system for iterating on prepass and grammar prompts with:
1. Automatic backup and versioning of prompts
2. Test-driven prompt improvement
3. A/B testing between prompt versions
4. Detailed analysis of what changes work and why
5. Rollback capability to previous versions
6. Structured improvement documentation
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import difflib

from stress_test_system import StressTestSystem, TestResult

class PromptEvolutionSystem:
    """System for systematically improving prompts through testing"""
    
    def __init__(self):
        self.prepass_prompt_file = Path("prepass_prompt.txt")
        self.grammar_prompt_file = Path("grammar_promt.txt")  # Keep original typo
        self.versions_dir = Path("prompt_versions")
        self.evolution_log = Path("prompt_evolution_log.md")
        
        # Create directories
        self.versions_dir.mkdir(exist_ok=True)
        
        # Initialize test system
        self.test_system = StressTestSystem()
        
        # Load version history
        self.version_history = self.load_version_history()
    
    def backup_current_prompts(self, version_tag: str) -> str:
        """Backup current prompts with version tag"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = f"{timestamp}_{version_tag}"
        
        version_dir = self.versions_dir / version_id
        version_dir.mkdir(exist_ok=True)
        
        # Backup prepass prompt
        if self.prepass_prompt_file.exists():
            shutil.copy2(self.prepass_prompt_file, version_dir / "prepass_prompt.txt")
        
        # Backup grammar prompt  
        if self.grammar_prompt_file.exists():
            shutil.copy2(self.grammar_prompt_file, version_dir / "grammar_promt.txt")
        
        # Save metadata
        metadata = {
            "version_id": version_id,
            "timestamp": timestamp,
            "tag": version_tag,
            "created_by": "PromptEvolutionSystem",
            "prepass_exists": self.prepass_prompt_file.exists(),
            "grammar_exists": self.grammar_prompt_file.exists()
        }
        
        with open(version_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Backed up prompts as version: {version_id}")
        return version_id
    
    def load_version_history(self) -> List[Dict]:
        """Load all prompt versions from disk"""
        versions = []
        
        for version_dir in self.versions_dir.iterdir():
            if version_dir.is_dir():
                metadata_file = version_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        versions.append(metadata)
                    except Exception as e:
                        print(f"Warning: Could not load metadata from {version_dir}: {e}")
        
        # Sort by timestamp
        versions.sort(key=lambda x: x.get('timestamp', ''))
        return versions
    
    def create_prompt_variant(self, prompt_type: str, changes_description: str, 
                            new_content: str) -> str:
        """Create a new prompt variant and test it"""
        
        # Backup current version first
        version_tag = f"{prompt_type}_{changes_description.replace(' ', '_')}"
        backup_id = self.backup_current_prompts(version_tag)
        
        # Update the prompt file
        prompt_file = self.prepass_prompt_file if prompt_type == "prepass" else self.grammar_prompt_file
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Updated {prompt_type} prompt: {changes_description}")
        
        # Log the change
        self.log_prompt_change(backup_id, prompt_type, changes_description, new_content)
        
        return backup_id
    
    def test_current_prompts(self) -> TestResult:
        """Test current prompt configuration"""
        print("\\n=== Testing Current Prompt Configuration ===")
        
        # Reload prompts to get latest versions
        self.test_system.load_current_prompts()
        
        # Run comprehensive test
        result = self.test_system.run_comprehensive_test()
        
        return result
    
    def compare_versions(self, version_id_a: str, version_id_b: str) -> Dict:
        """Compare two prompt versions by testing both"""
        
        print(f"\\n=== Comparing Versions: {version_id_a} vs {version_id_b} ===")
        
        # Test version A
        self.restore_version(version_id_a)
        result_a = self.test_current_prompts()
        
        # Test version B  
        self.restore_version(version_id_b)
        result_b = self.test_current_prompts()
        
        # Compare results
        comparison = {
            'version_a': {
                'id': version_id_a,
                'match_percentage': result_a.reference_match_percentage,
                'problems_found': result_a.total_problems_found,
                'processing_time': result_a.processing_time_seconds
            },
            'version_b': {
                'id': version_id_b, 
                'match_percentage': result_b.reference_match_percentage,
                'problems_found': result_b.total_problems_found,
                'processing_time': result_b.processing_time_seconds
            }
        }
        
        # Calculate improvements
        match_improvement = result_b.reference_match_percentage - result_a.reference_match_percentage
        time_improvement = result_a.processing_time_seconds - result_b.processing_time_seconds
        
        comparison['improvements'] = {
            'match_percentage': match_improvement,
            'processing_time_seconds': time_improvement,
            'better_version': version_id_b if match_improvement > 0 else version_id_a
        }
        
        print(f"\\n📊 Version Comparison Results:")
        print(f"   {version_id_a}: {result_a.reference_match_percentage:.1f}% match")
        print(f"   {version_id_b}: {result_b.reference_match_percentage:.1f}% match")
        print(f"   Improvement: {match_improvement:+.1f}%")
        
        return comparison
    
    def restore_version(self, version_id: str):
        """Restore prompts from a specific version"""
        version_dir = self.versions_dir / version_id
        
        if not version_dir.exists():
            raise ValueError(f"Version {version_id} not found")
        
        # Restore prepass prompt
        prepass_backup = version_dir / "prepass_prompt.txt"
        if prepass_backup.exists():
            shutil.copy2(prepass_backup, self.prepass_prompt_file)
            print(f"✓ Restored prepass prompt from {version_id}")
        
        # Restore grammar prompt
        grammar_backup = version_dir / "grammar_promt.txt"
        if grammar_backup.exists():
            shutil.copy2(grammar_backup, self.grammar_prompt_file)
            print(f"✓ Restored grammar prompt from {version_id}")
    
    def log_prompt_change(self, version_id: str, prompt_type: str, 
                         changes_description: str, new_content: str):
        """Log prompt changes to evolution log"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.evolution_log, 'a', encoding='utf-8') as f:
            f.write(f"\\n## {timestamp} - {prompt_type.title()} Prompt Change\\n\\n")
            f.write(f"**Version ID:** {version_id}\\n")
            f.write(f"**Change Description:** {changes_description}\\n")
            f.write(f"**Prompt Type:** {prompt_type}\\n\\n")
            
            f.write("### New Content\\n\\n")
            f.write("```\\n")
            f.write(new_content[:500])  # First 500 chars
            if len(new_content) > 500:
                f.write("\\n... (truncated)")
            f.write("\\n```\\n\\n")
            
            f.write("---\\n")
    
    def generate_evolution_report(self) -> str:
        """Generate comprehensive evolution report"""
        
        report_lines = []
        report_lines.append("# Prompt Evolution Report\\n")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        report_lines.append(f"**Total Versions:** {len(self.version_history)}\\n\\n")
        
        report_lines.append("## Version History\\n\\n")
        
        for i, version in enumerate(self.version_history):
            report_lines.append(f"### {i+1}. {version['version_id']}\\n")
            report_lines.append(f"- **Tag:** {version['tag']}\\n")
            report_lines.append(f"- **Timestamp:** {version['timestamp']}\\n")
            report_lines.append(f"- **Has Prepass:** {'✓' if version['prepass_exists'] else '✗'}\\n")
            report_lines.append(f"- **Has Grammar:** {'✓' if version['grammar_exists'] else '✗'}\\n\\n")
        
        # Add test results if available
        if hasattr(self.test_system, 'test_history') and self.test_system.test_history:
            report_lines.append("## Recent Test Results\\n\\n")
            
            for result in self.test_system.test_history[-5:]:  # Last 5 results
                report_lines.append(f"### {result.timestamp}\\n")
                report_lines.append(f"- **Reference Match:** {result.reference_match_percentage:.1f}%\\n")
                report_lines.append(f"- **Problems Found:** {result.total_problems_found}\\n")
                report_lines.append(f"- **Processing Time:** {result.processing_time_seconds:.2f}s\\n\\n")
        
        return "\\n".join(report_lines)
    
    def interactive_improvement_session(self):
        """Interactive session for improving prompts"""
        print("\\n=== Interactive Prompt Improvement Session ===")
        print("Available commands:")
        print("  test    - Test current prompts")
        print("  backup  - Backup current prompts with tag")
        print("  edit    - Edit a prompt (prepass/grammar)")
        print("  compare - Compare two versions") 
        print("  restore - Restore a previous version")
        print("  report  - Generate evolution report")
        print("  history - Show version history")
        print("  quit    - Exit session")
        
        while True:
            try:
                command = input("\\n> ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "test":
                    result = self.test_current_prompts()
                    print(f"\\n📊 Test Results:")
                    print(f"   Reference match: {result.reference_match_percentage:.1f}%")
                    print(f"   Problems found: {result.total_problems_found}")
                    
                elif command == "backup":
                    tag = input("Enter version tag: ").strip()
                    if tag:
                        version_id = self.backup_current_prompts(tag)
                        print(f"✓ Created backup: {version_id}")
                    
                elif command == "edit":
                    prompt_type = input("Edit which prompt? (prepass/grammar): ").strip().lower()
                    if prompt_type in ['prepass', 'grammar']:
                        print(f"\\nCurrent {prompt_type} prompt:")
                        current_file = self.prepass_prompt_file if prompt_type == 'prepass' else self.grammar_prompt_file
                        
                        if current_file.exists():
                            with open(current_file, encoding='utf-8') as f:
                                current_content = f.read()
                            print(f"```\\n{current_content[:200]}...\\n```")
                        
                        print("\\nEnter new content (or 'cancel' to abort):")
                        print("(Type 'END' on a new line when finished)")
                        
                        new_lines = []
                        while True:
                            line = input()
                            if line == "END":
                                break
                            elif line == "cancel":
                                print("Edit cancelled.")
                                break
                            new_lines.append(line)
                        
                        if new_lines and new_lines != ["cancel"]:
                            new_content = "\\n".join(new_lines)
                            changes_desc = input("Describe the changes: ").strip()
                            version_id = self.create_prompt_variant(prompt_type, changes_desc, new_content)
                            print(f"✓ Updated {prompt_type} prompt. Backup: {version_id}")
                    
                elif command == "compare":
                    print("Available versions:")
                    for i, version in enumerate(self.version_history[-10:]):  # Last 10
                        print(f"  {i}: {version['version_id']} - {version['tag']}")
                    
                    try:
                        idx_a = int(input("First version index: "))
                        idx_b = int(input("Second version index: "))
                        
                        if 0 <= idx_a < len(self.version_history) and 0 <= idx_b < len(self.version_history):
                            version_a = self.version_history[idx_a]['version_id']
                            version_b = self.version_history[idx_b]['version_id']
                            comparison = self.compare_versions(version_a, version_b)
                            
                            print("\\n📋 Comparison saved to test logs")
                        else:
                            print("Invalid version indices")
                    except ValueError:
                        print("Please enter valid numbers")
                    
                elif command == "restore":
                    print("Available versions:")
                    for i, version in enumerate(self.version_history[-10:]):
                        print(f"  {i}: {version['version_id']} - {version['tag']}")
                    
                    try:
                        idx = int(input("Version index to restore: "))
                        if 0 <= idx < len(self.version_history):
                            version_id = self.version_history[idx]['version_id']
                            self.restore_version(version_id)
                            print(f"✓ Restored version {version_id}")
                        else:
                            print("Invalid version index")
                    except ValueError:
                        print("Please enter a valid number")
                    
                elif command == "report":
                    report = self.generate_evolution_report()
                    report_file = f"evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    
                    with open(report_file, 'w', encoding='utf-8') as f:
                        f.write(report)
                    
                    print(f"✓ Evolution report saved to: {report_file}")
                    
                elif command == "history":
                    print("\\n📜 Version History:")
                    for i, version in enumerate(self.version_history):
                        print(f"  {i}: {version['version_id']} - {version['tag']}")
                    
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\\n\\nExiting session...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\\n👋 Interactive session ended.")


def main():
    """Main function for prompt evolution system"""
    
    evolution_system = PromptEvolutionSystem()
    
    print("=== TTS-Proof Prompt Evolution System ===")
    print("This system helps you iteratively improve prompts through testing.")
    
    # Check if we have existing versions
    if evolution_system.version_history:
        print(f"\\n📚 Found {len(evolution_system.version_history)} existing prompt versions")
        
        # Show latest version
        latest = evolution_system.version_history[-1]
        print(f"   Latest: {latest['version_id']} - {latest['tag']}")
    else:
        print("\\n📝 No previous versions found. Creating initial backup...")
        initial_version = evolution_system.backup_current_prompts("initial_baseline")
        print(f"   Created: {initial_version}")
    
    # Start interactive session
    evolution_system.interactive_improvement_session()


if __name__ == "__main__":
    main()