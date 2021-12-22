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

from pypedrive_api.objects import LeadLabel, Person, Email, Lead


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
            traces: Optional[List["Trace"]] = None,
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
    def __init__(self, api_token: str, base_url: str, lead_title_prefix: str) -> None:
        super().__init__()
        self.api_token = api_token
        self.base_url = base_url
        self.lead_title_prefix = lead_title_prefix
        self._session: Optional[ClientSession] = None

    async def __aenter__(self):
        self._session = ClientSession(
            self.base_url, request_class=_client_request_with_token(self.api_token), headers={"content-type": "application/json"}
        )
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def create_lead_label(self, label: LeadLabel) -> LeadLabel:
        # TODO don't allow duplicates?
        async with self._session.post("/v1/leadLabels", data=label.json(exclude={"id"})) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return LeadLabel(**(resp_dict["data"]))

    async def get_lead_labels(self) -> List[LeadLabel]:
        async with self._session.get("/v1/leadLabels") as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            lead_label_dicts = resp_dict["data"]
            return [LeadLabel(**x) for x in lead_label_dicts]

    async def create_person(self, person: Person) -> Person:
        # TODO don't allow duplicates?
        async with self._session.post("/v1/persons", data=person.json(exclude={"id"})) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return Person(**(resp_dict["data"]))

    async def create_lead(self, lead: Lead) -> Lead:
        # TODO don't allow duplicates?
        async with self._session.post("/v1/leads", data=lead.json(exclude={"id"})) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return Lead(**(resp_dict["data"]))

    async def update_lead(self, lead: Lead) -> Lead:
        """Updates the given lead (by id) with the new field values"""
        async with self._session.patch(f"/v1/leads/{lead.id}", data=lead.json(exclude={"id"}, exclude_unset=True)) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return Lead(**(resp_dict["data"]))

    async def get_lead(self, lead_id: str) -> Lead:
        async with self._session.get(f"/v1/leads/{lead_id}") as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            lead_dict = resp_dict["data"]
            return Lead(**lead_dict)

    async def create_or_get_lead_label(self, label) -> LeadLabel:
        lead_labels = await self.get_lead_labels()
        existing_label = [l for l in lead_labels if l.name == label.name]
        if len(existing_label) == 0:
            # make it
            label = await self.create_lead_label(label)
        else:
            # get it
            label = existing_label[0]
        return label

    # Helper wrappers
    def _minimal_lead_title(self, email: str):
        return f"{self.lead_title_prefix}: {email}"

    async def create_minimal_lead(self, email: str, name: Optional[str], label: Optional[LeadLabel]):
        """Creates a new simple lead with the provided email and optionally a label."""
        # Create a person for this email
        if name is None:
            name = f"<{email}>"
        person = Person(name=name, email=[Email(value=email)])
        person = await self.create_person(person)

        # Create the lead label, if needed
        if label is not None:
            label = await self.create_or_get_lead_label(label)
            label_ids = [label.id]
        else:
            label_ids = []

        # Create a lead attached to this person
        lead = Lead(title=self._minimal_lead_title(email), label_ids=label_ids, person_id=person.id)
        await self.create_lead(lead)

    async def find_minimal_lead(self, email) -> Lead:
        """Finds a minimal lead for the given email"""
        async with self._session.get(
            "/v1/itemSearch",
            params={"term": self._minimal_lead_title(email), "item_types": ["lead"], "fields": ["title"], "exact_match": "false"},
        ) as resp:
            resp.raise_for_status()

            resp_dict = await resp.json()
            results = resp_dict["data"]["items"]
            if results is None or len(results) == 0:
                raise ValueError(f"No lead found for email: {email}")

            # While the search returns json of the match(es), a) that json doesn't align with how the json of other leads looks, and b) it
            # doesn't contain the labels. So do _another_ call to get the lead with the ID we now know.

            return await self.get_lead(results[0]["item"]["id"])

    async def add_label_to_minimal_lead(self, email: str, new_label: LeadLabel):
        """Adds a label to a previously created minimal lead"""
        # Get existing lead by searching
        lead = await self.find_minimal_lead(email)

        # Create or get new label
        new_label = await self.create_or_get_lead_label(new_label)

        # Add the label (unless it already exists)
        if new_label.id not in lead.label_ids:
            # Update obj and update Pipedrive
            lead.label_ids = [*lead.label_ids, new_label.id]
            await self.update_lead(lead)
