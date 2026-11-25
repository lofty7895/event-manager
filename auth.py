import os
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from supabase import create_client, ClientOptions

router=APIRouter(prefix="/auth")
URL=os.getenv("SUPABASE_URL")
KEY=os.getenv("SUPABASE_SERVICE_KEY")
BACKENED=os.getenv("BACKEND_URL","http://localhost:8000")

shared_client=create_client(URL, KEY)
pending={}

def new_client():
    return create_client(URL,KEY,options=ClientOptions(flow_type="pkce"))

@router.get("/login")
def login(login_id: str):
    client=new_client()
    res=client.auth.sign_in_with_oauth({
        "provider":"google",
        "options": {"redirect_to": f"{BACKEND}/auth/callback?login_id={login_id}"},
    })
    pending[login_id]={"client":client,"session":None}
    return RedirectResponse(res.url)

@router.get("/callback")
def callback(login_id:str, code:str):
    entry=pending.get(login_id)
    if not entry:
        raise HTTPException(400,"Unknown or expired login")
    r=entry["client"].auth.exchange_code_for_session({"auth_code":code})
    entry["session"]={
        "access_token": r.session.access_token,
        "refresh_token": r.session.refresh_token,
        "email":r.user.email,
        "name": (r.user.user_metadata or {}).get("full_name","")
    }
    return HTMLResponse("<h3>Signed in. You can close this tab and return to the app.</h3>")

@router.get("/poll/{login_id}")
def poll(login_id:str):
    entry=pending.get(login_id)
    if not entry:
        raise HTTPException(404,"Unknown login")
    if entry["session"] is None:
        return {"status":"pending"}
    session=entry["session"]
    del pending[login_id]
    return {"status":"ok",**session}

def get_current_user(authorization: str=Header(None)):
    if not authorization or authorization.startswith("Bearer "):
        raise HTTPException(401,"Missing token")
    token=authorization.split(" ",1)[1]
    try:
        res=shared_client.auth.get_user(token)
    except Exception:
        raise HTTPException (401,"INvalid or expired token")
    if not res or not res.user:
        raise HTTPException(401,"Invalid token")
    return res.user

