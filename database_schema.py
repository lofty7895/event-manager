from sqlalchemy import Column,Integer,String,Text,VARCHAR,Date,Time,BigInteger,ForeignKey
from sqlalchemy.orm import declarative_base,relationship

base=declarative_base()

class organisers(base):
    __tablename__="organisers"
    id=Column(BigInteger,primary_key=True,nullable=False,autoincrement=False)
    organiser_name=Column(Text,nullable=False)
    email_id=Column(Text,unique=True,nullable=False)
    org_rel=relationship("events",back_populates="eve_rel")

class events(base):
    __tablename__="events"
    event_id=Column(BigInteger,primary_key=True,index=False,nullable=False,autoincrement=False)
    name=Column(VARCHAR(100),nullable=False)
    description=Column(Text,nullable=True)
    event_date=Column(Date,nullable=False)
    venue=Column(VARCHAR(100),nullable=False)
    contacts=Column(Text,nullable=False)
    event_time=Column(Time,nullable=False)
    organiser_id=Column(BigInteger,ForeignKey(organisers.id),nullable=False)
    organiser=Column(Text,nullable=False)
    event_type=Column(Text,nullable=False)
    eve_rel=relationship("organisers",back_populates="org_rel")


