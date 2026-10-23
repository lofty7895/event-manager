"""
Events Dashboard - Flet front end

Run:
    pip install -U flet
    python events_dashboard.py            # desktop window
    flet run --web events_dashboard.py    # in the browser

Three menus: Events Today, Expired Events, Upcoming Events.
All menus share a bright, cool-toned lilac and periwinkle theme.
"""

from datetime import date, timedelta

import flet as ft

# --------------------------------------------------------------------------
# 1. Shared colour theme
#    bg        -> pale lilac page background
#    accent    -> periwinkle buttons, active menu, and date tiles
#    on_accent -> text colour that sits on top of the accent
# --------------------------------------------------------------------------
THEMES = {
    "today": {
        "label": "Events Today",
        "icon": ft.Icons.TODAY_ROUNDED,
        "subtitle": None,  # filled in with today's date
        "bg": ("#F6F3FF", "#EDF1FC"),
        "accent": "#5B4ACB",
        "on_accent": "#FFFFFF",
        "action": "View details",
        "empty": "Nothing is scheduled for today.",
    },
    "expired": {
        "label": "Expired Events",
        "icon": ft.Icons.EVENT_BUSY_ROUNDED,
        "subtitle": "Events that have already ended",
        "bg": ("#F6F3FF", "#EDF1FC"),
        "accent": "#5B4ACB",
        "on_accent": "#FFFFFF",
        "action": "View recap",
        "empty": "No past events yet.",
    },
    "upcoming": {
        "label": "Upcoming Events",
        "icon": ft.Icons.EVENT_AVAILABLE_ROUNDED,
        "subtitle": "Events starting after today",
        "bg": ("#F6F3FF", "#EDF1FC"),
        "accent": "#5B4ACB",
        "on_accent": "#FFFFFF",
        "action": "Register",
        "empty": "No upcoming events have been posted.",
    },
}
MENU_ORDER = ["today", "expired", "upcoming"]


# --------------------------------------------------------------------------
# 2. Data. Sample events are dated relative to today so every menu has content.
#    Later, replace fetch_events() with a call to your FastAPI backend.
# --------------------------------------------------------------------------
def fetch_events():
    today = date.today()

    def day(offset):
        return today + timedelta(days=offset)

    return [
        {"title": "Python for Beginners Workshop", "category": "Workshop", "date": day(0),
         "time": "10:00 AM", "venue": "Seminar Hall A", "organiser": "Coding Club",
         "description": "Hands-on session covering variables, loops and a first small project. Bring a laptop."},
        {"title": "Inter-Department Quiz Finals", "category": "Competition", "date": day(0),
         "time": "2:30 PM", "venue": "Main Auditorium", "organiser": "Quiz Society",
         "description": "Eight teams, four rounds. The finals are open for everyone to watch."},
        {"title": "Open Mic Evening", "category": "Cultural", "date": day(0),
         "time": "6:00 PM", "venue": "Amphitheatre", "organiser": "Music Club",
         "description": "Music, poetry and stand-up. Sign up at the venue to perform."},
        {"title": "Resume Review Clinic", "category": "Career", "date": day(-1),
         "time": "4:00 PM", "venue": "Placement Cell", "organiser": "Placement Cell",
         "description": "One-to-one resume feedback from senior students and alumni."},
        {"title": "Robotics Demo Day", "category": "Tech", "date": day(-4),
         "time": "11:00 AM", "venue": "Innovation Lab", "organiser": "Robotics Club",
         "description": "Teams showed line-followers, robotic arms and a few surprises."},
        {"title": "Freshers' Welcome Night", "category": "Cultural", "date": day(-12),
         "time": "7:00 PM", "venue": "Main Lawn", "organiser": "Student Council",
         "description": "Dinner, performances and an introduction to every club on campus."},
        {"title": "Hack the Campus: 24-hour Hackathon", "category": "Hackathon", "date": day(2),
         "time": "9:00 AM", "venue": "Computer Centre", "organiser": "Coding Club",
         "description": "Teams of up to four build a working project in 24 hours. Prizes for the top three."},
        {"title": "Alumni Talk: Careers in Product", "category": "Career", "date": day(6),
         "time": "5:00 PM", "venue": "Main Auditorium", "organiser": "Alumni Cell",
         "description": "Three alumni share how they moved into product roles, followed by Q&A."},
        {"title": "Annual Tech Fest Kick-off", "category": "Festival", "date": day(15),
         "time": "10:00 AM", "venue": "Main Ground", "organiser": "Tech Fest Committee",
         "description": "Opening ceremony, stall walkthrough and the full event schedule."},
    ]


