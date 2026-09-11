from __future__ import annotations

from .action_bundle import ActionBundle
from .compiler import CompileResult


def bundle_from_compiled(compiled: CompileResult) -> ActionBundle | None:
    """Turn a compiler result into a validated transaction without dispatching."""
    if not compiled.actions:
        return None
    intent_kind = compiled.actions[-1].meta("semantic_kind") or "unknown"
    bundle = ActionBundle(intent_kind, tuple(compiled.actions))
    bundle.validate()
    return bundle
