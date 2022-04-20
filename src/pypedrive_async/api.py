"""
Wrapper to API calls.
"""

# TODO env
import asyncio
import json
from functools import partial
from ssl import SSLContext
from typing import List, Optional, Mapping, Iterable, Any, Type, Union

from aiohttp import ClientSession, ClientRequest, BasicAuth, http, Fingerprint, ClientResponse
from aiohttp.helpers import BaseTimerContext
from aiohttp.typedefs import LooseHeaders, LooseCookies
from pydantic.json import custom_pydantic_encoder
from yarl import URL

from pypedrive_async.objects import CustomFields, CustomFieldSource, LeadLabel, Person, CustomField, Email, Lead


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

    async def create_custom_field(self, field: CustomField, type: CustomFieldSource) -> CustomField:
        async with self._session.post(f"/v1/{type}Fields", data=field.json(exclude={"id"})) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return CustomField(**(resp_dict["data"]))

    async def update_custom_field(self, field: CustomField, type: CustomFieldSource) -> CustomField:
        async with self._session.put(f"/v1/{type}Fields/{field.id}", data=field.json(exclude={"id"})) as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            return CustomField(**(resp_dict["data"]))

    async def get_custom_person_fields(self):
        """From configuration, update all custom fields to match current state provided."""
        async with self._session.get("/v1/personFields") as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            person_field_dicts = resp_dict["data"]
            return [CustomField(**x) for x in person_field_dicts]

    async def get_custom_deal_fields(self):
        """From configuration, update all custom fields to match current state provided."""
        async with self._session.get("/v1/dealFields") as resp:
            resp.raise_for_status()
            resp_dict = await resp.json()
            deal_field_dicts = resp_dict["data"]
            return [CustomField(**x) for x in deal_field_dicts]

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

    async def create_person(self, person: Person, custom_fields: CustomFields = {}) -> Person:
        data = person.dict(exclude={"id"})
        data.update(custom_fields)
        data = json.dumps(data, default=partial(custom_pydantic_encoder, Person.Config.json_encoders))
        try:
            # Person matching this email address already exists
            async with self._session.get(f"/v1/persons/search?term={person.email[0].value}&fields=email&exact_match=true") as resp:
                resp.raise_for_status()
                resp_dict = await resp.json()
                if len(resp_dict["data"]["items"]) == 0:
                    raise ValueError("No matching person found. Creating new person.")
                existing_person = Person(**(resp_dict["data"]["items"][0]["item"]))
                async with self._session.put(f"/v1/persons/{existing_person.id}", data=data) as resp:
                    resp.raise_for_status()
                    resp_dict = await resp.json()
                    return Person(**(resp_dict["data"]))
        except:
            # Person does not yet exist
            async with self._session.post("/v1/persons", data=data) as resp:
                resp.raise_for_status()
                resp_dict = await resp.json()
                return Person(**(resp_dict["data"]))

    async def create_lead(self, lead: Lead, custom_fields: CustomFields = {}) -> Lead:
        data = lead.dict(exclude={"id"})
        # If owner_id is None, including it will cause an error
        if data["owner_id"] is None:
            del data["owner_id"]
        data.update(custom_fields)

        data = json.dumps(data, default=partial(custom_pydantic_encoder, Lead.Config.json_encoders))

        try:
            # Lead matching that Person already exists
            async with self._session.get(f"/v1/leads/search?term={lead.title}&fields=title&exact_match=true") as resp:
                resp.raise_for_status()
                resp_dict = await resp.json()
                if len(resp_dict["data"]["items"]) == 0:
                    raise ValueError("No matching lead found. Creating new lead.")
                existing_lead = Lead(**(resp_dict["data"]["items"][0]["item"]), person_id=lead.person_id)
                async with self._session.patch(f"/v1/leads/{existing_lead.id}", data=data) as resp:
                    resp.raise_for_status()
                    resp_dict = await resp.json()
                    return Lead(**(resp_dict["data"]))
        except:
            # Lead does not yet exist
            async with self._session.post("/v1/leads", data=data) as resp:
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

    async def add_label_to_minimal_lead(self, email: str, new_label: LeadLabel, quiet: bool = False):
        """Adds a label to a previously created minimal lead"""
        # Get existing lead by searching
        try:
            lead = await self.find_minimal_lead(email)
        except ValueError:
            if quiet:
                return
            else:
                raise

        # Create or get new label
        new_label = await self.create_or_get_lead_label(new_label)

        # Add the label (unless it already exists)
        if new_label.id not in lead.label_ids:
            # Update obj and update Pipedrive
            lead.label_ids = [*lead.label_ids, new_label.id]
            await self.update_lead(lead)
