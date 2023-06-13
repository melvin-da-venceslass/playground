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

from exceptional_response import *

from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional
from num2words import num2words

from pi_invoic_Writer import *
from invoic_Writer import *
from quote_Writer import *
from invoic_Writer_DC import *
from po_Writer import *
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
        


class Struct():
    def __init__(self, **entries):
        self.__dict__.update(entries)

class DayLog(BaseModel):
    name:str
    client:str
    jobDesc:str
    remarks:str
    time:str
    
class request(BaseModel):
    name: str
    name_ship: str
    address_bill: str
    address_ship: str
    cust_gstin:str
    atten: str
    invoice_date:int
    invoice_no:str
    p_order: str
    p_date: int
    line_item: str

    hsn:str
    item_gst:Optional[str]="18%"

    item_desc: str
    gst_type: str
    cost: int
    qty: int

    t_cost: Optional[str]

    gst_i_rate: str = "0%"
    gst_i_valu: Optional[str] = "₹0.00"

    gst_c_rate: str = "0%"
    gst_c_valu: Optional[str] = "0.00"

    gst_s_rate: str = "0%"
    gst_s_valu: Optional[str] = "0.00"

    st_value:Optional[str]
    gst_tot_value:Optional[str]
    t_cost_words: Optional[str]
    t_gst_valu_words: Optional[str]
    t_gst_valu: Optional[str]
    round_off:Optional[str]

    payment_mode:Optional[str] = "IMPS,UPI,NEFT,RTGS"
    mviis_gstin:Optional[str]= "33FHGPM2821H1ZI"


    delivery_note:Optional[str] = "NA"
    dispatch_thru:Optional[str] = "NA"
  
    payment_tearms:Optional[str]= "NA"

    delivery_tearms:Optional[str]= "NA"
   
    deliver_on:Optional[int]          
    destination:Optional[str]=""
    reference:str
    docType:str
    leadtime:str
    validity:str
    dc_checkbox:bool
 


class response(BaseModel):
    status: str

class CostingModel(BaseModel):
    proj_name:str
    lineitems:List[dict]
    discount:int
    profit:int
    cgst:int
    sgst:int
    igst:int
    gtotal:int

class PurchaseOrder(BaseModel):
    
    name:str
    address_bill: str
    cust_gstin: str
    docType: str
    reference: str
    atten:str
    invoice_no: str
    invoice_date: int
    vendor_quote: str
    vendor_quote_dte: int
    line_item: str
    hsn: str
    item_desc: str
    gst_type: str
    cost: int
    qty: int
    deliver_on: int
    deliver_by: str
    payment_terms: str
    delivery_terms: str
    t_cost: Optional[str]
    item_gst:Optional[str]="18%"

    gst_i_rate: str = "0%"
    gst_i_valu: Optional[str] = "₹0.00"

    gst_c_rate: str = "0%"
    gst_c_valu: Optional[str] = "0.00"

    gst_s_rate: str = "0%"
    gst_s_valu: Optional[str] = "0.00"

    st_value:Optional[str]
    gst_tot_value:Optional[str]
    t_cost_words: Optional[str]
    t_gst_valu_words: Optional[str]
    t_gst_valu: Optional[str]
    round_off:Optional[str]

    payment_mode:Optional[str] = "IMPS,UPI,NEFT,RTGS"
    mviis_gstin:Optional[str]= "33FHGPM2821H1ZI"



response_temp = response
request_temp = request
request_purch = PurchaseOrder

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


@app.get("/billing", response_class=HTMLResponse)
def home(request: Request,user = Depends(get_current_username)):
    return templates.TemplateResponse('index.html', context={'request': request})


@app.get("/dashboard/", response_class=HTMLResponse)
def dboard(request: Request,user = Depends(get_current_username)):
    return templates.TemplateResponse('documents.html', context={'request': request})    

@app.get("/pricing/", response_class=HTMLResponse)
def dboard(request: Request,user = Depends(get_current_username)):
    return templates.TemplateResponse('pricing.html', context={'request': request})    

@app.get("/po/", response_class=HTMLResponse)
def dboard(request: Request,user = Depends(get_current_username)):
    return templates.TemplateResponse('po.html', context={'request': request})    

@app.get("/timesheet/", response_class=HTMLResponse)
def dboard(request: Request,user = Depends(get_current_username)):
    return templates.TemplateResponse('jira.html', context={'request': request})  

@app.get("/documents/{value}")
async def get_documents(value):
    return mdb_client.get_documents(value)


@app.get("/documents/po/{value}")
async def get_documents(value):
    return mdb_client.get_po_documents(value)


@app.get("/customers")
async def list_customers():
    customers = mdb_client.get_customers_name("name")
    return {"customers": customers}


@app.get("/suppliers")
async def list_customers():
    customers = mdb_client.get_suppliers_name("name")
    return {"customers": customers}


