# TTS-Proof Makefile
# Cross-platform task runner for common operations

.PHONY: help test test-fast test-all smoke clean install dev

# Default target
help:
	@echo "TTS-Proof - Available Commands:"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run fast tests (<1s, default)"
	@echo "  make test-all   - Run all tests including LLM/slow/network"
	@echo "  make test-fast  - Alias for 'make test'"
	@echo "  make smoke      - Run smoke tests (detect+apply workflow)"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install all dependencies (backend + frontend)"
	@echo "  make dev        - Start development servers"
	@echo "  make clean      - Remove temporary files and caches"
	@echo ""
	@echo "CI/Automation:"
	@echo "  make ci-quick   - Lightweight CI job (smoke tests + fast tests)"

# Fast tests (default for development)
test:
	python -m pytest

test-fast: test

# All tests (including LLM, slow, network)
test-all:
	python -m pytest -m ""

# Smoke tests - end-to-end detector + applier workflow
smoke:
	@echo "=== Running Smoke Tests ==="
	@echo ""
	@echo "Note: These tests require a detector model server running (e.g., LM Studio)"
	@echo "To run without server, use 'make test-fast' for unit tests instead."
	@echo ""
	@echo "1. Testing detect step (generates plan)..."
	python -m mdp testing/test_data/hell/inter_letter_dialogue.md --steps detect --plan .tmp/smoke_plan.json
	@echo ""
	@echo "2. Testing detect → apply workflow (should succeed)..."
	python -m mdp testing/test_data/hell/inter_letter_dialogue.md --steps detect,apply --dry-run
	@echo ""
	@echo "✓ Smoke tests complete! (Validation rejection testing available via unit tests)"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf .tmp/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.partial
	rm -rf .coverage
	rm -rf htmlcov/
	@echo "✓ Clean complete"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo ""
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo ""
	@echo "✓ Installation complete"

# Start development servers
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5174"
	@echo ""
	python launch.py

# Quick CI job (for GitHub Actions or similar)
ci-quick:
	@echo "=== Quick CI Job ==="
	@echo "1. Running fast tests..."
	python -m pytest
	@echo ""
	@echo "2. Running smoke tests..."
	$(MAKE) smoke
	@echo ""
	@echo "✓ CI quick job complete!"
