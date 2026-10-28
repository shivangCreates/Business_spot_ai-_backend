
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryCreate, InquiryResponse

router = APIRouter(
    prefix="/api/v1/inquiries",
    tags=["Inquiries"],
)


@router.post(
    "",
    response_model=InquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inquiry(
    inquiry_data: InquiryCreate,
    db: Session = Depends(get_db),
):
    inquiry = Inquiry(
        name=inquiry_data.name,
        email=str(inquiry_data.email),
        company=inquiry_data.company,
        project_type=inquiry_data.project_type,
        message=inquiry_data.message,
    )

    try:
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        return inquiry

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save your inquiry. Please try again.",
        )
