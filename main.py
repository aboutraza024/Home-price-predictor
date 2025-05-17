from models import get_user_by_email,get_user_by_email_google,get_user_by_github,create_user_with_github,create_user_with_google,create_user
from models import UserCreate,LoginUser,Register_With_Google,Register_With_Github,Register_With_Email
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import create_engine, Integer, String, Column
from auth import send_verification_code
import random
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi import FastAPI, Form, Depends, HTTPException, Request, BackgroundTasks,File,UploadFile
# from fastapi.staticfiles import StaticFiles
from models import app,SessionLocal
get_email={}
get_email_forget={}

def v_code():
    return random.randint(100000, 999999)

verification_code=v_code() # check every one get unique code


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
    get_email["f_name"]=user.first_name
    get_email["l_name"] = user.last_name
    get_email["email"] = user.email
    get_email["password"] = user.password
    print("Hello",user)
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        message3=True
        return templates.TemplateResponse("register.html", {"request": request,"message3":message3})
    backgroundtask.add_task(send_verification_code, user.email, verification_code)
    return RedirectResponse(url="/verification", status_code=303)


@app.post("/verification", response_class=HTMLResponse)
def verify_code(request: Request,backgroundtask:BackgroundTasks, vcode1: str = Form(...),db: Session = Depends(get_db)):
    email=get_email.get("email")
    first_name=get_email.get("f_name")
    last_name = get_email.get("l_name")
    password = get_email.get("password")
    newpassword=get_email_forget.get("newpassword")
    password1=get_email_forget.get("password")
    email2=get_email_forget.get("email")
    print(email)
    print("mail",email,"fname",first_name,"lname",last_name,"password",password)
    print(f"Verification code received: {vcode1}")
    vcode2=int(vcode1)
    verification_code2=int(verification_code)
    if newpassword:
        if verification_code2 == vcode2:
            user = db.query(Register_With_Email).filter(Register_With_Email.email == email2).first()  # Fetch the user instance
            if user:
                user.password = newpassword
                db.commit()
                db.refresh(user)
                message2 = True
            else:
                message2 = False
        return templates.TemplateResponse("verification.html", {"request": request, "message2": message2})
    if verification_code2==vcode2:
        print("account created")
        message=True
        create_user(db=db, email=email,first_name=first_name,last_name=last_name,password=password)
    return templates.TemplateResponse("verification.html", {"request": request,"message":message})

@app.post("/login")
def login_user(request: Request, user: LoginUser = Depends(LoginUser.as_form), db: Session = Depends(get_db)):
    print("HELLO ",user.email)
    mail = get_user_by_email(db, email=user.email)
    print(mail)
    if not mail or mail.password != user.password:
        message=True
        return templates.TemplateResponse("login.html", {"request": request,
                                                                "message": message})
    return templates.TemplateResponse("predict_page.html", {"request": request,
                                                        "message": "User logged in successfully!"})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)