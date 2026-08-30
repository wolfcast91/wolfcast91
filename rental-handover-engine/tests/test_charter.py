"""The determinism charter, enforced against the source tree itself.

A rule that only lives in a document is a rule that erodes. These tests read the
actual code and fail the build if the charter is violated -- which is the only
way "no randomness anywhere" stays true six months from now.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

PACKAGE = "rhe"

# Modules permitted to touch the real world. Everything else is pure.
CLOCK_ADAPTER = "rhe/l5_adapters/clock.py"

BANNED_IMPORTS = {
    "random": "charter rule 1: no randomness anywhere",
    "secrets": "charter rule 1: no randomness anywhere",
    "uuid": "charter rule 1: ids are content hashes or monotonic counters",
    "socket": "charter rule 9: no network in any decision path",
    "http": "charter rule 9: no network in any decision path",
    "urllib": "charter rule 9: no network in any decision path",
    "requests": "charter rule 9: no network in any decision path",
    "asyncio": "charter rule 9: no I/O in the decision path",
}


def _python_files(root: pathlib.Path, subpath: str = PACKAGE):
    return sorted((root / subpath).rglob("*.py"))


def _parsed(root: pathlib.Path, subpath: str = PACKAGE):
    for path in _python_files(root, subpath):
        yield path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_no_banned_module_is_imported_anywhere(root):
    offences = []
    for path, tree in _parsed(root):
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                if name in BANNED_IMPORTS:
                    offences.append(f"{path.relative_to(root)}:{node.lineno} imports {name} "
                                    f"({BANNED_IMPORTS[name]})")
    assert not offences, "\n".join(offences)


def test_only_the_clock_adapter_reads_a_clock(root):
    """No hidden clock reads: datetime.now / time.time live in exactly one file."""
    offences = []
    for path, tree in _parsed(root):
        relative = path.relative_to(root).as_posix()
        if relative == CLOCK_ADAPTER:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("now", "utcnow", "today", "time"):
                source = ast.unparse(node)
                if any(token in source for token in ("datetime", "date.", "time.")):
                    offences.append(f"{relative}:{node.lineno} reads a clock: {source}")
    assert not offences, (
        "time must enter through the injected Clock interface only\n" + "\n".join(offences))


def test_the_pure_kernel_contains_no_float_literals(root):
    """Charter rule 3: money in integer cents, scores as integers, percentages
    as basis points. A float literal in L1 is a bug by definition."""
    offences = []
    for path, tree in _parsed(root, f"{PACKAGE}/l1_kernel"):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                offences.append(f"{path.relative_to(root)}:{node.lineno} float literal {node.value}")
    assert not offences, "\n".join(offences)


def test_the_pure_kernel_uses_no_true_division(root):
    """`/` produces a float. Every division in the kernel must be `//`."""
    offences = []
    for path, tree in _parsed(root, f"{PACKAGE}/l1_kernel"):
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                offences.append(f"{path.relative_to(root)}:{node.lineno} uses / instead of //")
    assert not offences, "\n".join(offences)


def test_the_pure_kernel_does_not_import_upward(root):
    """Strict downward dependency: L1 may read L0 and nothing above it."""
    allowed = {"rhe.canonical", "rhe.l0_rules", "rhe.l1_kernel"}
    offences = []
    for path, tree in _parsed(root, f"{PACKAGE}/l1_kernel"):
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = node.names[0].name
            if module and module.startswith("rhe.") and not any(
                module == a or module.startswith(a + ".") for a in allowed
            ):
                offences.append(f"{path.relative_to(root)}:{node.lineno} imports {module}")
    assert not offences, "L1 must not call upward\n" + "\n".join(offences)


def test_the_kernel_does_not_open_files_or_databases(root):
    offences = []
    for path, tree in _parsed(root, f"{PACKAGE}/l1_kernel"):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                offences.append(f"{path.relative_to(root)}:{node.lineno} opens a file")
    assert not offences, "\n".join(offences)


def test_no_ansi_escape_codes_in_rendered_output(root):
    """A terminal colour setting must never change the bytes a scenario emits."""
    for path in _python_files(root, f"{PACKAGE}/l6_cli") + _python_files(root, "sim"):
        assert "\\x1b[" not in path.read_text(encoding="utf-8"), path


def test_every_ruleset_file_declares_a_version(ruleset):
    for stem, version in ruleset.versions.items():
        assert isinstance(version, int), stem


def test_thresholds_do_not_appear_as_literals_below_l0(root, ruleset):
    """Spot-check: the specific integers the rulesets own must not be hardcoded
    in the kernel. If a threshold moves in YAML, no code change should be needed."""
    # Only distinctive values are listed. A number like 1000 or 100 appears
    # legitimately as a grid precision or a percentage base, so including it
    # would make this test noise rather than signal.
    owned = {
        "6000": "complementary_items.thresholds.cumulative_spend_bp",
        "604800": "state_transitions.guard_parameters.lost_grace_seconds",
        "15552000": "complementary_items.thresholds.window_seconds",
        "3600": "state_transitions.guard_parameters.overdue_grace_seconds",
    }
    offences = []
    for path, tree in _parsed(root, f"{PACKAGE}/l1_kernel"):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, int):
                literal = str(node.value)
                if literal in owned:
                    offences.append(
                        f"{path.relative_to(root)}:{node.lineno} hardcodes {literal}, "
                        f"which belongs to {owned[literal]}")
    assert not offences, "\n".join(offences)
