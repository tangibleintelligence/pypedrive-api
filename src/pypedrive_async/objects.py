"""
Pipedrive objects in pydantic form. TODO implement all.
"""
from abc import ABC
from enum import Enum
from typing import NewType, Optional, List, Dict, Any
from uuid import UUID
from xmlrpc.client import Boolean

from pydantic import BaseModel, root_validator, EmailStr

ID = NewType("ID", int)


class LeadColor(str, Enum):
    green = "green"
    blue = "blue"
    red = "red"
    yellow = "yellow"
    purple = "purple"
    gray = "gray"


class LeadLabel(BaseModel):
    id: Optional[UUID] = None
    name: str
    color: LeadColor


class Lead(BaseModel):
    id: Optional[UUID] = None
    title: str
    owner_id: Optional[ID] = None
    label_ids: List[UUID] = []
    person_id: Optional[ID] = None
    organization_id: Optional[ID] = None
    # value
    # expected_close_date
    # was_seen

    @root_validator
    def person_or_org(cls, values):
        if values.get("person_id", None) is None and values.get("organization_id", None) is None:
            raise ValueError("Person or Org must be specified")

        return values


class ContactInfo(BaseModel, ABC):
    primary: bool = True
    label: str = "other"


class Email(ContactInfo):
    value: EmailStr


class Phone(ContactInfo):
    value: str


class Person(BaseModel):
    id: Optional[ID] = None
    name: str
    # owner_id
    org_id: Optional[str] = None
    email: List[Email] = []
    phone: List[Phone] = []
    # add_time


class Note(BaseModel):
    id: Optional[ID] = None
    lead_id: Optional[ID] = None
    deal_id: Optional[ID] = None
    person_id: Optional[ID] = None
    org_id: Optional[ID] = None
    content: str
    user_id: Optional[ID] = None


class CustomFieldSource(str, Enum):
    person = "person"
    deal = "deal"
    

class CustomField(BaseModel):
    """ Custom field for a Person, Deal, or Lead object """
    id: Optional[ID] = None
    key: str
    name: str
    field_type: str # Initially this was an Enum, but Pipedrive does not provide a complete list of possible enum values so now it's a str
    # Available 'options' for the field, required for set or enum type fields
    options: Optional[List[dict]] = None
    add_visible_flag: Optional[Boolean] = True

class CustomFields(BaseModel):
    __root__: Dict[str, CustomField]
