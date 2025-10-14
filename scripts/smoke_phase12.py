import os
import sys
from pathlib import Path
from uuid import uuid4

# Ensure repository root is importable when running as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mdp.__main__ import run_pipeline
try:
    from mdp.config import load_config
except Exception:  # pragma: no cover - fallback path
    from mdp import config as cfg
    load_config = cfg.load_config


def main() -> None:
    src = Path("testing/test_data/phase12_adversarial.md")
    if not src.exists():
        raise FileNotFoundError(f"Missing test file: {src}")

    text = src.read_text(encoding="utf-8")
    config = load_config(None)

    run_id = f"smoke-{uuid4().hex[:8]}"
    run_root = Path(os.environ.get("MDP_SMOKE_RUN_ROOT", Path.home() / ".mdp" / "runs"))
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    stages = ["mask", "prepass-basic", "prepass-advanced", "grammar", "fix"]

    output_text, stats = run_pipeline(
        text,
        stages,
        config,
        run_dir=run_dir,
    )

    (run_dir / "output.md").write_text(output_text, encoding="utf-8")
    print("RUN_DIR", run_dir)
    print("FIX", stats.get("fix"))
    print("TIE_BREAKER", stats.get("tie_breaker"))
    print("POSTCHECK", stats.get("postcheck"))


if __name__ == "__main__":
    main()
