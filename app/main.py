from fastapi import FastAPI
from app.database import init_db
from app.routers import operators, sources, contacts, leads, stats

app = FastAPI(
    title="Mini-CRM Lead Distribution System",
    description="A mini-CRM system for distributing leads between operators by sources",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Include routers
app.include_router(operators.router)
app.include_router(sources.router)
app.include_router(contacts.router)
app.include_router(leads.router)
app.include_router(stats.router)


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Mini-CRM Lead Distribution System",
        "docs": "/docs",
        "version": "1.0.0"
    }

