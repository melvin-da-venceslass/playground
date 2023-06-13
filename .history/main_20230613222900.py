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
def home(request: Request,user = Depends(get_current_username)):
    return templates.TemplateResponse('index.html', context={'request': request})


@app.post("/create_po")
async def create_purchaseorder(request: Request, income: request_purch):
    try:
        
        obj = billing_po(income)
        obj = pre_formatting(obj)
        insertion = mdb_client.insert_new_po_document(dict(obj))
        if insertion == True:
            if obj.docType=="Purchase Order" :
                po_writter(obj)
                return {"file":obj.invoice_no,"data":obj,"url":BASEURL +"/get_document/"+obj.invoice_no+".pdf"}
        else:
            return {"file":False}

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return {"file":False}

@app.post("/update_po")
async def create_purchaseorder(request: Request, income: request_purch):
    try:
        
        obj = billing_po(income)
        obj = pre_formatting(obj)
        insertion = mdb_client.update_old_po_document(dict(obj))
        if insertion == True:
            if obj.docType=="Purchase Order" :
                po_writter(obj)
                return {"file":obj.invoice_no,"data":obj,"url":BASEURL +"/get_document/"+obj.invoice_no+".pdf"}
        else:
            return {"file":False}

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return {"file":False}




@app.post("/update_document")
async def update_document(request: Request, income: request_temp):
    try:
        obj = billing(income)
        obj = pre_formatting(obj)
        insertion = mdb_client.update_old_document(dict(obj))
        if insertion == True:
            if obj.docType=="Invoice + DC" :
                writter(obj)
                if obj.dc_checkbox==True:
                    dc_writter(obj)
                    return {"file":obj.invoice_no,"data":obj,"url":BASEURL +"/get_document/"+obj.invoice_no+".pdf","url_dc":BASEURL +"/get_document/"+obj.delivery_note+".pdf",}
                else:
                    return {"file":obj.invoice_no,"data":obj,"url":BASEURL +"/get_document/"+obj.invoice_no+".pdf","url_dc":None,}

            elif obj.docType=="PRO FORMA":
                pi_writter(obj)
                return {"file":obj.invoice_no,"data":obj,"url":BASEURL +"/get_document/"+obj.invoice_no+".pdf","url_dc":BASEURL +"/get_document/"+obj.delivery_note+".pdf",}

            elif obj.docType=="Quotation":
                q_writter(obj)
                return {"file":obj.invoice_no,"data":obj,"url":BASEURL +"/get_document/"+obj.invoice_no+".pdf","url_dc":BASEURL +"/get_document/"+obj.delivery_note+".pdf",}

        else:
            return {"file":False}

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return {"file":False}



def date_gpd_mdb(date):
    x = datetime.strptime(date, '%Y-%m-%d').strftime('%d-%b-%Y')
    return x


@app.get("/download/{doc}",response_class=FileResponse)
async def download_(doc):
    document_ = mdb_client.get_documents(doc)
    document_["invoice_date"] = date_gpd_mdb(document_["invoice_date"])
    document_["deliver_on"] = date_gpd_mdb(document_["deliver_on"])
    document_["p_date"] = date_gpd_mdb(document_["p_date"])
    
    if "IN-" in doc:
        writter(document_)

    elif "PI-" in doc:
        pi_writter(document_)
    
    elif "Q-" in doc:
        q_writter(document_)
    return str(doc)+".pdf"





@app.get("/get_document/{invs}",response_class=FileResponse)
async def create_invoice(invs):
    return invs


@app.get("/costing/Projects/{qry}")
async def get_proj_cost(qry):
    return mdb_client.get_proj_costing(qry)

@app.get("/costing/Projects/")
async def get_proj():
    return mdb_client.get_proj()

@app.get("/pricing/products/")
async def get_prod():
    return mdb_client.get_products()


@app.get("/pricing/products/{key}")
async def get_prod_(key):
    try:
        return mdb_client.get_product_price(key)
    except:
        return ""


@app.post("/costing/new/")
async def newCosting_document(request: Request, income: CostingModel):
    try:
        mdb_client.create_new_document(dict(income))
        return {"file":True} 

    except Exception as error_obj:
        print(error_obj)
        return {"file":False}


@app.post("/daylog")
async def create_day_log(request:Request, name: str= Form(...), client: str= Form(...),
                                        job: str= Form(...), hrs: str= Form(...),
                                        remarks: str= Form(...),date:str=Form(...)):
    try:
        dataframe = {"name":name.upper(), "time":hrs, "remarks":remarks.upper(), "client":client.upper(), "job":job.upper(), "date":date}
        
        mdb_client.create_new_entry(dataframe)
        return templates.TemplateResponse('sucess.html', context={'request': request})
    except Exception as error_obj:
        print(error_obj)
        return {"file":False}



# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     resp = dict(status="failed",remarks=str(exc),errorCode="422",errorType="Validation Error")
#     resp = dict(layer_4(**resp))
#     return JSONResponse(status_code=422,content=resp)


# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request, exc):
#     exception_handlers = {  404: error_404(request,exc,templates,layer_4,JSONResponse,auth_re),
#                             401: error_401(exc,JSONResponse,auth_re),
#                             500: error_500(exc,JSONResponse,auth_re)
#                         }
#     return exception_handlers.get(exc.status_code)


if __name__ == "__main__":
   uvicorn.run("main:app",reload=True,
               host='0.0.0.0', port=8000, workers=1)
