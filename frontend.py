import flet as ft
import atexit
import os
import subprocess
import sys
import time
import requests
from dotenv import load_dotenv
from datetime import date, datetime
from datetime_formatter import parse_date,pretty_time,when_label,convert_to_date,convert_to_time

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

    def throw_error(message):
        error=ft.SnackBar(
            content=ft.Text(message,color=COMMON_THEME["on_accent"]),
            bgcolor=COMMON_THEME["accent"]
        )
        if hasattr(win,"show_dialog"):
            win.show_dialog(error)
        else:
            win.open(error)

    try:
        groups=group_events(fetch_events())
        load_error=None
    except requests.RequestException:
        groups=group_events([])
        load_error="Could not reach the server"

    if load_error:
        throw_error(load_error)

    def reload_events():
        nonlocal groups
        try:
            groups=group_events(fetch_events())
        except requests.RequestException:
            throw_error("Could not refresh events")

    def open_create_form(e=None):
        year=date.today().year
        accent=COMMON_THEME["accent"]

        days=[i for i in range(1,32)]
        months=[i for i in range (1,13)]
        years=[year,year+1]
        hours=[i for i in range(1,13)]
        minutes=[i for i in range(0,60)]
        am_pm=["AM","PM"]
        event_type=["Hackathon","Buildathon","Workshop","Conference","Seminar","Webinar","Guest Lectures","Concert","Others"]


        def close_form(e=None):
            if layer in win.overlay:
                win.overlay.remove(layer)
                win.update()

        close_btn=ft.Container(
            content=ft.Icon(ft.Icons.CLOSE_ROUNDED,size=18,color="#BE185D"),
            width=32,
            height=32,
            bgcolor="#FCE4EC",
            alignment=ft.Alignment(0,0),
            ink=True,
            on_click=close_form
        )

        add_icon=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, size=22, color=accent)
        button_Text=ft.Text("Create new event",size=19,weight=ft.FontWeight.W_700,color="#272543",expand=True)
        header=ft.Container(
            bgcolor="#EAE5FF",
            padding=ft.Padding(left=22,right=14,top=14,bottom=14),
            border=ft.Border(bottom=ft.BorderSide(1,"#CFC6F2")),
            content=ft.Row([add_icon,button_Text,close_btn],spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        )
        )

        def field(label_x,**kwargs):
            text_field=ft.TextField(
                label=label_x,
                border={
                ft.ControlState.ERROR: ft.OutlineInputBorder(border_radius=12,side=ft.BorderSide(2,"#BE185D")),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(border_radius=12,side=ft.BorderSide(2,accent)),
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(border_radius=12,side=ft.BorderSide(1,"#E0DAF0"))
                },
                bgcolor="#FFFFFF",
                text_size=15,
                **kwargs
            )
            return text_field

        def dropdown_menu(title,width_x,list_x,**kwargs):
            dropdown=ft.Dropdown(label=title,width=width_x,
                    options=[ft.DropdownOption(key=str(i), text=str(i)) for i in list_x],**kwargs
            )
            return dropdown

        name_f=field("Event Name *",autofocus=True,width=900)
        description_f=field("Description",multiline=True,width=900,min_lines=15)
        day_f=dropdown_menu("Day",100,days)
        month_f=dropdown_menu("Month",130,months)
        year_f=dropdown_menu("Year",130,years)
        hour_f=dropdown_menu("Hour",130,hours)
        minutes_f=dropdown_menu("Minute",130,minutes)
        am_pm_f=dropdown_menu("Time Period",180,am_pm)
        venue_f=field("Venue")
        organiser_f=field("Organiser *",hint_text="Organiser * (must already be registered)")
        contacts_f=field("Contacts *",min_lines=2,multiline=True)
        type_f=dropdown_menu("Type *",300,event_type,value="Others")
        required=[name_f,organiser_f,contacts_f,type_f]

        date_f=ft.Row([day_f,month_f,year_f],spacing=6)
        time_f=ft.Row([hour_f,minutes_f,am_pm_f],spacing=6)
        
        date_time_f=ft.Row([date_f,time_f],spacing=90)

        error_msg=ft.Text("",size=13,color="#BE185D",visible=False)

        def set_field_error(control, has_error):
            control.border = {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(
                width=2 if has_error else 1,
                color="#BE185D" if has_error else "#E0DAF0"
                )
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(width=2, color=accent),
            ),
            ft.ControlState.ERROR: ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(width=2, color="#BE185D"),
            )
            }


        def show_error(message):
            error_msg.value=message
            error_msg.visible=True
            win.update()

        def submit(e):
            error_msg.visible=False
            for f in required:
                set_field_error(f,False)

            missing=[f for f in required if not (f.value or "").strip()]
            if missing:
                for f in missing:
                    set_field_error(f,True)
                show_error("Please fill in the fields marked with *")
                return

            

            payload={
                "event_name": name_f.value.strip(),
                "description": (description_f.value or "").strip(),
                "event_date": (convert_to_date(year_f.value,month_f.value,day_f.value) or ""),
                "event_time": (convert_to_time(hour_f.value,minutes_f.value,am_pm_f.value) or ""),
                "venue": (venue_f.value or "").strip(),
                "organiser": organiser_f.value.strip(),
                "contacts": contacts_f.value.strip(),
                "type": type_f.value        
            }

            submit_btn.disabled=True
            submit_btn.content="Saving..."
            win.update()

            try:
                r=requests.post(f"{api_url}/Post_event",json=payload,timeout=5)
            except requests.RequestException:
                r=None

            submit_btn.disabled=False
            submit_btn.content="Submit"

            if r is None:
                show_error("Could not reach the server")
                return
            elif r.status_code==404:
                show_error("Organiser not found. Check the spelling or register them first.")
                return
            elif not r.ok:
                print (r.status_code,r.text)
                show_error(f"The server rejected the event ({r.status_code})")
                return

            close_form()
            reload_events()
            refresh_menu()
            refresh_content()
            win.update()
            throw_error("Event created")

        cancel_btn=ft.TextButton(
            content="Cancel",
            style=ft.ButtonStyle(
                color="#5141B8",
                shape=ft.RoundedRectangleBorder(radius=12)
            ),
            on_click=close_form
        )

        submit_btn=ft.Button(
            content="Submit",
            height=42,
            style=ft.ButtonStyle(
                bgcolor=accent,
                color=COMMON_THEME["on_accent"],
                overlay_color={"hovered": "#4E3DB8","pressed": "#4132A0"},
                shape=ft.RoundedRectangleBorder(radius=12)
            ),
            on_click=submit
        )

        submit_cancel=ft.Row([cancel_btn,submit_btn],alignment=ft.MainAxisAlignment.END,spacing=10)

        header = ft.Container(
            bgcolor="#EAE5FF",
            padding=ft.Padding(left=22, right=14, top=14, bottom=14),
            border=ft.Border(bottom=ft.BorderSide(1, "#CFC6F2")),
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, size=22, color=accent),
                 ft.Text("Create new event", size=19, weight=ft.FontWeight.W_700,
                         color="#272543", expand=True),
                 close_btn],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        
        
        body=ft.Container(
                expand=True,
                padding=ft.Padding(left=22,right=22,top=18,bottom=8),
                content=ft.Column(
                    [name_f,description_f,date_time_f,venue_f,organiser_f,contacts_f,type_f],
                    spacing=14,scroll=ft.ScrollMode.AUTO,expand=True
                ),
        )

        footer=ft.Container(
                    padding=ft.Padding(left=22,right=22,top=10,bottom=16),
                    content=ft.Column([error_msg,submit_cancel],spacing=8,tight=True)
        )
    
    

        card=ft.Container(
            width=1000,
            height=800,
            bgcolor="#FFFFFF",
            border_radius=18,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=24,
                color=ft.Colors.with_opacity(0.25,"#6559A8"),
                offset=ft.Offset(0,8)
            ),
            content=ft.Column([header,body,footer],spacing=0)
        )

        layer=ft.Container(
            left=0,right=0,top=0,bottom=0,
            bgcolor=ft.Colors.with_opacity(0.45,"#272543"),
            alignment=ft.Alignment(0,0),
            content=card
        )



        win.overlay.append(layer)
        win.update()

        
    def open_panel(event):
        accent=COMMON_THEME["accent"]
        offset=30*(len(win.overlay) % 8)

        def detail_row(icon,label,value):
            club=ft.Row (
                [ft.Icon(icon,size=20,color=accent),ft.Column(
                    [ft.Text(label,size=12,color="#676781"),
                     ft.Text(value,size=15,color="#272543",selectable=True)],
                    spacing=2,expand=True
                )],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

            return club

        def drag(e):
            panel.left=max(0, panel.left+e.local_delta.x)
            panel.top=max(0, panel.top+e.local_delta.y)
            panel.update()

        def close(e):
            win.overlay.remove(panel)
            win.update()

        def hover_close(e):
            hovering=str(e.data).lower() == "true"
            close_btn.bgcolor="#BE185D" if hovering else "#FCE4EC"
            close_btn.content.color= "#FFFFFF" if hovering else "#BE185D"
            close_btn.update()

        close_btn=ft.Container(
            content=ft.Icon(ft.Icons.CLOSE_ROUNDED,size=18,color="#BE185D"),
            width=32,height=32,
            border_radius=10,
            bgcolor="#FCE4EC",
            alignment=ft.Alignment(0,0),
            ink=True,
            on_click=close,
            on_hover=hover_close
        )

        title_bar=ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.MOVE,
            on_pan_update=drag,
            drag_interval=10,
            content=ft.Container(
                bgcolor="#EAE5FF",
                padding=ft.Padding(left=18,right=12,top=10,bottom=10),
                border=ft.Border(bottom=ft.BorderSide(1,'#CFC6F2')),
                content=ft.Row(
                    [ft.Icon(ft.Icons.DRAG_INDICATOR,size=18,color=accent),
                     ft.Text(event["name"],size=17,weight=ft.FontWeight.W_700,
                             color="#272543",expand=True,max_lines=1,overflow=ft.TextOverflow.ELLIPSIS),
                    close_btn],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            )
        )

        reference_days=ft.Text( when_label(event["event_date"]) , size=18,color="#676781")
        body=ft.Container(padding=18, expand=True,
            content = ft.Column(
            spacing=16,scroll=ft.ScrollMode.AUTO,
            controls=[
                    ft.Row( 
                        [reference_days],spacing=10,wrap=True
                    ),
                    detail_row(ft.Icons.CALENDAR_MONTH_ROUNDED,"Date",
                        event["event_date"].strftime("%A, %d %B %Y")),
                    detail_row(ft.Icons.SCHEDULE_ROUNDED,"Time",event["event_time"]),
                    detail_row(ft.Icons.LOCATION_ON_ROUNDED,"Venue",event["venue"]),
                    detail_row(ft.Icons.NOTES_ROUNDED,"About this event",event["description"]),
                    detail_row(ft.Icons.GROUPS,"Organiser",event["organiser"]),
                    detail_row(ft.Icons.CALL_ROUNDED,"Contact",event["contacts"])
            ]
            )
        )

        panel=ft.Container(
            width=1000,
            height=900,
            padding=ft.Padding(bottom=20),
            left=120+offset,top=80+offset,
            bgcolor="#FFFFFF",
            border_radius=18,
            border=outline("#E3DFF0"),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=18,
                color=ft.Colors.with_opacity(0.15,"#6559A8"),
                offset=ft.Offset(0,5)
            ),
            content=ft.Column([title_bar,body],spacing=0,tight=True),
        )

        win.overlay.append(panel)
        win.update()

    def event_card(event,key):
        accent=COMMON_THEME["accent"]
        d=event["event_date"]
        action=THEMES[key]["action"]

        date_tile = ft.Container(
            margin=ft.Margin(left=0,right=0,top=24,bottom=0),
            width=64, 
            height=72,
            border_radius=14,
            bgcolor="#EAE5FF",
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                [ft.Text(str(d.day), size=26, weight=ft.FontWeight.W_700, color=accent),
                ft.Text(d.strftime("%b"), size=13, color=accent)],
                spacing=0, tight=True,
                alignment=ft.MainAxisAlignment.END,
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
            on_click=lambda e, ev=event: open_panel(ev)
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
            event_list.controls=[event_card(e,choice) for e in events]
        else:
            event_list.controls=[ft.Text(theme["empty"],size=16,color="#BE185D")]
        

    def select(choice):
        state["active"]= choice
        refresh_menu()
        refresh_content()
        win.update()
        
    create_btn = ft.Button(
        content="Create new event",
        icon=ft.Icons.ADD_ROUNDED,
        height=46,
        style=ft.ButtonStyle(
            bgcolor=COMMON_THEME["accent"],
            color=COMMON_THEME["on_accent"],
            overlay_color={"hovered": "#4E3DB8", "pressed": "#4132A0"},
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=open_create_form,
    )

    menu_bar=ft.Row([build_menu_item(selected_menu) for selected_menu in MENU_ORDER],expand=True,spacing=16,run_spacing=6,wrap=True)
    subtitle_text=ft.Text(size=18,weight=ft.FontWeight.W_600,color=COMMON_THEME["accent"])
    event_list=ft.Column(spacing=14,expand=True,scroll=ft.ScrollMode.AUTO)

    root.content = ft.Column(
        [ft.Row([menu_bar, create_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER),
         subtitle_text, event_list],
        spacing=20, expand=True,
    )

    win.add(
        ft.Row(root,expand=True,vertical_alignment=ft.CrossAxisAlignment.STRETCH)
    )
    refresh_menu()    
    refresh_content()

if __name__ == "__main__":
    start_backend()
    ft.run(GUI)