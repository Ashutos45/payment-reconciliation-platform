from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.logger import logger
from app.db.database import Base, engine
from app.api import upload, reconcile, results, exceptions, export, metrics

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production-grade backend for Payment Reconciliation Platform"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(upload.router, prefix=settings.API_V1_STR, tags=["Upload"])
app.include_router(reconcile.router, prefix=settings.API_V1_STR, tags=["Reconciliation"])
app.include_router(results.router, prefix=settings.API_V1_STR, tags=["Results"])
app.include_router(exceptions.router, prefix=settings.API_V1_STR, tags=["Exceptions"])
app.include_router(export.router, prefix=settings.API_V1_STR, tags=["Export"])
app.include_router(metrics.router, prefix=settings.API_V1_STR, tags=["Metrics"])

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application and setting up database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

@app.get("/")
def read_root():
    """Root endpoint verifying API is running."""
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    logger.info("Starting up FastAPI application")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)