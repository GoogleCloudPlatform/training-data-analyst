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

from unittest.mock import MagicMock, patch

from starlette.testclient import TestClient

# Patch telemetry before importing main to avoid GCP API calls during testing.
with patch("otel_setup.init_telemetry", return_value=MagicMock()):
    from main import _verify, app


def test_verify_known_applicant():
    result = _verify("Julian", "Sterling")
    assert result is not None
    assert result["status"] == "success"
    assert result["verification"]["applicant"]["name"] == "Julian A. Sterling"


def test_verify_unknown_applicant():
    result = _verify("Unknown", "Person")
    assert result is None


def test_verify_case_insensitive():
    result = _verify("JULIAN", "STERLING")
    assert result is not None
    assert result["status"] == "success"


# ---------------------------------------------------------------------------
# REST endpoint tests
# ---------------------------------------------------------------------------

client = TestClient(app)


def test_rest_health():
    response = client.get("/api/income-verification/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rest_verify_known_applicant():
    response = client.post(
        "/api/income-verification/verify",
        json={"first_name": "Julian", "last_name": "Sterling"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["verification"]["applicant"]["name"] == "Julian A. Sterling"


def test_rest_verify_unknown_applicant():
    response = client.post(
        "/api/income-verification/verify",
        json={"first_name": "Unknown", "last_name": "Person"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"


def test_rest_verify_case_insensitive():
    response = client.post(
        "/api/income-verification/verify",
        json={"first_name": "JULIAN", "last_name": "STERLING"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
