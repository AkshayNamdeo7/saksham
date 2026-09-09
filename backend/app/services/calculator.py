"""
Deterministic financial calculations.

EMI uses the standard mathematical formula with monthly compounding:

    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

where
    P = principal
    r = monthly interest rate (annual rate / 12 / 100)
    n = number of monthly payments

No AI is used for any financial value.
"""


def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    if annual_rate == 0:
        return principal / tenure_months
    monthly_rate = annual_rate / 12.0 / 100.0
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    return round(emi, 2)


def calculate_loan(principal, annual_rate, tenure, tenure_unit="months", moratorium_months=0):
    """
    Returns a dict with EMI, total interest, total repayment, principal and an
    amortization-like timeline.
    """
    tenure = float(tenure)
    if tenure_unit == "years":
        tenure_months = int(round(tenure * 12))
    else:
        tenure_months = int(round(tenure))
    if tenure_months < 1:
        tenure_months = 1
    moratorium = max(0, int(moratorium_months) or 0)

    if annual_rate == 0:
        emi = round(principal / tenure_months, 2)
    else:
        emi = compute_emi(principal, annual_rate, tenure_months)

    total_repayment = round(emi * tenure_months, 2)
    total_interest = round(total_repayment - principal, 2)

    timeline = _build_timeline(principal, annual_rate, tenure_months, emi)

    return {
        "principal": round(principal, 2),
        "annual_rate": round(annual_rate, 2),
        "tenure_months": tenure_months,
        "tenure_unit": "months",
        "moratorium_months": moratorium,
        "emi": emi,
        "total_interest": total_interest,
        "total_repayment": total_repayment,
        "total_payments": tenure_months,
        "effective_annual_rate": round(annual_rate, 2),
        "timeline": timeline,
    }


def load_limited_total_interest(principal, annual_rate, tenure_months):
    """Interest accrued on principal during a moratorium period (simple approx)."""
    if annual_rate == 0:
        return 0.0
    months = max(0, tenure_months)
    monthly_rate = annual_rate / 12.0 / 100.0
    return round(principal * monthly_rate * months, 2)


def _build_timeline(principal, annual_rate, tenure_months, emi, bucket_size=12):
    """Bucket the payment timeline into yearly lumps for charting."""
    remaining = principal
    monthly_rate = annual_rate / 12.0 / 100.0
    buckets = []
    year = 1
    principal_sum = 0.0
    interest_sum = 0.0
    count = 0
    for i in range(1, tenure_months + 1):
        interest = remaining * monthly_rate
        principal_part = emi - interest
        principal_part = min(principal_part, remaining)
        interest = emi - principal_part
        remaining = max(0, remaining - principal_part)
        principal_sum += principal_part
        interest_sum += interest
        count += 1
        if count == bucket_size or i == tenure_months:
            buckets.append(
                {
                    "period": f"Year {year}" if year > 0 else "Year 1",
                    "principal": round(principal_sum, 2),
                    "interest": round(interest_sum, 2),
                    "balance": round(remaining, 2),
                }
            )
            year += 1
            principal_sum = 0.0
            interest_sum = 0.0
            count = 0
    return buckets
