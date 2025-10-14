#!/usr/bin/env python3
"""
MDP (Markdown Processing) CLI Interface

Supports pipeline chaining with --steps argument:
  python -m mdp input.md --steps mask,prepass-basic,prepass-advanced,grammar,detect,apply,fix

Available steps:
  - mask: Phase 1 Markdown masking
  - prepass-basic: Phase 2 Unicode & spacing normalization
  - prepass-advanced: Phase 2+ Advanced normalization
  - scrubber: Phase 3 Content scrubbing
  - grammar: Phase 5 Grammar assist (requires Java)
  - detect: Phase 6 Detector (tiny model → JSON plan)
  - apply: Phase 7 Plan Applier with structural validation
  - fix: Phase 8 Fixer (bigger model → light polish on text nodes)
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


from .tie_breaker import detect_hazards, tie_break, postcheck, DecisionLogger


def run_pipeline(
    input_text: str,
    steps: List[str],
    config: Dict[str, Any],
    detector_dump_dir: Path = None,
    run_dir: Optional[Path] = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Run the MDP pipeline with specified steps.
    
    Args:
        input_text: Input Markdown text
        steps: List of step names to execute
        config: Configuration dictionary
        detector_dump_dir: Optional directory to dump raw detector outputs
    
    Returns:
        (processed_text, combined_stats)
    """
    from . import markdown_adapter, prepass_basic, prepass_advanced, scrubber, grammar_assist
    
    text = input_text
    combined_stats = {}
    mask_table = None
    prepass_snapshot: Optional[str] = None
    grammar_snapshot: Optional[str] = None
    fixer_snapshot: Optional[str] = None
    decision_logger = DecisionLogger(run_dir / "decision-log.ndjson" if run_dir else None)
    
    for step in steps:
        logger.info(f"Running step: {step}")
        
        if step == 'mask':
            # Phase 1: Markdown masking
            text, mask_table = markdown_adapter.mask_protected(text)
            combined_stats['mask'] = {
                'masks_created': len(mask_table)
            }
            logger.info(f"  Masked {len(mask_table)} regions")
        
        elif step == 'prepass-basic':
            # Phase 2: Unicode & spacing normalization
            text, stats = prepass_basic.normalize_text_nodes(text, config)
            combined_stats['prepass-basic'] = stats
            logger.info(f"  Stats: {stats}")
            prepass_snapshot = text
        
        elif step == 'prepass-advanced':
            # Phase 2+: Advanced normalization
            from .prepass_advanced import normalize_casing, collapse_punctuation_runs, normalize_ellipsis
            
            step_stats = {}
            
            # Casing
            if config.get('prepass_advanced', {}).get('enabled', True):
                text, casing_fixes = normalize_casing(text, config)
                step_stats['casing_fixes'] = casing_fixes
                
                # Punctuation
                text, punct_fixes = collapse_punctuation_runs(text, config)
                step_stats['punctuation_fixes'] = punct_fixes
                
                # Ellipsis
                text, ellipsis_fixes = normalize_ellipsis(text, config)
                step_stats['ellipsis_fixes'] = ellipsis_fixes
            
            combined_stats['prepass-advanced'] = step_stats
            logger.info(f"  Stats: {step_stats}")
            prepass_snapshot = text
        
        elif step == 'scrubber':
            # Phase 3: Content scrubbing
            scrubber_config = config.get('scrubber', {})
            if scrubber_config.get('enabled', True):
                text, candidates, stats = scrubber.scrub_text(text, config, dry_run=False)
                combined_stats['scrubber'] = stats
                combined_stats['scrubber']['blocks_removed'] = len(candidates)
                logger.info(f"  Removed {len(candidates)} blocks, stats: {stats}")
            else:
                logger.info("  Scrubber disabled in config")
        
        elif step == 'grammar':
            # Phase 5: Grammar assist
            text, stats = grammar_assist.apply_grammar_corrections(text, config, mask_table)
            combined_stats['grammar'] = stats
            logger.info(f"  Stats: {stats}")
            grammar_snapshot = text
        
        elif step == 'detect':
            # Phase 6: Detector
            from detector.detector import run_detector
            from detector.schema import plan_to_json
            from detector.client import ModelClient
            import requests
            
            detector_config = config.get('detector', {})
            
            # Check server connectivity before processing
            try:
                api_base = detector_config.get('api_base', 'http://127.0.0.1:1234/v1')
                logger.info(f"  Checking connectivity to: {api_base}")
                response = requests.get(f"{api_base}/models", timeout=5)
                if response.status_code != 200:
                    raise ConnectionError(f"Server returned status {response.status_code}")
                logger.info("  Server is reachable")
            except Exception as e:
                logger.error(f"  Detector model server unreachable: {e}")
                logger.error(f"  Make sure LM Studio (or compatible server) is running at {api_base}")
                raise ConnectionError("Detector requires reachable model server") from e
            
            # Extract text nodes for detector (simple approach - split on newlines)
            # In real implementation, would use AST to get actual text nodes
            text_nodes = [line.strip() for line in text.split('\n') if line.strip()]
            
            plan, stats = run_detector(text_nodes, detector_config)
            combined_stats['detect'] = stats
            combined_stats['detect']['plan_size'] = len(plan)
            logger.info(f"  Proposed {len(plan)} replacements")
            logger.info(f"  Stats: {stats}")
            
            # Store plan for potential use by Phase 7
            combined_stats['detect']['plan'] = plan_to_json(plan)
            
            # Dump raw outputs if requested (debugging only)
            if detector_dump_dir:
                detector_dump_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"  Dumping raw outputs to: {detector_dump_dir}")
                # Note: This would require modifying detector to capture raw responses
                # For now, just log that the feature is available
                logger.warning("  --detector-dump requires instrumentation (not yet implemented)")
        
        elif step == 'apply':
            # Phase 7: Plan Applier with structural validation
            from apply.applier import apply_plan_to_text
            from apply.validate import validate_all
            
            apply_config = config.get('apply', {})
            
            # Check if we have a plan from previous detector step
            plan_items = combined_stats.get('detect', {}).get('plan', [])
            
            if not plan_items:
                logger.warning("  No replacements to apply (detector returned empty plan)")
                logger.info("  Skipping apply step - text unchanged")
                combined_stats['apply'] = {
                    'replacements_applied': 0,
                    'length_delta': 0,
                    'growth_ratio': 0.0,
                    'validation_passed': True,
                    'skipped': True,
                    'reason': 'empty_plan'
                }
                continue
            
            logger.info(f"  Applying plan with {len(plan_items)} items")
            
            # Apply plan to text
            try:
                edited_text, report = apply_plan_to_text(text, plan_items, config)
            except Exception as e:
                logger.error(f"  Plan application failed: {e}")
                raise ValueError(f"Apply failed: {e}") from e
            
            # Validate structural integrity
            is_valid, failures = validate_all(text, edited_text, config)
            
            if not is_valid:
                logger.error(f"  Validation failed with {len(failures)} error(s):")
                for failure in failures:
                    logger.error(f"    - {failure}")
                
                # Write rejected file if configured
                if apply_config.get('reject_dir'):
                    reject_dir = Path(apply_config['reject_dir'])
                    reject_dir.mkdir(parents=True, exist_ok=True)
                    reject_file = reject_dir / (Path(input_text).stem + '.rejected.md')
                    reject_file.write_text(edited_text, encoding='utf-8')
                    logger.info(f"  Wrote rejected edit to: {reject_file}")
                
                raise ValueError(f"Validation failed: {'; '.join(failures)}")
            
            # Validation passed - use edited text
            text = edited_text
            combined_stats['apply'] = report
            combined_stats['apply']['validation_passed'] = True
            logger.info(f"  Applied {report['replacements_applied']} replacements")
            logger.info(f"  Length delta: {report['length_delta']:+d} chars")
            logger.info(f"  Growth ratio: {report['growth_ratio']:.2%}")
        
        elif step == 'fix':
            # Phase 8: Fixer - light polish on text nodes
            from fixer.fixer import apply_fixer
            from apply.validate import validate_all
            
            fixer_config = config.get('fixer', {})
            
            if not fixer_config.get('enabled', True):
                logger.info("  Fixer disabled in config")
                continue
            
            # Need text nodes and mask table from Phase 1
            if mask_table is None:
                logger.error("  Fixer requires masking - run with --steps mask,...,fix")
                raise ValueError("Fixer requires Phase 1 masking (run with --steps mask,...,fix)")
            
            # Extract text nodes from current text
            text_nodes = markdown_adapter.extract_text_spans(text)
            
            logger.info(f"  Fixing {len(text_nodes)} text nodes")
            
            try:
                fixed_text, fixer_stats = apply_fixer(
                    text=text,
                    text_nodes=text_nodes,
                    mask_table=mask_table,
                    config=fixer_config
                )
                
                # Validate after fixing (reuse Phase 7 validators)
                logger.info("  Validating fixed text...")
                is_valid, failures = validate_all(text, fixed_text, config)
                
                if not is_valid:
                    logger.error(f"  Validation failed after fixer with {len(failures)} error(s):")
                    for failure in failures:
                        logger.error(f"    - {failure}")
                    
                    # Write rejected file if reject_dir exists
                    apply_config = config.get('apply', {})
                    if apply_config.get('reject_dir'):
                        reject_dir = Path(apply_config['reject_dir'])
                        reject_dir.mkdir(parents=True, exist_ok=True)
                        reject_file = reject_dir / (Path(input_text).stem + '.rejected.md')
                        reject_file.write_text(fixed_text, encoding='utf-8')
                        logger.info(f"  Wrote rejected fix to: {reject_file}")
                    
                    sys.exit(3)  # Validation failure
                
                # Validation passed - use fixed text
                text = fixed_text
                combined_stats['fix'] = fixer_stats
                logger.info(f"  Fixed {fixer_stats['spans_fixed']} of {fixer_stats['spans_total']} spans")
                logger.info(f"  File growth: {fixer_stats['file_growth_ratio']:.2%}")
                fixer_snapshot = text
                
            except ConnectionError as e:
                logger.error(f"  Fixer model server unreachable: {e}")
                logger.error(f"  Make sure LM Studio is running at {fixer_config.get('api_base')}")
                sys.exit(2)  # Model unreachable
        
        else:
            logger.warning(f"Unknown step: {step}")
    
    # Tie-breaker and postcheck (Phase 12)
    if grammar_snapshot is not None:
        baseline = prepass_snapshot or input_text
        hazard_mask = detect_hazards(baseline)
        merged_text, tie_stats = tie_break(
            prepass_text=baseline,
            grammar_text=grammar_snapshot,
            tts_text=fixer_snapshot,
            hazard_mask=hazard_mask,
            logger=decision_logger,
        )
        combined_stats['tie_breaker'] = tie_stats
        text = merged_text

        postcheck_result = postcheck(text)
        combined_stats['postcheck'] = postcheck_result

        if run_dir:
            if not postcheck_result.get('ok'):
                failed_path = Path(run_dir) / 'failed-chunks.json'
                data = json.dumps(postcheck_result, ensure_ascii=False, indent=2)
                failed_path.write_text(data, encoding='utf-8')

    # Unmask if we masked
    if mask_table is not None and 'mask' in steps:
        text = markdown_adapter.unmask(text, mask_table)
        logger.info("Unmasked Markdown structure")
    
    return text, combined_stats


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='MDP: Markdown Processing Pipeline',
        epilog='''
Examples:
  # Run full pipeline
  python -m mdp input.md --steps mask,prepass-basic,prepass-advanced,grammar
  
  # Run only grammar correction
  python -m mdp input.md --steps mask,grammar -o output.md
  
  # Run prepass without grammar
  python -m mdp input.md --steps mask,prepass-basic,prepass-advanced
  
  # Include scrubber
  python -m mdp input.md --steps mask,prepass-basic,scrubber
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input_file', type=Path, help='Input Markdown file')
    parser.add_argument('-o', '--output', type=Path, help='Output file (default: stdout)')
    parser.add_argument('-c', '--config', type=Path, help='Configuration YAML file')
    parser.add_argument('--steps', type=str, 
                       default='mask,prepass-basic',
                       help='Comma-separated pipeline steps (default: mask,prepass-basic)')
    parser.add_argument('--report', type=Path, 
                       help='Output JSON report file with statistics')
    parser.add_argument('--report-pretty', action='store_true',
                       help='Print human-readable report summary after JSON report')
    parser.add_argument('--plan', type=Path,
                       help='Output JSON plan file (for detector step)')
    parser.add_argument('--print-plan', action='store_true',
                       help='Print detector plan to stdout')
    parser.add_argument('--detector-dump', type=Path,
                       help='Directory to dump per-span raw model outputs (debug only)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Apply step: show diff without writing output')
    parser.add_argument('--print-diff', action='store_true',
                       help='Apply step: print unified diff after applying plan')
    parser.add_argument('--reject-dir', type=Path,
                       help='Apply step: directory to write rejected edits (if validation fails)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    from . import config as cfg_module
    config = cfg_module.load_config(str(args.config) if args.config else None)
    
    # Read input file
    if not args.input_file.exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    logger.info(f"Reading input file: {args.input_file}")
    input_text = args.input_file.read_text(encoding='utf-8')
    
    # Parse steps
    steps = [s.strip() for s in args.steps.split(',')]
    logger.info(f"Pipeline steps: {' → '.join(steps)}")
    
    # Validate steps
    valid_steps = {'mask', 'prepass-basic', 'prepass-advanced', 'scrubber', 'grammar', 'detect', 'apply', 'fix'}
    invalid_steps = set(steps) - valid_steps
    if invalid_steps:
        logger.error(f"Invalid steps: {invalid_steps}")
        logger.error(f"Valid steps: {valid_steps}")
        return 1
    
    # Run pipeline
    try:
        output_text, stats = run_pipeline(input_text, steps, config, args.detector_dump)
    except ConnectionError as e:
        # Exit code 2 for unreachable model server
        logger.error(f"Pipeline failed: {e}")
        return 2
    except ValueError as e:
        # Exit code 3 for validation failures (from apply step)
        if "Validation failed" in str(e):
            logger.error(f"Pipeline failed: {e}")
            return 3
        # Exit code 4 for plan parse errors
        elif "plan" in str(e).lower() or "parse" in str(e).lower():
            logger.error(f"Pipeline failed: {e}")
            return 4
        else:
            logger.error(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Write output
    if args.output:
        args.output.write_text(output_text, encoding='utf-8')
        logger.info(f"Wrote output to: {args.output}")
    else:
        print(output_text)
    
    # Write detector plan if requested
    if args.plan and 'detect' in steps and 'detect' in stats:
        plan_data = stats['detect'].get('plan', [])
        args.plan.write_text(json.dumps(plan_data, indent=2), encoding='utf-8')
        logger.info(f"Wrote plan to: {args.plan}")
    
    # Print detector plan if requested
    if args.print_plan and 'detect' in steps and 'detect' in stats:
        plan_data = stats['detect'].get('plan', [])
        print("\n=== Detector Plan ===")
        print(json.dumps(plan_data, indent=2))
    
    # Write report
    report_data = None
    if args.report:
        report_data = {
            'input_file': str(args.input_file),
            'output_file': str(args.output) if args.output else None,
            'steps': steps,
            'statistics': stats
        }
        args.report.write_text(json.dumps(report_data, indent=2), encoding='utf-8')
        logger.info(f"Wrote report to: {args.report}")
    
    # Print pretty report if requested
    if args.report_pretty:
        from report import render_pretty
        
        # Build report data if not already created
        if report_data is None:
            report_data = {
                'input_file': str(args.input_file),
                'output_file': str(args.output) if args.output else None,
                'steps': steps,
                'statistics': stats
            }
        
        pretty_output = render_pretty(report_data)
        print(pretty_output)
    
    # Print summary
    print("\n=== Pipeline Summary ===")
    for step, step_stats in stats.items():
        print(f"\n{step}:")
        if isinstance(step_stats, dict):
            for key, value in step_stats.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {step_stats}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
