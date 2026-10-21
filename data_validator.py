from pydantic import BaseModel,Field,ConfigDict
from typing import Optional
from datetime import date,time

class OrganisersCreate(BaseModel):
    organiser_name: str
    email_id: str

class OrganisersOut(BaseModel):
    id: int
    organiser_name: str
    email_id: str

class EventIn(BaseModel):
    name: str=Field(max_length=100)
    description: Optional[str]
    event_date: date
    venue: str=Field(max_length=100)
    contacts: str
    event_time: time
    organiser: str,
    event_type: str

class EventOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    event_id: int
    name: str=Field(max_length=100)
    description: Optional[str]
    event_date: date
    venue: str=Field(max_length=100)
    contacts: str
    event_time: time
    organiser_id: int
    organiser: str,
    event_type: str

class EventUpdate(BaseModel):
    name: str=Field(max_length=100)
    description: Optional[str]
    event_date: date
    venue: str=Field(max_length=100)
    contacts: str
    event_time: time
    organiser: str
    event_type: str



