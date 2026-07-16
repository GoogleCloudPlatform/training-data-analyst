# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import subprocess
from urllib.parse import urlparse

from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
    PREV_AGENT_CARD_WELL_KNOWN_PATH
)
from google.adk.agents.remote_a2a_agent import DEFAULT_TIMEOUT
from google.auth.transport.requests import AuthorizedSession, Request
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.credentials import Credentials
from google.oauth2.id_token import fetch_id_token_credentials
import httpx
from starlette.datastructures import URL
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response


async def a2a_card_dispatch(
        request: StarletteRequest,
        call_next: RequestResponseEndpoint
) -> Response:
    """Handles requests for A2A Agent Cards by making sure
       the agent URL's protocol, and netloc are the same as in the card's
       request.

    Args:
        request (Request): HTTP Request.
        call_next (RequestResponseEndpoint): original handler to call.

    Returns:
        Response: HTTP Response
    """
    response = await call_next(request)
    if (
        response.status_code == 200
        and (
            request.url.path.endswith(AGENT_CARD_WELL_KNOWN_PATH)
            or request.url.path.endswith(PREV_AGENT_CARD_WELL_KNOWN_PATH)
            or request.url.path.endswith(EXTENDED_AGENT_CARD_PATH)
        )
    ):
        body = b""
        if hasattr(response, "body_iterator"):
            async for chunk in response.body_iterator: # type: ignore
                if isinstance(chunk, str):
                    chunk = chunk.encode(response.charset)
                body += chunk
        else:
            body = response.body
        if isinstance(body, memoryview):
            body = body.tobytes()
        body = body.decode(response.charset)
        card = json.loads(body)
        agent_url = URL(card["url"])

        headers = request.headers
        host = headers.get("x-forwarded-host", request.url.hostname)
        scheme = headers.get(
            "x-forwarded-proto",
            request.url.scheme or "http"
        ).lower()
        port = headers.get("x-forwarded-port", request.url.port)
        if port:
            if (
                scheme == "http" and port == "80"
            ) or (
                scheme == "https" and port == "443"
            ):
                port = None

        agent_url = agent_url.replace(
            scheme=scheme,
            hostname=host,
            port=port,
        )
        card["url"] = str(agent_url)
        response_headers = response.headers
        del response_headers["content-length"] # Content length will be recalculated
        response = Response(
            json.dumps(card).encode(response.charset),
            media_type="application/json",
            headers=response_headers,
        )
    return response


def create_authenticated_client(
        remote_service_url: str,
        timeout: float = DEFAULT_TIMEOUT
    ) -> httpx.AsyncClient:
    """Creates an httpx.AsyncClient with Google identity token authentication.
    Identity tokens are obtained:
      - If running in Cloud, from Compute Metadata server
      - If running locally, from gcloud CLI

    Args:
        remote_service_url (str): URL of the service to authenticate requests to.
        timeout (float, optional): Request timeout. Defaults to DEFAULT_TIMEOUT.

    Returns:
        httpx.AsyncClient: httpx Client with Google identity token authentication.
    """

    class _IdentityTokenAuth(httpx.Auth):
        requires_request_body = False

        def __init__(self, remote_service_url: str):
            parsed_url = urlparse(remote_service_url)
            self.root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            self.session = None

        def auth_flow(self, request):
            if self.session:
                id_token = self.session.credentials.token
            else:
                id_token = None
                try:
                    credentials = fetch_id_token_credentials(
                        audience=self.root_url,
                    )
                    credentials.refresh(Request())
                    self.session = AuthorizedSession(
                        credentials
                    )
                    id_token = self.session.credentials.token
                except DefaultCredentialsError:
                    self.outside_cloud = True
                if not id_token:
                    # Local run, fetching authenticated user's identity token
                    # from gcloud CLI
                    try:
                        id_token = subprocess.check_output(
                            [
                                "gcloud",
                                "auth",
                                "print-identity-token",
                                "-q"
                            ]
                        ).decode().strip()
                        if id_token:
                            refresh_token = subprocess.check_output(
                                [
                                    "gcloud",
                                    "auth",
                                    "print-refresh-token",
                                    "-q"
                                ]
                            ).decode().strip()
                            credentials = Credentials(
                                token=id_token,
                                id_token=id_token,
                                refresh_token=refresh_token
                            )
                            self.session = AuthorizedSession(
                                credentials
                            )
                    except subprocess.SubprocessError:
                        print("ERROR: Unable to fetch identity token.")
            if id_token:
                request.headers["Authorization"] = f"Bearer {id_token}"
            yield request

    return httpx.AsyncClient(
        auth=_IdentityTokenAuth(remote_service_url),
        follow_redirects=True,
        timeout=timeout,
    )
