import uvicorn
import math
from fastapi import FastAPI, Request ,Depends, HTTPException,status,Form
from fastapi.responses import FileResponse, HTMLResponse
from starlette.exceptions import HTTPException 
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import json

from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional
from num2words import num2words
import base64
import sys,time,os

security = HTTPBasic()

BASEURL = ""

def user_verification(un,pw):
    user ={}
    if un=="admin" and pw=="password*9":
        user["username"] = "admin"
        user["password"] = "password*9"
    else:
        user = False

    if user:
        token = user["username"]+":"+user["password"]
        token = bytes(token, 'utf-8')
        token = str(base64.b64encode(token)).strip("b")
        token = token.strip("'")
        # user.pop("_id")
        user.pop("password")
        user["token"] =token
        return user
    
    else:
        return False

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    user = user_verification(credentials.username,credentials.password)
    if user:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    
app = FastAPI(title="MVIIS Invoicing Application.")



origins = [
    "https://localhost", "http://localhost",
    "https://localhost:7297", "http://localhost:7297",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get('/favicon.ico')
async def favicon():
    return FileResponse("static/favicon.png")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):#,user = Depends(get_current_username)):
    return templates.TemplateResponse('index.html', context={'request': request})

@app.get("/manage-product.html", response_class=HTMLResponse)
def home(request: Request):#,user = Depends(get_current_username)):
    return templates.TemplateResponse('manage-product.html', context={'request': request})


@app.get("/order.html", response_class=HTMLResponse)
def home(request: Request):#,user = Depends(get_current_username)):
    return templates.TemplateResponse('order.html', context={'request': request})


@app.get("/getProducts")
def get_products(request:Request):
    return Json{
        [{
            "product_id":1,
            "product_name":"rice",
            "product_price_per_unit":10},
         {
            "product_id":2,
            "product_name":"dhal",
            "product_price_per_unit":20},
          {
            "product_id":3,
            "product_name":"soap",
            "product_price_per_unit":30},
          {
            "product_id":4,
            "product_name":"toothpaste",
            "product_price_per_unit":40}
          ]
        
    }
if __name__ == "__main__":
   uvicorn.run("main:app",reload=True,
               host='0.0.0.0', port=5000, workers=1)
