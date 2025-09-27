from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models.database import create_tables
from app.api import due_diligence, entities, reports, admin
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
create_tables()
logger.info("Database tables created successfully")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

    return response

# CORS middleware
logger.info(f"CORS origins configured: {settings.BACKEND_CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    due_diligence.router,
    prefix=f"{settings.API_V1_STR}/due-diligence",
    tags=["due-diligence"]
)
logger.info(f"Due diligence router included at {settings.API_V1_STR}/due-diligence")

app.include_router(
    entities.router,
    prefix=f"{settings.API_V1_STR}/entities",
    tags=["entities"]
)
logger.info(f"Entities router included at {settings.API_V1_STR}/entities")

app.include_router(
    reports.router,
    prefix=f"{settings.API_V1_STR}/reports",
    tags=["reports"]
)
logger.info(f"Reports router included at {settings.API_V1_STR}/reports")

app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["admin"]
)
logger.info(f"Admin router included at {settings.API_V1_STR}/admin")

@app.get("/")
async def root():
    return {"message": "Legal Entity Due Diligence API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)