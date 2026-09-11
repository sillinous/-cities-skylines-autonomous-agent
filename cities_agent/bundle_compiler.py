from __future__ import annotations

from .action_bundle import ActionBundle
from .compiler import CompiledIntent


def bundle_from_compiled(compiled: CompiledIntent) -> ActionBundle | None:
    """Convert a compiled semantic intent into a validated transactional bundle."""
    if not compiled.actions:
        return None
    intent_kind = compiled.actions[-1].meta("semantic_kind") or "unknown"
    bundle = ActionBundle(intent_kind, tuple(compiled.actions))
    bundle.validate()
    return bundle
