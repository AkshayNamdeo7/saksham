from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent, LoanCalculation
from app.schemas.schemas import LoanCalcRequest
from app.services.calculator import calculate_loan

router = APIRouter(tags=["calculator"])


@router.post("/emi")
def calculate_emi(payload: LoanCalcRequest, db: Session = Depends(get_db)):
    result = calculate_loan(
        principal=payload.principal,
        annual_rate=payload.annual_rate,
        tenure=payload.tenure,
        tenure_unit=payload.tenure_unit,
        moratorium_months=payload.moratorium_months,
    )
    warnings = []
    if payload.scheme_max_loan is not None and payload.principal > payload.scheme_max_loan:
        warnings.append(
            f"Requested amount (₹{payload.principal:,.0f}) exceeds the configured scheme "
            f"maximum of ₹{payload.scheme_max_loan:,.0f} (demo)."
        )
    result["warnings"] = warnings

    db.add(
        LoanCalculation(
            principal=result["principal"],
            annual_rate=result["annual_rate"],
            tenure_months=result["tenure_months"],
            moratorium_months=result["moratorium_months"],
            emi=result["emi"],
            total_interest=result["total_interest"],
            total_repayment=result["total_repayment"],
        )
    )
    db.add(AuditEvent(event_type="loan_calculation", payload=f"p={payload.principal}"))
    db.commit()
    return result