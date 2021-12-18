"""
Wrapper to API calls.
"""

# TODO env
import asyncio
from ssl import SSLContext
from typing import List, Optional, Mapping, Iterable, Any, Type, Union

from aiohttp import ClientSession, ClientRequest, BasicAuth, http, Fingerprint, ClientResponse
from aiohttp.helpers import BaseTimerContext
from aiohttp.typedefs import LooseHeaders, LooseCookies
from yarl import URL

from pypedrive_api.objects import LeadLabel, Person


def _client_request_with_token(api_token: str):
    class ClientRequestWithToken(ClientRequest):
        def __init__(
            self,
            method: str,
            url: URL,
            *,
            params: Optional[Mapping[str, str]] = None,
            headers: Optional[LooseHeaders] = None,
            skip_auto_headers: Iterable[str] = frozenset(),
            data: Any = None,
            cookies: Optional[LooseCookies] = None,
            auth: Optional[BasicAuth] = None,
            version: http.HttpVersion = http.HttpVersion11,
            compress: Optional[str] = None,
            chunked: Optional[bool] = None,
            expect100: bool = False,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            response_class: Optional[Type["ClientResponse"]] = None,
            proxy: Optional[URL] = None,
            proxy_auth: Optional[BasicAuth] = None,
            timer: Optional[BaseTimerContext] = None,
            session: Optional["ClientSession"] = None,
            ssl: Union[SSLContext, bool, Fingerprint, None] = None,
            proxy_headers: Optional[LooseHeaders] = None,
            traces: Optional[List["Trace"]] = None
        ):
            if params is None:
                params = {}
            params["api_token"] = api_token
            super().__init__(
                method,
                url,
                params=params,
                headers=headers,
                skip_auto_headers=skip_auto_headers,
                data=data,
                cookies=cookies,
                auth=auth,
                version=version,
                compress=compress,
                chunked=chunked,
                expect100=expect100,
                loop=loop,
                response_class=response_class,
                proxy=proxy,
                proxy_auth=proxy_auth,
                timer=timer,
                session=session,
                ssl=ssl,
                proxy_headers=proxy_headers,
                traces=traces,
            )

    return ClientRequestWithToken


class Client:
    def __init__(self) -> None:
        super().__init__()
        self.api_token = "a2b6f4447a165e8926a0f0eb830e6b87c7a25252"  # TODO read in
        self.base_url = "https://ti5.pipedrive.com"  # TODO read in
        self._session: Optional[ClientSession] = None

    async def __aenter__(self):
        self._session = ClientSession(self.base_url, request_class=_client_request_with_token(self.api_token))
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def create_lead_label(self, label: LeadLabel) -> LeadLabel:
        # TODO don't allow duplicates?
        async with self._session.post("/v1/leadLabels", json=label.dict(exclude={"id"})) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return LeadLabel(**(resp_dict["data"]))

    async def get_lead_labels(self) -> List[LeadLabel]:
        ...

    async def create_person(self, person: Person) -> Person:
        ...

    async def create_minimal_lead(self, email: str, label: Optional[LeadLabel]):
        """Creates a new simple lead with the provided email and optionally a label."""
        ...