@app.get("/customers/{customer}")
async def customer_address(customer):
    customer_obj = mdb_client.get_customer_info(customer)
    customer_address = customer_obj[0]["address"]
    customer_cname = customer_obj[0]["name"]
    customer_nname = customer_obj[0]["n_name"]
    return {"name":customer_cname, "nickname":customer_nname,"address": customer_address,"gstin":customer_obj[0]["gstin"],"attn":customer_obj[0]["attn"]}




@app.get("/suppliers/{supplier}")
async def customer_address(supplier):
    supplier_obj = mdb_client.get_supplier_info(supplier)
    supplier_address = supplier_obj[0]["address"]
    supplier_cname = supplier_obj[0]["name"]
    supplier_nname = supplier_obj[0]["n_name"]
    return {"name":supplier_cname, "nickname":supplier_nname,"address": supplier_address,"gstin":supplier_obj[0]["gstin"],"attn":supplier_obj[0]["attn"]}




@app.get("/records/{key}")
async def record_ids(key):
    return {"records":mdb_client.get_docment_nums(key)}

@app.get("/records/new/{key}")
async def create_new(key):
    return {"new_key":str(mdb_client.get_next_roll(key))}


@app.get("/records/get/{key}")
async def records_get(key):
    return {"DOCS":mdb_client.get_records(key)}




def date_gdp(date):
    date = date/1000
    return datetime.utcfromtimestamp(date).strftime('%d-%b-%Y')


def get_in_words(value):
    value = float(value)
    x = num2words(value, lang="en_IN", to='currency',currency='INR')    
    x = x.replace("euro", "rupees")
    x = x.replace("cents", "paise")
    x = x + " Only /-"
    x = x.title()
    return x


def costing(obj):

    obj.t_cost = obj.cost * obj.qty
    

    if obj.gst_type == "I":
        obj.gst_i_rate = "18%"
        obj.gst_i_valu = "{:.2f}".format(float(obj.t_cost * 0.18))

        obj.t_gst_valu = obj.gst_i_valu
        obj.t_gst_valu_words = get_in_words(obj.gst_i_valu)

    elif obj.gst_type == "C":
        obj.gst_c_rate = "9%"
        obj.gst_c_valu = "{:.2f}".format(float(obj.t_cost * 0.09))
        obj.gst_s_rate = "9%"
        obj.gst_s_valu = "{:.2f}".format(float(obj.t_cost * 0.09))

        obj.t_gst_valu = obj.t_cost * 0.18
        obj.t_gst_valu_words = get_in_words(obj.t_gst_valu)

    elif obj.gst_type == "SEZ":
        obj.gst_c_rate = "0%"
        obj.gst_c_valu = "{:.2f}".format(float(obj.t_cost * 0))
        obj.gst_s_rate = "0%"
        obj.gst_s_valu = "{:.2f}".format(float(obj.t_cost * 0))

        obj.t_gst_valu = obj.t_cost * 0
        obj.t_gst_valu_words = get_in_words(obj.t_gst_valu)



    obj.gst_tot_value = float(obj.t_cost) + float(obj.t_gst_valu)
    # obj.st_value =  math.floor(obj.gst_tot_value)
    obj.st_value =  round(obj.gst_tot_value)
    obj.round_off = obj.st_value - obj.gst_tot_value




    obj.t_cost_words = get_in_words(obj.st_value)
    

    obj.st_value = "{:.2f}".format(float(obj.st_value))
    obj.t_gst_valu = "{:.2f}".format(float(obj.t_gst_valu))

    return obj


def billing(obj):
    obj.invoice_date = date_gdp(obj.invoice_date)
    obj.p_date = date_gdp(obj.p_date)
    obj = costing(obj)
    return obj

def billing_po(obj):
    obj.invoice_date = date_gdp(obj.invoice_date)
    obj.vendor_quote_dte = date_gdp(obj.vendor_quote_dte)
    obj = costing(obj)
    return obj

def pre_formatting(obj):
    try:
        obj.cost =  "₹{:.2f}".format(float(obj.cost))
        obj.gst_tot_value =  "₹{:.2f}".format(float(obj.gst_tot_value))
        obj.round_off = "₹{:.2f}".format(float(obj.round_off))
        obj.st_value = "₹{:.2f}".format(float(obj.st_value))
        obj.t_cost = "₹{:.2f}".format(float(obj.t_cost))
        obj.t_gst_valu = "₹{:.2f}".format(float(obj.t_gst_valu))
        obj.qty = str(obj.qty)
        obj.deliver_on = date_gdp(obj.deliver_on)
        return obj
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


@app.post("/create_document")
async def create_invoice(request: Request, income: request_temp):
    try:
        obj = billing(income)
        obj = pre_formatting(obj)
        insertion = mdb_client.insert_new_document(dict(obj))
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
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return {"file":False}



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
