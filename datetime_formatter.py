from datetime import date
from database_schema import events

def get_date(raw_date: str):
    if len(raw_date)==0:
        return "enter the date!!"
    count=0
    for char in raw_date:
        if char=="-":
            count+=1
    if count==2:
        date=raw_date.split("-")
        date=date(date[2],date[1],date[0])
        return date
    else:
        return "enter date in correct format"

    


