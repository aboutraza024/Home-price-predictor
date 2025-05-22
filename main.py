import os
from dotenv import load_dotenv
from pyexpat.errors import messages

from models import get_user_by_email, get_user_by_email_google, get_user_by_github, create_user_with_github, \
    create_user_with_google, create_user
from models import UserCreate, LoginUser, Register_With_Google, Register_With_Github, Register_With_Email,PredictHouse
from auth import send_verification_code
from models import app, SessionLocal
import uvicorn
from fastapi import FastAPI, Form, Depends, HTTPException, Request, BackgroundTasks, File, UploadFile
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import create_engine, Integer, String, Column
import random
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
import io
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError

get_email = {}
get_email_forget = {}

load_dotenv()
github_client_id = os.getenv("github_client_id1")
github_client_secret = os.getenv("github_client_secret1")

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id="610538991757-6i1rno8vnhac5d2bcl1a85om8b4h81a9.apps.googleusercontent.com",
    client_secret="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",
    client_kwargs={
        'scope': 'openid profile email',
    },
)


def v_code():
    return random.randint(100000, 999999)


verification_code = v_code()  # check every one get unique code


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory="templates")


# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def display_landing_page(request: Request):
    return templates.TemplateResponse("landing_page.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def get_form_data1(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def get_form_data1(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/verification", response_class=HTMLResponse)
def get_form_data(request: Request):
    return templates.TemplateResponse("verification.html", {"request": request})


@app.post("/register", response_model=UserCreate, status_code=201)
def reg_user(request: Request, backgroundtask: BackgroundTasks, user: UserCreate = Depends(UserCreate.as_form),
             db: Session = Depends(get_db)):
    get_email["f_name"] = user.first_name
    get_email["l_name"] = user.last_name
    get_email["email"] = user.email
    get_email["password"] = user.password
    print("Hello", user)
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        message3 = True
        return templates.TemplateResponse("register.html", {"request": request, "message3": message3})
    backgroundtask.add_task(send_verification_code, user.email, verification_code)
    return RedirectResponse(url="/verification", status_code=303)


@app.post("/verification", response_class=HTMLResponse)
def verify_code(request: Request, backgroundtask: BackgroundTasks, vcode1: str = Form(...),
                db: Session = Depends(get_db)):
    email = get_email.get("email")
    first_name = get_email.get("f_name")
    last_name = get_email.get("l_name")
    password = get_email.get("password")
    newpassword = get_email_forget.get("newpassword")
    password1 = get_email_forget.get("password")
    email2 = get_email_forget.get("email")
    print(email)
    print("mail", email, "fname", first_name, "lname", last_name, "password", password)
    print(f"Verification code received: {vcode1}")
    vcode2 = int(vcode1)
    verification_code2 = int(verification_code)
    if newpassword:
        if verification_code2 == vcode2:
            user = db.query(Register_With_Email).filter(
                Register_With_Email.email == email2).first()  # Fetch the user instance
            if user:
                user.password = newpassword
                db.commit()
                db.refresh(user)
                message2 = True
            else:
                message2 = False
        else:
            message3 = True
            return templates.TemplateResponse("verification.html", {"request": request, "message3": message3})
        return templates.TemplateResponse("verification.html", {"request": request, "message2": message2})
    if verification_code2 == vcode2:
        print("account created")
        message = True
        create_user(db=db, email=email, first_name=first_name, last_name=last_name, password=password)
    return templates.TemplateResponse("verification.html", {"request": request, "message": message})


@app.post("/login")
def login_user(request: Request, user: LoginUser = Depends(LoginUser.as_form), db: Session = Depends(get_db)):
    print("HELLO ", user.email)
    request.session.pop("user_email_with_google", None)
    request.session.pop("user_name_with_google", None)
    request.session.pop("user_email_with_github", None)
    request.session.pop("user_name_with_github", None)
    request.session["user_email"] = user.email
    mail = get_user_by_email(db, email=user.email)
    print(mail)
    if not mail:
        message1 = True
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "message1": message1})

    if mail.password != user.password:
        message = True
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "message": message})

    return templates.TemplateResponse("predict_page.html", {"request": request,
                                                        "message": "User logged in successfully!"})




@app.get("/forget", response_class=HTMLResponse)
def gen_response(request: Request):
    return templates.TemplateResponse("forgetpassword.html", {"request": request})


@app.post("/forget", response_class=HTMLResponse)
def gen_response(request: Request, backgroundtask: BackgroundTasks, email: str = Form(...), password: str = Form(...),
                 newpassword: str = Form(...), ):
    print(email, password, newpassword)
    if password != newpassword:
        message1 = True
        return templates.TemplateResponse("forgetpassword.html", {"request": request, "message1": message1})
    backgroundtask.add_task(send_verification_code, email, verification_code)
    get_email_forget["email"] = email
    get_email_forget["newpassword"] = newpassword
    return RedirectResponse(url="/verification", status_code=303)


@app.get("/google-register")
async def google_reg(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri, prompt="select_account")


@app.get("/github-login")
async def githublogin():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={github_client_id}&prompt=consent",
        status_code=302,
    )


