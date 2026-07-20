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

"""Thin AdkApp subclass that relies on Agent Engine's default telemetry pipeline."""

from __future__ import annotations

from vertexai.agent_engines import AdkApp


class InstrumentedAdkApp(AdkApp):
    """AdkApp that uses the default Agent Engine telemetry pipeline.

    The default _default_instrumentor_builder() sets up:
    - TracerProvider with OTLP export to telemetry.googleapis.com/v1/traces
    - GenAI SDK instrumentation
    - Proper resource attributes for Agent Engine dashboard

    ADK already creates semantic spans (execute_tool, tools/call, call_llm)
    for agent operations, so no additional HTTP-level instrumentation is needed.
    """
