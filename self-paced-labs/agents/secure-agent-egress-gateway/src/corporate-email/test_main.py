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

# Patch telemetry before importing main to avoid GCP API calls during testing.
with patch("otel_setup.init_telemetry", return_value=MagicMock()):
    from main import _read, _send


def test_send_returns_status_and_message_id():
    result = _send("user@example.com", "Test Subject", "Test Body")
    assert result["status"] == "sent"
    assert "message_id" in result
    assert result["to"] == "user@example.com"
    assert result["subject"] == "Test Subject"


def test_read_returns_all_emails():
    result = _read()
    assert len(result["emails"]) == 3


def test_read_with_specific_id():
    result = _read("msg-001")
    assert len(result["emails"]) == 1
    assert result["emails"][0]["id"] == "msg-001"


def test_read_with_unknown_id():
    result = _read("msg-999")
    assert len(result["emails"]) == 0
