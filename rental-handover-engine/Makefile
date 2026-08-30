# Rental Handover Engine
#
# Single-command setup, single-command run, single-command proof.
# Everything runs locally. Nothing here opens a socket.

PYTHON ?= python3
RHE    := $(PYTHON) -m rhe.l6_cli.main

.DEFAULT_GOAL := help
.PHONY: help setup run scenarios demo classify tiers rulesets test golden golden-update prove bench verify clean

help:  ## show this help
	@echo "Rental Handover Engine"
	@echo ""
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-16s %s\n", $$1, $$2}'
	@echo ""
	@echo "  Start here:  make setup && make demo"

setup:  ## install the two dependencies (PyYAML, pytest)
	$(PYTHON) -m pip install --quiet -r requirements.txt
	@echo "ready. try: make demo"

demo:  ## run the flagship scenario (a Tier 1 rental with no humans in it)
	@$(RHE) run 01_tier1_clean

run:  ## run every scenario, in order
	@$(RHE) run all

scenarios:  ## list the built-in scenarios
	@$(RHE) scenarios

classify:  ## classify every leaf category and show the winning rule row
	@$(RHE) classify --all

tiers:  ## show the five tiers and the handover choreography of each
	@$(RHE) tiers

rulesets:  ## list every L0 ruleset file, its version and its hash
	@$(RHE) rulesets

test:  ## run the full test suite
	@$(PYTHON) -m pytest tests/ -q

golden:  ## compare every scenario against its golden file
	@$(RHE) golden

golden-update:  ## rewrite the golden files (review the diff before committing)
	@$(RHE) golden --update

prove:  ## enumerate the classifier's full input space and prove it is total
	@$(PYTHON) tools/prove_exhaustiveness.py

bench:  ## re-render the 34-item classification bench artifact
	@$(PYTHON) tools/render_item_bench.py

verify: ## THE BAR: golden files, replay from zero, exhaustiveness proof, every scenario twice
	@echo "== 1/5  classifier exhaustiveness proof =="
	@$(PYTHON) tools/prove_exhaustiveness.py
	@echo ""
	@echo "== 2/5  item classification bench =="
	@$(PYTHON) tools/render_item_bench.py
	@echo ""
	@echo "== 3/5  golden file comparison =="
	@$(RHE) golden
	@echo ""
	@echo "== 4/5  in-process determinism, every scenario run twice =="
	@$(RHE) verify-determinism
	@echo ""
	@echo "== 5/5  acceptance bar: suite twice byte-for-byte, plus replay from zero =="
	@$(PYTHON) tools/verify_acceptance.py
	@echo ""
	@echo "== test suite =="
	@$(PYTHON) -m pytest tests/ -q

clean:  ## remove caches and any stray projection databases
	@find . -name __pycache__ -type d -prune -exec rm -rf {} +
	@find . -name '*.sqlite3' -delete
	@rm -rf .pytest_cache
	@echo "cleaned"
