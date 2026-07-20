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

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.tools.base import ToolResult
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.responses import JSONResponse as StarletteJSONResponse
from starlette.routing import Mount, Route

from otel_setup import init_telemetry, trace_endpoint, trace_tool

tracer = init_telemetry()

# ---------------------------------------------------------------------------
# Shared verification logic
# ---------------------------------------------------------------------------

_APPLICANTS = {
    "julian": {
        "name": "Julian A. Sterling",
        "ssn": "323-45-6789",
        "employer": "City General Hospital",
        "title": "Registered Nurse - ICU",
        "employment_status": "Active - Full Time",
        "start_date": "2018-01-10",
        "current_annual_salary": 92000,
        "year_to_date_earnings": 19200,
        "verification_date": "2026-03-13",
    },
    "elena": {
        "name": "Elena M. Sterling",
        "ssn": "321-54-9876",
        "employer": "Summit Advisory Group",
        "title": "Director of Financial Planning",
        "employment_status": "Active - Full Time",
        "start_date": "2025-11-15",
        "current_annual_salary": 98000,
        "year_to_date_earnings": 20400,
        "verification_date": "2026-03-13",
    },
}

_INCOME_SUMMARY = {
    "combined_current_salary": 190000,
    "two_year_average_agi": 174300,
    "income_trend": "INCREASING",
    "confidence": "HIGH",
}


def _verify(first_name: str, last_name: str) -> dict | None:
    """Return verification data for a known applicant, or None."""
    if last_name.lower() == "sterling" and first_name.lower() in _APPLICANTS:
        return {
            "status": "success",
            "verification": {
                "applicant": _APPLICANTS[first_name.lower()],
                "income_summary": _INCOME_SUMMARY,
                "source": "National Income Verification Database",
            },
        }
    return None


# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(name="income-verification")


@mcp.tool()
def verify_applicant(first_name: str, last_name: str) -> ToolResult:
    """Verify applicant income through third-party income verification service.

    Args:
        first_name: Applicant's first name.
        last_name: Applicant's last name.

    Returns:
        ToolResult with verified income data in structured_content.
    """
    # content=[] suppresses the duplicate raw-text representation; Model Armor's
    # CONTENT_AUTHZ only redacts structuredContent, so leaving content[] populated
    # leaks SSNs around the redactor.
    with trace_tool(tracer, "verify_applicant"):
        result = _verify(first_name, last_name) or {
            "status": "error",
            "error": f"No verification records found for {first_name} {last_name}.",
        }
        return ToolResult(content=[], structured_content=result)


# ---------------------------------------------------------------------------
# FastAPI REST app (existing endpoints)
# ---------------------------------------------------------------------------


class VerifyRequest(BaseModel):
    first_name: str
    last_name: str


PREFIX = "/income-verification"

rest_app = FastAPI(
    title="Income Verification API",
    description="Verify applicant income through third-party income verification service.",
    version="1.0.0",
)


@rest_app.get(f"{PREFIX}/health")
async def rest_health():
    return {"status": "ok"}


@rest_app.post(f"{PREFIX}/verify")
async def verify(req: VerifyRequest):
    with trace_endpoint(tracer, "verify_applicant"):
        result = _verify(req.first_name, req.last_name)
        if result:
            return result
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": f"No verification records found for {req.first_name} {req.last_name}.",
            },
        )


# ---------------------------------------------------------------------------
# Starlette app combining health, MCP, and REST
# ---------------------------------------------------------------------------


async def health(request):
    return StarletteJSONResponse({"status": "ok"})


_mcp_app = mcp.http_app(path="/mcp", stateless_http=True, json_response=True)

app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/api", app=rest_app),
        Mount("/", app=_mcp_app),
    ],
    lifespan=_mcp_app.lifespan,
)
