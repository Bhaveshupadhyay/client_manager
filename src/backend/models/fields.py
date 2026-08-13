"""
Cosmos DB JSON Patch paths derived from Pydantic models.

Instead of hardcoding strings like '/extracted_facts/client_budget',
use ProjectFields.extracted_facts.client_budget which resolves to the
same path but stays in sync with the model automatically.

If a field is renamed in ExtractedFacts or ProjectItem, the attribute
access here will raise an AttributeError at import time — not a silent
runtime bug.

Usage:
    from backend.models.fields import ProjectFields

    await repo.update_single_project_field(
        project_id="pid_123",
        field=ProjectFields.extracted_facts.estimated_cost,
        new_value=75000.0
    )
"""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.client import ProjectItem


class _PatchPath:
    """
    A descriptor that builds a Cosmos DB JSON Patch path (RFC 6902)
    from the Pydantic model's field names.

    Accessing an attribute returns a new _PatchPath with the
    accumulated path segments. Calling str() or using it where a
    string is expected yields the '/'-prefixed path.
    """

    def __init__(self, segments: tuple[str, ...] = (), model: type[BaseModel] | None = None):
        self._segments = segments
        self._model = model

    def __getattr__(self, name: str) -> _PatchPath:
        # Validate that the field actually exists on the Pydantic model.
        if self._model is not None:
            fields = self._model.model_fields
            if name not in fields:
                raise AttributeError(
                    f"'{self._model.__name__}' has no field '{name}'. "
                    f"Valid fields: {list(fields.keys())}"
                )
            # Resolve the child model (if it's another BaseModel) so
            # chained access like ProjectFields.extracted_facts.client_budget
            # validates every segment.
            child_annotation = fields[name].annotation
            child_model = None
            if isinstance(child_annotation, type):
                from pydantic import BaseModel
                if issubclass(child_annotation, BaseModel):
                    child_model = child_annotation
        else:
            child_model = None

        return _PatchPath(self._segments + (name,), model=child_model)

    # --- String / repr ---------------------------------------------------

    @property
    def path(self) -> str:
        """Return the full JSON Patch path, e.g. '/extracted_facts/client_budget'."""
        return "/" + "/".join(self._segments)

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"PatchPath({self.path!r})"

    # Allow direct comparison with strings for convenience in tests
    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.path == other
        if isinstance(other, _PatchPath):
            return self._segments == other._segments
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._segments)


# ── Public API ────────────────────────────────────────────────────────────

ProjectFields = _PatchPath(model=ProjectItem)
"""
Type-safe accessor for ProjectItem JSON Patch paths.

Examples:
    str(ProjectFields.extracted_facts.client_budget)
    # → '/extracted_facts/client_budget'

    str(ProjectFields.extracted_facts.estimated_cost)
    # → '/extracted_facts/estimated_cost'

    str(ProjectFields.project_id)
    # → '/project_id'
"""
