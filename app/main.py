
import logging
from contextlib import asynccontextmanager
from sqlalchemy import select, text

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import Base, engine, get_db
# Import registers the mapped table before metadata.create_all runs.
from app.models.inquiry import Inquiry
from app.api.routes.inquiries import router as inquiries_router


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.debug("Starting %s", _app.title)
    logger.debug("Loaded inquiry model for table %s", Inquiry.__tablename__)
    print("Registered tables:", list(Base.metadata.tables.keys()))

    with engine.connect() as conn:
        db_name = conn.execute(
            text("SELECT current_database()")
        ).scalar()
        print("Connected database:", db_name)

    Base.metadata.create_all(bind=engine)
    print("Table creation check completed.")

    yield



app = FastAPI(
    title="Business Spot AI API",
    description="Backend API for Business Spot AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
def root():
    return {"message": "Business Spot AI API is running"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        logger.warning("Database health check failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "ok", "database": "ok"}


app.include_router(inquiries_router)
