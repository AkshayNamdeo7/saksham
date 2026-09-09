from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import Base, engine
from app.api.routes import (
    admin_applications,
    admin_auth,
    admin_dashboard,
    admin_partners,
    admin_schemes,
    assistant,
    calculator,
    eligibility,
    partner_routing,
    partners,
    recommendations,
    schemes,
)
from app.db.seed import seed

app = FastAPI(
    title="Saksham API",
    description="AI-driven scheme matching for marginalized entrepreneurs (prototype)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    if settings.SEED_ON_STARTUP:
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()


@app.get("/")
def root():
    return {
        "name": "Saksham API",
        "version": "1.0.0",
        "docs": "/docs",
        "demo_mode": settings.DEMO_MODE,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(schemes.router, prefix="/api/schemes")
app.include_router(partners.router, prefix="/api/partners")
app.include_router(eligibility.router, prefix="/api/eligibility")
app.include_router(recommendations.router, prefix="/api/recommendations")
app.include_router(calculator.router, prefix="/api/calculator")
app.include_router(partner_routing.router, prefix="/api/partners")
app.include_router(assistant.router, prefix="/api/assistant")
app.include_router(admin_auth.router, prefix="/api/admin")
app.include_router(admin_dashboard.router, prefix="/api/admin")
app.include_router(admin_schemes.router, prefix="/api/admin/schemes")
app.include_router(admin_partners.router, prefix="/api/admin/partners")
app.include_router(admin_applications.router, prefix="/api/admin")


@app.exception_handler(Exception)
async def unhandled_exception(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )