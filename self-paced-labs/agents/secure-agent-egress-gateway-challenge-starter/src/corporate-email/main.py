# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid
from datetime import datetime, timezone

from fastmcp import FastMCP
from fastmcp.tools.base import ToolResult
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from otel_setup import init_telemetry, trace_tool

tracer = init_telemetry()

# ---------------------------------------------------------------------------
# Email data and helpers
# ---------------------------------------------------------------------------


SAMPLE_EMAILS = [
    {
        "id": "msg-001",
        "from": "underwriting@megabank.com",
        "to": "loan-officers@megabank.com",
        "subject": "Mortgage Application #2024-7891 - Documents Received",
        "body": (
            "All required documents for application #2024-7891 (Johnson, Sarah) have been received. "
            "Tax returns, pay stubs, and bank statements are now in the document management system. "
            "Please proceed with income verification."
        ),
        "timestamp": "2025-06-15T09:30:00Z",
        "read": True,
    },
    {
        "id": "msg-002",
        "from": "compliance@megabank.com",
        "to": "loan-officers@megabank.com",
        "subject": "Updated DTI Ratio Guidelines - Effective July 1",
        "body": (
            "Please note that maximum debt-to-income ratio thresholds have been updated for conforming loans. "
            "The new maximum DTI is 45% (previously 43%). Refer to compliance bulletin CB-2025-12 for details."
        ),
        "timestamp": "2025-06-14T14:15:00Z",
        "read": False,
    },
    {
        "id": "msg-003",
        "from": "appraisals@megabank.com",
        "to": "loan-officers@megabank.com",
        "subject": "Appraisal Complete - 742 Evergreen Terrace",
        "body": (
            "The appraisal for 742 Evergreen Terrace has been completed. Appraised value: $485,000. "
            "This supports the requested loan amount of $388,000 (80% LTV). Full report attached to the loan file."
        ),
        "timestamp": "2025-06-13T11:45:00Z",
        "read": True,
    },
]


def _send(to: str, subject: str, body: str) -> dict:
    """Simulate sending an email and return a mock success response."""
    return {
        "status": "sent",
        "message_id": str(uuid.uuid4()),
        "to": to,
        "subject": subject,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _read(email_id: str | None = None) -> dict:
    """Read emails from the inbox. Optionally filter by email ID."""
    if email_id:
        for email in SAMPLE_EMAILS:
            if email["id"] == email_id:
                return {"emails": [email]}
        return {"emails": [], "message": f"No email found with ID {email_id}"}
    return {"emails": SAMPLE_EMAILS}


# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(name="corporate-email")


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> ToolResult:
    """Send an email through the corporate email system.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body content.

    Returns:
        ToolResult with send status, message ID, and timestamp in structured_content.
    """
    # content=[] suppresses the duplicate raw-text representation; Model Armor's
    # CONTENT_AUTHZ only redacts structuredContent, so leaving content[] populated
    # leaks sensitive fields around the redactor.
    with trace_tool(tracer, "send_email"):
        return ToolResult(content=[], structured_content=_send(to, subject, body))


@mcp.tool()
def read_email(email_id: str | None = None) -> ToolResult:
    """Read emails from the corporate inbox. This is a read-only operation.

    Args:
        email_id: Optional email ID to fetch a specific email. If not provided,
                  returns all emails in the inbox.

    Returns:
        ToolResult with a list of email messages in structured_content.
    """
    with trace_tool(tracer, "read_email"):
        return ToolResult(content=[], structured_content=_read(email_id))


# ---------------------------------------------------------------------------
# Starlette app with health endpoint + FastMCP mount
# ---------------------------------------------------------------------------


async def health(request):
    return JSONResponse({"status": "ok"})


_mcp_app = mcp.http_app(path="/mcp", stateless_http=True, json_response=True)

app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/", app=_mcp_app),
    ],
    lifespan=_mcp_app.lifespan,
)
