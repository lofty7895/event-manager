import flet as ft
import atexit
import os
import subprocess
import sys
import time
import requests
from dotenv import load_dotenv
from datetime import date
from datetime_formatter import parse_date,pretty_time,when_label

load_dotenv()
api_url=os.environ.get("API_URL")
backend_process=None

def backend_is_up():
    try:
        requests.get(f"{api_url}/docs",timeout=1)
        return True
    except requests.RequestException as err:
        print (err)
        return False

def stop_backend():
    if backend_process and backend_process.poll() is None:
        backend_process.terminate()

def start_backend():
    global backend_process
    if backend_is_up():
        return

    backend_process=subprocess.Popen(
        [sys.executable,"-m","uvicorn","backend:app","--port","8000"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    atexit.register(stop_backend)

    for i in range(60):
        if backend_is_up():
            return
        time.sleep(0.5)
    raise RuntimeError ("Backend did not start in time")



COMMON_THEME={
    "bg": ("#F6F3FF","#EDF1FC"),
    "accent":"#5B4ACB",
    "on_accent":"#FFFFFF"
}

THEMES={
    "today": {
        "label":"Events Today",
        "icon": ft.Icons.TODAY_ROUNDED,
        "subtitle":None,
        "action": "View details",
        "empty": "No Event Today"
    },
    "upcoming": {
            "label": "Upcoming Events",
            "icon": ft.Icons.EVENT,
            "subtitle":"Events upcoming in the campus",
            "action": "View details",
            "empty": "No upcoming events have been posted"
    },
    "expired": {
        "label": "Expired Events",
        "icon": ft.Icons.EVENT_AVAILABLE_ROUNDED,
        "subtitle": "Events that have already ended",
        "action": "View Details",
        "empty": "No past events yet"
    }
}
MENU_ORDER=["today","upcoming","expired"]
menu_items={}


def to_card(raw):
    return {
        "name": raw.get("name"),
        "description": raw.get("description"),
        "event_date": parse_date(raw.get("event_date")),
        "venue": raw.get("venue","TBA"),
        "contacts": raw.get("contacts"),
        "event_time": pretty_time(raw.get("event_time")),
        "organiser": raw.get("organiser"),
        "type": raw.get("type")
    }

def fetch_events():
    response=requests.get(f"{api_url}/all_Events",timeout=5)
    response.raise_for_status()
    cards=[]
    for raw in response.json():
        cards.append(to_card(raw))
    return cards

def background(theme):
    return ft.LinearGradient(
        begin=ft.Alignment(-1,-1),
        end=ft.Alignment(1,1),
        colors=list(theme["bg"])
    )

def outline(color):
    side=ft.BorderSide(1,color)
    return ft.Border(left=side, right=side, top=side, bottom=side)

def group_events(events):
    today=date.today()
    sorted_events={
        "today": sorted([e for e in events if e["event_date"]==today],
                        key=lambda e: e["event_time"]),
        "upcoming": sorted ([e for e in events if e["event_date"]>today],
                           key=lambda e: (e(["event_date"],e["event_time"]) )),
        "expired": sorted( [e for e in events if e["event_date"]<today], 
                          key=lambda e: (e["event_date"], e["event_time"]),reverse=True) 
    }
    return sorted_events

 

def GUI(win: ft.Page):
    #background
    win.title="Events Manager"
    win.theme_mode=ft.ThemeMode.LIGHT
    win.bgcolor="#F6F3FF"
    win.horizontal_alignment=ft.CrossAxisAlignment.STRETCH
    win.padding=0
    root=ft.Container(expand=True,padding=ft.Padding(top=28,left=28,right=28,bottom=28))
    root.gradient=background(COMMON_THEME)
    state={"active": "today"}

    try:
        groups=group_events(fetch_events())
        print (f"{groups} events are present")
        load_error=None
    except requests.RequestException:
        groups=group_events([])
        print (f"{groups} is none")
        load_error="Could not reach the server"

    if load_error:
        throw_error(load_error)

    def show_details(ev):
        accent = COMMON_THEME["accent"]

        def close_dialog(e=None):
            if hasattr(win, "pop_dialog"):      # Flet 1.0+
                win.pop_dialog()
            else:                               # older Flet
                dialog.open = False
                win.update()

    def show_details(event):
        accent=COMMON_THEME["accent"]

        def close_dialog():
            if hasattr(win,"pop_diaog"):
                win.pop_dialog()
            else:
                dialog.open=False
                win.update()   

        def detail_row(icon,label,value):
            club=ft.Row (
                [ft.Icon(icon,size=20,color=accent),ft.Column(
                    [ft.Text(label,size=12,color="676781"),
                     ft.Text(value,size=15,color="#272543",selectable=True)],
                    spacing=2,expand=True
                )],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
            

        chip=ft.Container(
            content=ft.Text(event["type"],size=20,
                    weight=ft.FontWeight.W_600,color=accent),
            padding=ft.Padding(left=10,right=10,top=3,bottom=3),
            border_radius=10,
            bgcolor="#EFECFA"                
        )

        reference_days=ft.Text( when_label(event["event_date"]) ) , size=18,color="#676781"

        body=ft.Column(
            spacing=16,tight=True,scroll=ft.ScrollMode.AUTO,
            controls=[
                    ft.Row( 
                        [chip,reference_days],spacing=10,wrap=True
                    ),
                    detail_row(ft.Icons.CALENDAR_MONTH_ROUNDED,"Date",
                        event["event_date"].strftime("%A, %d %B %Y")),
                    detail_row(ft.Icons.SCHEDULE_ROUNDED,"Time",event["event_time"]),
                    detail_row(ft.Icons.LOCATION_ON_ROUNDED,"Venue",event["venue"]),
                    detail_row(ft.Icons.NOTES_ROUNDED,"About this event",event["description"]),
                    detail_row(ft.Icons.GROUPS,"Organiser",event["organiser"]),
                    detail_row(ft.Icons.NOTES_ROUNDED,"Contact",event["contacts"])
            ]
        )


        
        

    def event_card(event,key):
        accent=COMMON_THEME["accent"]
        d=event["event_date"]
        action=THEMES[key]["action"]

        date_tile = ft.Container(
            width=64, 
            height=72,
            border_radius=14,
            bgcolor="#EAE5FF",
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                [ft.Text(str(d.day), size=26, weight=ft.FontWeight.W_700, color=accent),
                ft.Text(d.strftime("%b"), size=13, color=accent)],
                spacing=0, tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    
        chip = ft.Container(
            content=ft.Text(event["type"], size=12, weight=ft.FontWeight.W_600, color=accent),
            padding=ft.Padding(left=10, right=10, top=3, bottom=3),
            border_radius=10,
            bgcolor="#EFECFA",
        )

   
        def meta(icon, text):
            club=ft.Row(
                [ft.Icon(icon, size=20, color=accent),
                ft.Text(text, size=18, color="#676781")],
                spacing=6, tight=True,
            )
            return club

    
        primary = ft.Button(
            content=action,
            height=42,
            style=ft.ButtonStyle(
                bgcolor=accent,
                color=COMMON_THEME["on_accent"],
                overlay_color={"hovered": "#4E3DB8", "pressed": "#4132A0"},
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e, ev=event: show_details(ev)
        )

        controls=[
            ft.Row([chip,ft.Text(when_label(d),size=13,color="#676781")],
                   spacing=10,wrap=True,run_spacing=4),
            ft.Text(event["name"],size=31,weight=ft.FontWeight.W_700,color="#272543",
                    max_lines=2,overflow=ft.TextOverflow.ELLIPSIS),
            ft.Row(
                [meta(ft.Icons.SCHEDULE_ROUNDED,event["event_time"]),
                 meta(ft.Icons.LOCATION_ON_ROUNDED,event["venue"]),
                 meta(ft.Icons.GROUPS,event["organiser"])
                ],
                spacing=18,run_spacing=6,wrap=True
            )
        ]
        controls.append(ft.Row([primary],spacing=100,expand=True))

        details=ft.Column(spacing=16,expand=True,controls=controls)

        return ft.Container(

            content=ft.Row([date_tile,details],spacing=16,vertical_alignment=ft.CrossAxisAlignment.START),
            padding=18,
            border_radius=18,
            bgcolor="#FFFFFF",
            border=outline("#E3DFF0"),
            shadow=ft.BoxShadow(
                blur_radius=18,
                color=ft.Colors.with_opacity(0.08,"#6559A8"),
                offset=ft.Offset(0,5)
            ),
        )


    def throw_error(message):
        error=ft.SnackBar(
            content=ft.Text(message,color=COMMON_THEME["on_accent"]),
            bgcolor=COMMON_THEME["accent"]
        )
        if hasattr(win,"show_dialog"):
            win.show_dialog(error)
        else:
            win.open(error)

    

    def build_menu_item(choice):
        menu_content=THEMES[choice]
        icon=ft.Icon(menu_content["icon"],size=20)
        label=ft.Text(menu_content["label"],size=15)
        count=ft.Text(str(len(groups[choice])),size=24,weight=ft.FontWeight.W_700)
        badge=ft.Container(content=count,padding=ft.Padding(left=8,right=8,top=2,bottom=2),border_radius=8)
        box=ft.Container(
            content=ft.Row([icon,label,badge],spacing=8,tight=True),
            padding=ft.Padding(left=20,right=20,top=14,bottom=14),
            border_radius=12,
            ink=True,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e,k=choice: select(k)
        )
        menu_items[choice]= {"box": box, "icon": icon, "label": label, "badge":badge, "count":count}
        return box

    def refresh_menu():
        for choice, element in menu_items.items():
            chosen= (choice==state["active"])
            fg="#4939AC" if chosen else "#62627A"
            element["box"].bgcolor="#EAE5FF" if chosen else "#FBFAFF"
            element["box"].border=outline("#BDB1EC" if chosen else "#E2DDF0")
            element["icon"].color=fg
            element["label"].color=fg
            element["label"].weight = ft.FontWeight.W_700 if chosen else ft.FontWeight.W_500
            element["count"].color=fg
            element["badge"].bgcolor="#D9D0F7" if chosen else "#EFECF8"

    def refresh_content():
        choice=state["active"]
        theme=THEMES[choice]
        if theme["subtitle"]:
            subtitle_text.value=theme["subtitle"]
        else:
            today=date.today()
            subtitle_text.value=today.strftime("%d %B %Y, %A")

        events=groups[choice]
        if events:
            event_list.controls=([event_card(e,choice) for e in events])
        else:
            event_list.controls=ft.Text(theme["empty"],size=16,color="#BE185D")
        

    def select(choice):
        state["active"]= choice
        refresh_menu()
        refresh_content()
        win.update()

    menu_bar=ft.Row([build_menu_item(selected_menu) for selected_menu in MENU_ORDER],spacing=16,run_spacing=6,wrap=True)
    subtitle_text=ft.Text(size=18,weight=ft.FontWeight.W_600,color=COMMON_THEME["accent"])
    event_list=ft.Column(spacing=14,expand=True,scroll=ft.ScrollMode.AUTO)

    root.content=ft.Column( [menu_bar,subtitle_text,event_list], spacing=20,expand=True)
    win.add(
        ft.Row(root,expand=True,vertical_alignment=ft.CrossAxisAlignment.STRETCH)
    )
    refresh_menu()    
    refresh_content()

if __name__ == "__main__":
    start_backend()
    ft.run(GUI)