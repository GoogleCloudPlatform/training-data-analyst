# NOTE: This file is intentionally duplicated across income-verification-api, corporate-email,
# and legacy-dms rather than extracted to a shared package, to keep each demo service self-contained.
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

"""OpenTelemetry initialization for legacy-dms."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager

import google.auth
import google.auth.transport.requests
import grpc
from google.auth.transport.grpc import AuthMetadataPlugin
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.resourcedetector.gcp_resource_detector import GoogleCloudResourceDetector
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "legacy-dms")


def _get_channel_credentials() -> grpc.ChannelCredentials:
    """Create gRPC channel credentials using Application Default Credentials."""
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = google.auth.transport.requests.Request()
    return grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(AuthMetadataPlugin(credentials=credentials, request=request)),
    )


def _get_project_id() -> str:
    """Get the GCP project ID from ADC or environment."""
    _, project = google.auth.default()
    return project or os.getenv("GOOGLE_CLOUD_PROJECT", "")


def init_telemetry() -> trace.Tracer:
    """Initialize OpenTelemetry tracing, metrics, and auto-instrumentation."""
    gcp_resource = GoogleCloudResourceDetector().detect()
    project_id = _get_project_id()
    resource = Resource.create({"service.name": SERVICE_NAME, "gcp.project_id": project_id}).merge(gcp_resource)
    channel_creds = _get_channel_credentials()

    # Traces
    provider = TracerProvider(resource=resource)
    # provider.add_span_processor(
    #     BatchSpanProcessor(
    #         OTLPSpanExporter(
    #             endpoint="telemetry.googleapis.com:443",
    #             credentials=channel_creds,
    #         )
    #     )
    # )
    trace.set_tracer_provider(provider)

    # Metrics
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint="telemetry.googleapis.com:443",
            credentials=channel_creds,
        ),
        export_interval_millis=60000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    # Auto-instrument Starlette
    StarletteInstrumentor().instrument()

    return trace.get_tracer(SERVICE_NAME)


# Custom MCP metrics
_meter = metrics.get_meter(SERVICE_NAME)
tool_call_counter = _meter.create_counter("mcp.tool.calls", description="Number of MCP tool invocations")
tool_duration_histogram = _meter.create_histogram(
    "mcp.tool.duration", unit="s", description="MCP tool execution duration"
)


@contextmanager
def trace_tool(tracer: trace.Tracer, tool_name: str):
    """Context manager that creates a span and records metrics for an MCP tool call."""
    attributes = {"mcp.tool.name": tool_name}
    with tracer.start_as_current_span(f"mcp.tool.{tool_name}", attributes=attributes):
        tool_call_counter.add(1, attributes)
        start = time.monotonic()
        try:
            yield
        finally:
            tool_duration_histogram.record(time.monotonic() - start, attributes)
