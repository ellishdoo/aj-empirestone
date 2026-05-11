import csv
import io
import os
from dotenv import load_dotenv
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.database import get_connection, init_db
from app.email_utils import send_lead_notification

load_dotenv()


app = FastAPI(
    title="AJ Empirestone Backend",
    description="Backend API for AJ Empirestone quote requests.",
    version="1.0.0"
)

# CORS allows your frontend website to talk to this backend.
# For now, we allow local development origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_KEY = os.getenv("ADMIN_KEY", "dev-secret-key")


@app.on_event("startup")
def on_startup():
    init_db()


class LeadCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=7)
    email: Optional[str] = None
    project_city: Optional[str] = None
    project_type: Optional[str] = None
    message: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {
        "ok": True,
        "message": "AJ Empirestone backend is running"
    }


@app.post("/api/leads")
def create_lead(lead: LeadCreate):
    """
    Receives a quote request and saves it to the SQLite database.
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO leads (
                        full_name,
                        phone,
                        email,
                        project_city,
                        project_type,
                        message
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        lead.full_name.strip(),
                        lead.phone.strip(),
                        lead.email.strip() if lead.email else None,
                        lead.project_city.strip() if lead.project_city else None,
                        lead.project_type.strip() if lead.project_type else None,
                        lead.message.strip() if lead.message else None,
                    )
                )

                lead_id = cursor.fetchone()["id"]

            conn.commit()

        email_sent = send_lead_notification(lead_id, lead)

        return {
            "ok": True,
            "message": "Quote request submitted successfully.",
            "lead_id": lead_id
        }

    except Exception as error:
        print("Error creating lead:", error)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while saving the quote request."
        )
    
@app.get("/api/leads")
def get_leads(admin_key: str = Query(...)):
    """
    Returns all quote requests.
    Protected by a simple admin key for now.
    """

    if admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        full_name,
                        phone,
                        email,
                        project_city,
                        project_type,
                        message,
                        status,
                        created_at
                    FROM leads
                    ORDER BY created_at DESC
                    """
                )

                rows = cursor.fetchall()

        leads = [dict(row) for row in rows]

        return {
            "ok": True,
            "count": len(leads),
            "leads": leads
        }

    except Exception as error:
        print("Error reading leads:", error)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while reading quote requests."
        )
    
@app.get("/api/leads/export")
def export_leads(admin_key: str = Query(...)):
    """
    Exports all quote requests as a CSV file.
    Protected by the same simple admin key.
    """

    if admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        full_name,
                        phone,
                        email,
                        project_city,
                        project_type,
                        message,
                        status,
                        created_at
                    FROM leads
                    ORDER BY created_at DESC
                    """
                )

                rows = cursor.fetchall()

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow([
            "ID",
            "Full Name",
            "Phone",
            "Email",
            "Project City",
            "Project Type",
            "Message",
            "Status",
            "Created At"
        ])

        for row in rows:
            writer.writerow([
                row["id"],
                row["full_name"],
                row["phone"],
                row["email"],
                row["project_city"],
                row["project_type"],
                row["message"],
                row["status"],
                row["created_at"]
            ])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=aj_empirestone_leads.csv"
            }
        )

    except Exception as error:
        print("Error exporting leads:", error)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while exporting quote requests."
        )