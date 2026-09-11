"""
myScheme.gov.in adapter.

myScheme (https://www.myscheme.gov.in/) is the Government of India's official
scheme discovery portal. It is treated here as a *discovery/application-route*
source rather than a scheme provider:

- PM-SURAJ (https://pmsuraj.dosje.gov.in/) is the online application portal for
  NSFDC concessional credit, not a standalone scheme. It is surfaced as the
  official_apply_url on each NSFDC record instead of as a scheme row.
- Direct, verified programme-level scheme records live in
  government_sources.py.

This adapter therefore returns no scheme records; it exists so the importer
pipeline stays stable and any PM-SURAJ-related records that may pre-exist in a
local database are de-activated as legacy slugs.
"""

from app.services.scheme_sources.base import NormalizedScheme, SchemeSourceAdapter

MSCHEME_URL = "https://www.myscheme.gov.in/"


class MySchemeAdapter(SchemeSourceAdapter):
    source_name = "myScheme"

    def fetch(self) -> list[NormalizedScheme]:
        # See module docstring: PM-SURAJ is the application route for NSFDC
        # schemes (official_apply_url), not a separate scheme record.
        return []