"""
Pipedrive objects in pydantic form. TODO implement all.
"""
from abc import ABC
from enum import Enum
from typing import NewType, Optional, List
from uuid import UUID

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
    id: Optional[ID] = None
    title: str
    # owner_id
    label_ids: List[ID]
    person_id: Optional[ID] = None
    organization_id: Optional[ID] = None
    # value
    # expected_close_date
    # was_seen

    @root_validator
    def person_or_org(cls, values):
        if "person_id" not in values and "organization_id" not in values:
            raise ValueError("Person or Org must be specified")


class ContactInfo(BaseModel, ABC):
    primary: bool = True
    label: str = "other"


class Email(ContactInfo):
    value: EmailStr


class Phone(ContactInfo):
    value: str


class Person(BaseModel):
    id: Optional[ID] = None
    name: Optional[str] = None
    # owner_id
    org_id: Optional[str] = None
    email: Optional[Email] = None
    phone: Optional[Phone] = None
    # add_time


class Note(BaseModel):
    id: Optional[ID] = None
    lead_id: Optional[ID] = None
    deal_id: Optional[ID] = None
    person_id: Optional[ID] = None
    org_id: Optional[ID] = None
    content: str
    user_id: Optional[ID] = None