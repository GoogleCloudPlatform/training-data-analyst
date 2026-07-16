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

# Patch telemetry before importing server to avoid GCP API calls during testing.
with patch("otel_setup.init_telemetry", return_value=MagicMock()):
    from server import _get_document, _search_documents


def test_search_by_name_and_doc_type():
    result = _search_documents(applicant_last_name="Sterling", document_type="tax_return")
    assert result["status"] == "success"
    assert result["total_results"] > 0


def test_search_unknown_applicant():
    result = _search_documents(applicant_last_name="Unknown", document_type="tax_return")
    assert result["status"] == "success"
    assert result["total_results"] == 0


def test_get_document_by_id():
    result = _get_document(document_id="DOC-2024-SM-1040")
    assert result["status"] == "success"
    assert result["document"]["document_id"] == "DOC-2024-SM-1040"


def test_get_document_not_found():
    result = _get_document(document_id="DOC-NONEXISTENT")
    assert result["status"] == "error"