@app.get("/github-code")
async def github_code(code: str, request: Request, db: Session = Depends(get_db)):
    print(f"Received code: {code}")
    params = {
        "client_id": github_client_id,
        "client_secret": github_client_secret,
        "code": code,
    }
    try:
        headers = {"Accept": "application/json"}
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                url="https://github.com/login/oauth/access_token",
                params=params,
                headers=headers,
            )
            token_json = token_response.json()
            access_token = token_json.get("access_token")
            print(f"Access token: {access_token}")

            if not access_token:
                raise ValueError("Failed to retrieve access token.")

            # Fetch user details from GitHub API
            headers.update({"Authorization": f"Bearer {access_token}"})
            user_response = await client.get("https://api.github.com/user", headers=headers)
            user_data = user_response.json()
            print(f"GitHub user data: {user_data}")

            name = user_data.get("name")
            github_id = user_data.get("id")
            request.session.pop("user_email", None)
            request.session.pop("user_email_with_google", None)
            request.session.pop("user_name_with_google", None)
            request.session["user_email_with_github"] = user_data.get("id")
            request.session["user_name_with_github"] = user_data.get("name")

            print(name, github_id)
            # if not name or not github_id:
            #     raise ValueError("Incomplete user data from GitHub.")

            # Check if the user exists in the database
            existing_user = get_user_by_github(db, github_id)
            if existing_user:
                print(f"User exists: {existing_user}")
                message6 = True
                return templates.TemplateResponse(
                    "predict_page.html", {"request": request, "message6": message6}
                )
            if name is None:
                name = "NOT MENTIONED"
            # Create new user if not found
            new_user = create_user_with_github(db, name, github_id)
            print(f"New user created: {new_user}")
            message7 = True
            return templates.TemplateResponse(
                "predict_page.html", {"request": request, "message7": message7}
            )

    except Exception as e:
        print(f"Error occurred: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@app.get("/auth")
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get('userinfo')
        if userinfo:
            email = userinfo.get('email')
            name = userinfo.get('name')
            request.session.pop("user_email", None)
            request.session.pop("user_email_with_github", None)
            request.session.pop("user_name_with_github", None)
            request.session["user_email_with_google"] = userinfo.get('email')
            request.session["user_name_with_google"] = userinfo.get('name')

            print(f"User Email: {userinfo.get('email')}")
            print(f"User Name: {userinfo.get('name')}")
            get_data = get_user_by_email_google(db, email)
            print(get_data)
            if get_data:
                message4 = True
                return templates.TemplateResponse("predict_page.html", {"request": request,
                                                                        "message": "User  logged in successfully!",
                                                                        "message4": message4})
            #     return templates.TemplateResponse("register.html", context={"request": request, "message4": message4})

            db_user1 = create_user_with_google(db, email, name)
            print("user store in db", db_user1)
            message5 = True
            # print("User Info:", userinfo)  # Debugging purpose
    except OAuthError as e:
        return templates.TemplateResponse(
            "error.html", context={"request": request, "error": e.error}  # update this with error
        )
    return templates.TemplateResponse("predict_page.html", context={"request": request, "message5": message5})


@app.get("/profile", response_class=HTMLResponse)
def gen_response(request: Request, db: Session = Depends(get_db)):
    name = None
    email = None
    email = request.session.get("user_email")
    email_with_google = request.session.get("user_email_with_google")
    name_with_google = request.session.get("user_name_with_google")
    email_with_github = request.session.get("user_email_with_github")
    name_with_github = request.session.get("user_name_with_github")
    try:
        if email_with_google:
            print("GOOGLE")
            name = name_with_google
            email = email_with_google
        elif email_with_github:
            print("GITHUB")
            name = name_with_github
            if name is None:
                name = "NOT MENTIONED"
            email = email_with_github
            print("hello", name, email)
        else:
            print(email)
            user_info = get_user_by_email(db, email)
            print(user_info)
            fname = user_info.first_name
            lname = user_info.last_name
            name = f"{fname} {lname}"
    except Exception as e:
        print("ERROR", e)
    return templates.TemplateResponse("profile_settings.html", {"request": request, "email": email, "name": name})


@app.post("/profile", response_class=HTMLResponse)
def gen_response(request: Request, db: Session = Depends(get_db), password: str = Form(...),
                 newpassword: str = Form(...)):
    email = request.session.get("user_email")
    if email:
        user_info = get_user_by_email(db, email)

        fname = user_info.first_name
        lname = user_info.last_name
        name = f"{fname} {lname}"
        print(password, newpassword)
        if password != newpassword:
            message1 = True
            return templates.TemplateResponse("profile_settings.html",
                                              {"request": request, "message1": message1, "email": email, "name": name})
        # user_info = db.query(Register_With_Email).filter(Register_With_Email.email == email).first()  # Fetch the user instance
        if password == newpassword:
            if user_info:
                user_info = get_user_by_email(db, email)
                user_info.password = newpassword
                db.commit()
                db.refresh(user_info)
                message2 = True
                return templates.TemplateResponse("profile_settings.html",
                                                  {"request": request, "message2": message2, "email": email,
                                                   "name": name})

        return templates.TemplateResponse("profile_settings.html",
                                      {"request": request, "email": email, "name": name})

    email = request.session.get("user_email_with_google")
    name = request.session.get("user_name_with_google")
    email_with_github = request.session.get("user_email_with_github")
    name2 = request.session.get("user_name_with_github")
    if name:
        message4=True
        return templates.TemplateResponse("profile_settings.html",
                                      {"request": request, "email": email, "name": name,"message4":message4})
    if name2:
        email=email_with_github
        name=name2
        message3=True
        return templates.TemplateResponse("profile_settings.html",
                                      {"request": request, "email": email, "name": name,"message3":message3})







@app.post("/predict", response_class=HTMLResponse)
def get_form_data1(request: Request,Predict: PredictHouse = Depends(PredictHouse.as_form)):
    print("hello predict",Predict)
    return templates.TemplateResponse("predict_page.html", {"request": request})


@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    # Remove the user from the session or reset the session
    request.session.clear()
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
