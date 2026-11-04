from datetime import date,datetime,timedelta,time
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


def convert_to_date(day,month,year):
    date_obj=datetime.strptime(f"{year}-{month}-{day}")
    return date_obj

def convert_to_time(hour,minutes,meridian):
    time_obj=datetime.strptime(f"{hour}:{minutes} {meridian}","%I:%M %p")
    return time_obj

def parse_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        pass
    return "TBA"

def pretty_time(t):
    for format in ("%H:%M:%S","%H:%M"):
        try:
            time=datetime.strptime(str(t),format)
            return time.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            pass
        return "TBA"
            
def when_label(d):
    today=date.today()
    n=(d-today).days

    if n==0:
        return "today"
    elif n>0:
        return f"In {n} days"
    elif n==-1:
        return f"ended yesterday"
    else:
        return f"ended {-n} days ago"
