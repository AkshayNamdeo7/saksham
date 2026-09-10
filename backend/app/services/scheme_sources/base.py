"""
Scheme source adapter base.

External official scheme sources (myScheme, NSFDC, NBCFDC, state portals)
are normalized into the internal Scheme model through this interface.

The core matching engine reads from the local normalized cache only — it
never calls an external site on a user click. A periodic import job can call
each adapter to refresh the cache.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class NormalizedScheme:
    """Canonical record produced by a source adapter."""

    name: str
    slug: str
    description: str
    category: str
    purpose: str
    max_loan: float | None = None
    min_loan: float | None = None
    interest_rate: float | None = None
    tenure_months: int | None = None
    moratorium_months: int | None = None
    income_threshold: float | None = None
    project_min: float | None = None
    project_max: float | None = None
    education_focus: bool = False
    eligibility_notes: str = ""
    required_documents: str = ""
    partner_required: bool = True
    source_name: str = ""
    source_url: str = ""
    official_scheme_url: str = ""
    official_apply_url: str | None = None
    last_verified: str = ""
    source_type: str = "official_government"
    verification_status: str = "verified"
    is_demo: bool = False
    rules: list[tuple[str, str, str]] = field(default_factory=list)
    document_keys: list[str] = field(default_factory=list)


class SchemeSourceAdapter(ABC):
    """Base class for all official-source adapters."""

    source_name = "official"

    def __init__(self) -> None:
        self._cache: list[NormalizedScheme] | None = None

    @abstractmethod
    def fetch(self) -> list[NormalizedScheme]:
        """Fetch and normalize records from the source. Must be idempotent."""

    def get_all(self, refresh: bool = False) -> list[NormalizedScheme]:
        if refresh or self._cache is None:
            self._cache = self.fetch()
        return self._cache

    def get_by_slug(self, slug: str, refresh: bool = False) -> NormalizedScheme | None:
        for s in self.get_all(refresh=refresh):
            if s.slug == slug:
                return s
        return None