def group_events(events):
    today = date.today()
    return {
        "today": [e for e in events if e["date"] == today],
        "expired": sorted([e for e in events if e["date"] < today],
                          key=lambda e: e["date"], reverse=True),
        "upcoming": sorted([e for e in events if e["date"] > today],
                           key=lambda e: e["date"]),
    }


def when_label(d):
    n = (d - date.today()).days
    if n == 0:
        return "Today"
    if n > 0:
        return "Tomorrow" if n == 1 else f"In {n} days"
    return "Ended yesterday" if n == -1 else f"Ended {-n} days ago"


# --------------------------------------------------------------------------
# 3. Small style helpers
# --------------------------------------------------------------------------
def white(opacity):
    return "#676781"


def outline(color):
    side = ft.BorderSide(1, color)
    return ft.Border(left=side, top=side, right=side, bottom=side)


def background(theme):
    return ft.LinearGradient(
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
        colors=list(theme["bg"]),
    )


# --------------------------------------------------------------------------
# 4. The app
# --------------------------------------------------------------------------
def main(page: ft.Page):
    page.title = "Events Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F6F3FF"
    page.padding = 0
    page.spacing = 0
    page.window.width = 1100
    page.window.height = 780
    page.window.min_width = 380

    groups = group_events(fetch_events())
    state = {"active": "today"}
    menu_items = {}

    # ---- feedback when a card button is pressed (replace with real actions)
    def toast(message):
        t = THEMES[state["active"]]
        snack = ft.SnackBar(
            content=ft.Text(message, color=t["on_accent"]),
            bgcolor=t["accent"],
        )
        if hasattr(page, "show_dialog"):  # Flet 1.0+
            page.show_dialog(snack)
        else:  # older Flet
            page.open(snack)

    # ---- one menu button
    def build_menu_item(key):
        t = THEMES[key]
        icon = ft.Icon(t["icon"], size=20)
        label = ft.Text(t["label"], size=15)
        count = ft.Text(str(len(groups[key])), size=12, weight=ft.FontWeight.W_700)
        badge = ft.Container(
            content=count,
            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
            border_radius=8,
        )
        box = ft.Container(
            content=ft.Row([icon, label, badge], spacing=8, tight=True),
            padding=ft.Padding(left=16, right=12, top=11, bottom=11),
            border_radius=12,
            ink=True,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e, k=key: select(k),
        )
        menu_items[key] = {"box": box, "icon": icon, "label": label,
                           "badge": badge, "count": count}
        return box

    def refresh_menu():
        for key, m in menu_items.items():
            t = THEMES[key]
            active = key == state["active"]
            fg = "#4939AC" if active else "#62627A"
            # All menu items share one cool palette; selection uses a light tint.
            m["box"].bgcolor = "#EAE5FF" if active else "#FBFAFF"
            m["box"].border = outline("#BDB1EC" if active else "#E2DDF0")
            m["icon"].color = fg
            m["label"].color = fg
            m["label"].weight = ft.FontWeight.W_700 if active else ft.FontWeight.W_500
            m["count"].color = fg
            m["badge"].bgcolor = "#D9D0F7" if active else "#EFECF8"

    # ---- event cards
    def meta(icon, text, color):
        return ft.Row(
            [ft.Icon(icon, size=16, color=color),
             ft.Text(text, size=13, color=white(0.82))],
            spacing=6, tight=True,
        )

    def event_card(ev, key):
        t = THEMES[key]
        accent = t["accent"]
        d = ev["date"]

        date_tile = ft.Container(
            width=64, height=72, border_radius=14,
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
            content=ft.Text(ev["category"], size=12, weight=ft.FontWeight.W_600, color=accent),
            padding=ft.Padding(left=10, right=10, top=3, bottom=3),
            border_radius=10,
            bgcolor="#EFECFA",
        )

        primary = ft.Button(
            content=t["action"],
            height=42,
            style=ft.ButtonStyle(
                bgcolor=accent,
                color=t["on_accent"],
                overlay_color={"hovered": "#4E3DB8", "pressed": "#4132A0"},
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e, ev=ev, t=t: toast(f'{t["action"]}: {ev["title"]}'),
        )
        secondary = ft.TextButton(
            content="Share",
            style=ft.ButtonStyle(
                color="#5141B8",
                bgcolor="#FFFFFF",
                side=ft.BorderSide(1, "#E0DAF0"),
                overlay_color=ft.Colors.with_opacity(0.08, accent),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e, ev=ev: toast(f'Link copied for {ev["title"]}'),
        )

        details = ft.Column(
            spacing=8,
            expand=True,
            controls=[
                ft.Row([chip, ft.Text(when_label(d), size=13, color=white(0.65))],
                       spacing=10, wrap=True, run_spacing=4),
                ft.Text(
                    ev["title"],
                    size=19,
                    weight=ft.FontWeight.W_700,
                    color="#272543",
                    font_family="Arial",
                ),
                ft.Row(
                    [meta(ft.Icons.SCHEDULE_ROUNDED, ev["time"], accent),
                     meta(ft.Icons.LOCATION_ON_ROUNDED, ev["venue"], accent),
                     meta(ft.Icons.PERSON_ROUNDED, ev["organiser"], accent)],
                    spacing=18, run_spacing=6, wrap=True,
                ),
                ft.Text(ev["description"], size=14, color=white(0.7),
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Row([primary, secondary], spacing=8, wrap=True),
            ],
        )

        return ft.Container(
            content=ft.Row([date_tile, details], spacing=16,
                           vertical_alignment=ft.CrossAxisAlignment.START),
            padding=18,
            border_radius=18,
            bgcolor="#FFFFFF",
            border=outline("#E3DFF0"),
            shadow=ft.BoxShadow(
                blur_radius=18,
                color=ft.Colors.with_opacity(0.08, "#6559A8"),
                offset=ft.Offset(0, 5),
            ),
        )

    def empty_state(key):
        t = THEMES[key]
        return ft.Container(
            padding=40,
            alignment=ft.Alignment(0, 0),
            bgcolor="#FFFFFF",
            border_radius=18,
            border=outline("#E3DFF0"),
            shadow=ft.BoxShadow(
                blur_radius=18,
                color=ft.Colors.with_opacity(0.08, "#6559A8"),
                offset=ft.Offset(0, 5),
            ),
            content=ft.Column(
                [ft.Icon(ft.Icons.EVENT_NOTE_ROUNDED, size=48,
                         color=ft.Colors.with_opacity(0.6, t["accent"])),
                 ft.Text(t["empty"], size=16, color=white(0.8))],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ---- page structure
    title_text = ft.Text(
        size=30,
        weight=ft.FontWeight.W_700,
        color="#272543",
        font_family="Arial",
    )
    subtitle_text = ft.Text(size=14, color=white(0.65))
    cards = ft.Column(spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)

    root = ft.Container(expand=True, padding=ft.Padding(left=28, right=28, top=28, bottom=0))

    def refresh_content():
        key = state["active"]
        t = THEMES[key]
        title_text.value = t["label"]
        subtitle_text.value = t["subtitle"] or date.today().strftime("%A, %d %B %Y")
        cards.controls = [event_card(ev, key) for ev in groups[key]] or [empty_state(key)]
        root.gradient = background(t)

    def select(key):
        state["active"] = key
        refresh_menu()
        refresh_content()
        page.update()

    menu_bar = ft.Row(
        [build_menu_item(k) for k in MENU_ORDER],
        spacing=8, run_spacing=8, wrap=True,
    )

    root.content = ft.Column(
        spacing=20,
        expand=True,
        controls=[
            ft.Text("Events Dashboard", size=16, weight=ft.FontWeight.W_600, color=white(0.8)),
            menu_bar,
            ft.Column([title_text, subtitle_text], spacing=2),
            cards,
        ],
    )

    refresh_menu()
    refresh_content()
    page.add(root)


if __name__ == "__main__":
    ft.run(main)  # on Flet older than 1.0 use: ft.app(target=main)