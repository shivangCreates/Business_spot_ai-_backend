import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.inquiries import create_inquiry
from app.main import app, health, root
from app.schemas.inquiry import InquiryCreate, InquiryResponse


class InquirySchemaTests(unittest.TestCase):
    def test_strips_required_text_and_normalizes_empty_company(self):
        inquiry = InquiryCreate.model_validate(
            {
                "name": "  Ada Lovelace  ",
                "email": "ada@example.com",
                "company": "   ",
                "project_type": "  Consulting  ",
                "message": "  Please contact me soon.  ",
            }
        )

        self.assertEqual(inquiry.name, "Ada Lovelace")
        self.assertIsNone(inquiry.company)
        self.assertEqual(inquiry.project_type, "Consulting")
        self.assertEqual(inquiry.message, "Please contact me soon.")

    def test_rejects_whitespace_only_required_text(self):
        valid_payload = {
            "name": "Ada",
            "email": "ada@example.com",
            "project_type": "Consulting",
            "message": "Please contact me soon.",
        }

        for field in ("name", "project_type", "message"):
            with self.subTest(field=field):
                payload = {**valid_payload, field: "   "}
                with self.assertRaises(ValidationError):
                    InquiryCreate.model_validate(payload)


class HealthTests(unittest.TestCase):
    def test_inquiry_route_is_registered(self):
        self.assertIn("/api/v1/inquiries", app.openapi()["paths"])
        self.assertIn(
            "post",
            app.openapi()["paths"]["/api/v1/inquiries"],
        )

    def test_root_route(self):
        self.assertEqual(root(), {"message": "Business Spot AI API is running"})

    def test_health_reports_database_readiness(self):
        db = Mock()

        self.assertEqual(health(db), {"status": "ok", "database": "ok"})
        db.execute.assert_called_once()

    def test_health_returns_service_unavailable_when_database_fails(self):
        db = Mock()
        db.execute.side_effect = SQLAlchemyError("database unavailable")

        with self.assertLogs("app.main", level="WARNING"):
            with self.assertRaises(HTTPException) as raised:
                health(db)

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Database unavailable")


class InquiryRouteTests(unittest.TestCase):
    def test_create_inquiry_persists_and_returns_record(self):
        db = Mock()
        db.refresh.side_effect = lambda inquiry: (
            setattr(inquiry, "id", 1),
            setattr(inquiry, "status", "new"),
            setattr(inquiry, "created_at", datetime.now(timezone.utc)),
        )
        inquiry_data = InquiryCreate.model_validate(
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "project_type": "Consulting",
                "message": "Please contact me soon.",
            }
        )

        result = create_inquiry(inquiry_data, db)
        response = InquiryResponse.model_validate(result)

        self.assertEqual(response.id, 1)
        self.assertEqual(response.email, "ada@example.com")
        self.assertEqual(response.status, "new")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_create_inquiry_rolls_back_on_database_error(self):
        db = Mock()
        db.commit.side_effect = SQLAlchemyError("database unavailable")
        inquiry_data = InquiryCreate.model_validate(
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "project_type": "Consulting",
                "message": "Please contact me soon.",
            }
        )

        with self.assertRaises(HTTPException) as raised:
            create_inquiry(inquiry_data, db)

        self.assertEqual(raised.exception.status_code, 500)
        db.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
