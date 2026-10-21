from fastapi import FastAPI,Depends,HTTPException
from database_connector import get_db
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import date,time,datetime
from datetime_formatter import get_date
import database_schema
from data_validator import EventIn,EventOut,OrganisersCreate,OrganisersOut,EventUpdate
from random import randint


app=FastAPI()

def generate_unique_id(db,column):
    for i in range(100):
        unique_id=randint(10000,99999)
        db_count=db.query(column).filter(column==unique_id).first()
        if not db_count:
            return unique_id
    raise RuntimeError("No Free IDs Left")

#to view all events
@app.get("/all_Events")
def get_all_events(db: Session=Depends(get_db)):
    all_events=db.query(database_schema.events).all()
    return all_events

@app.get("/Events_today")
def get_events_today(db: Session=Depends(get_db)):
    date_obj=date.today()
    events_today=db.query(database_schema.events).filter(database_schema.events.event_date==date_obj).all()
    events_today.sort(key=lambda e: e.time)
    if len(events_today)==0:
        return "No events today"
    else:
        return events_today

@app.post("/Post_event",response_model=EventOut)
def post_event(event: EventIn, db: Session = Depends(get_db)):
    organiser = (
        db.query(database_schema.organisers).filter(func.lower(database_schema.organisers.organiser_name) == event.organiser.lower()).first()
    )
    print (type(organiser))
    
    if not organiser:
        raise HTTPException(status_code=404,detail="Organiser not found")

    data = event.model_dump(exclude={"organiser_id","event_id"})

    db_event = database_schema.events(
        **data,
        event_id=generate_unique_id(db, database_schema.events.event_id),
        organiser_id=organiser.id,
    )

    db.add(db_event)
    db.commit()
    return db_event

@app.post("/Register_organiser",response_model=OrganisersOut)
def register_organiser(organiser: OrganisersCreate, db: Session = Depends(get_db)):

    data = organiser.model_dump(exclude={"id"})

    db_event = database_schema.organisers(
        **data,
        id=generate_unique_id(db, database_schema.organisers.id)
        )

    db.add(db_event)
    db.commit()
    return db_event

@app.put("/Edit_event",response_model=EventOut)
def edit_event(Event_id: int,updated_values: EventUpdate,db: Session=Depends(get_db)):
    db_event=db.query(database_schema.events).filter(database_schema.events.event_id==Event_id).first()
    if db_event:
        for field,value in updated_values.model_dump(exclude_unset=True).items():
            if field=="organiser" and len(value)!=0:
                organiser=db.query(database_schema.organisers).filter(func.lower(database_schema.organisers.organiser_name)==value.lower()).first()
                if organiser:
                    setattr(db_event,field,value)
                    setattr(db_event,"organiser_id",organiser.id)
                else:
                    raise HTTPException(detail="Organiser not found",status_code=404)
            if value is None and field!="Description":
                continue
            setattr(db_event,field,value)
        db.commit()
        return db_event
    else:
        raise HTTPException(detail="event not found",status_code=404)

@app.put("/Edit_organiser_details",response_model=OrganisersOut)
def edit_organiser_details(Organiser_id: int,updated_values: OrganisersCreate,db: Session=Depends(get_db)):
    organiser=db.query(database_schema.organisers).filter(database_schema.organisers.id==Organiser_id).first()
    if organiser:
        for field,value in updated_values.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            setattr(organiser,field,value)
        db.commit()
        return organiser
    else:
        raise HTTPException(status_code=404,detail="organiser does not exist")
"""
@app.put("/Delete_event")
def delete_event(Event_id: int,db: Session=Depends(get_db)):
    event=db.query(database_schema.events).filter(database_schema.events.event_id==Event_id).first()
    if event:
        db.delete(event)
        db.commit()
        return "Event deleted successfully"
    else:
        raise HTTPException(status_code=404,detail="Event not found")
    
@app.put("/Delete_organiser")
def delete_event(Organiser_id: int,db: Session=Depends(get_db)):
    event=db.query(database_schema.organisers).filter(database_schema.organisers.id).first()
    if event:
        db.delete(event)
        db.commit()
        return "organiser removed from database"
    else:
        raise HTTPException(status_code=404,detail="Organiser not found")

@app.get("/Expired_events")
def expired_event(db: Session=Depends(get_db)):
    date_obj=date.today()
    expired_events=db.query(database_schema.organisers).filter(database_schema.events.event_date < date_obj).all()
    return expired_events

"""

