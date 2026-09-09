"""
Core business-logic tests (fast, no HTTP).

Run with: pytest backend/tests -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.calculator import calculate_loan, compute_emi
from app.services.partner_routing import haversine

from app.services.assistant_handler import extract_profile_from_text as _extract


def test_zero_interest_emi():
    assert compute_emi(120000, 0, 12) == 10000.0


def test_known_emi():
    # P=1,00,000 @10% annual, 12 months -> EMI ~ 8,791.59
    emi = compute_emi(100000, 10, 12)
    assert abs(emi - 8791.59) < 0.1


def test_calculate_loan_shape():
    result = calculate_loan(140000, 4.0, 36, "months", 0)
    assert result["emi"] > 0
    assert result["total_repayment"] == round(result["emi"] * 36, 2)
    assert result["total_interest"] >= 0
    assert len(result["timeline"]) >= 3


def test_years_conversion():
    result = calculate_loan(100000, 6, 5, "years", 0)
    assert result["tenure_months"] == 60


def test_moratorium_flag():
    result = calculate_loan(100000, 6, 12, "months", 3)
    assert result["moratorium_months"] == 3


def test_haversine_bhopal():
    d = haversine(23.2599, 77.4126, 23.2547, 77.4029)
    assert d is not None and 0 < d < 2


def test_extract_profile_dairy():
    extracted = _extract("Mujhe 1 lakh dairy business ke liye loan chahiye")
    assert extracted.get("purpose") == "business"
    assert extracted.get("requested_loan") == 100000
    assert extracted.get("project_type") == "dairy"