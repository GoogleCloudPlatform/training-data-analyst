
import subprocess
from urllib.parse import urlparse

from google.adk.agents.remote_a2a_agent import DEFAULT_TIMEOUT
from google.auth.transport.requests import AuthorizedSession, Request
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.credentials import Credentials
from google.oauth2.id_token import fetch_id_token_credentials
import httpx

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
