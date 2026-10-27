"""MEARCO Assist prototype. Do not put real personal data into this demo."""
import os, sqlite3, io, csv, secrets
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from openpyxl import load_workbook

ROOT=Path(__file__).parent
DB_PATH=os.environ.get('DB_PATH',str(ROOT/'assist_demo.sqlite3'))
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD')
SESSION_SECRET=os.environ.get('SESSION_SECRET')
if not ADMIN_PASSWORD or not SESSION_SECRET:
    raise RuntimeError('Set ADMIN_PASSWORD and SESSION_SECRET environment variables before starting')
app=FastAPI(title='MEARCO Assist 24/7 — Prototype')
app.add_middleware(SessionMiddleware,secret_key=SESSION_SECRET,https_only=os.environ.get('COOKIE_SECURE','1')=='1',same_site='lax')
app.mount('/static',StaticFiles(directory=str(ROOT/'static')),name='static')
templates=Jinja2Templates(directory=str(ROOT/'templates'))

@contextmanager
def conn():
    db=sqlite3.connect(DB_PATH, timeout=20)
    db.row_factory=sqlite3.Row
    try:
        yield db
        db.commit()
    finally: db.close()

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def init_db():
    with conn() as db:
        db.execute('CREATE TABLE IF NOT EXISTS policies(id INTEGER PRIMARY KEY,policy_number TEXT NOT NULL UNIQUE,insured_name TEXT,phone TEXT,plate TEXT,start_date TEXT,end_date TEXT,towing_entitlement TEXT DEFAULT "Review",status TEXT DEFAULT "Unknown")')
        db.execute('CREATE TABLE IF NOT EXISTS cases(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,client_name TEXT NOT NULL,phone TEXT,plate TEXT,location TEXT,case_type TEXT,status TEXT,notes TEXT,provider TEXT,eta TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS case_events(id INTEGER PRIMARY KEY,case_id INTEGER NOT NULL,created_at TEXT NOT NULL,actor TEXT NOT NULL,event TEXT NOT NULL)')
init_db()

def authorized(req): return bool(req.session.get('signed_in'))
def redirect(location): return RedirectResponse(location,status_code=303)
def render(req,name,**kw): return templates.TemplateResponse(req,name,{'logged_in':authorized(req),**kw})

@app.get('/login',response_class=HTMLResponse)
def login_form(request:Request): return render(request,'login.html',error=None)
@app.post('/login')
def login(request:Request,password:str=Form(...)):
    if secrets.compare_digest(password,ADMIN_PASSWORD):
        request.session['signed_in']=True
        return redirect('/')
    return templates.TemplateResponse(request,'login.html',{'logged_in':False,'error':'Incorrect password'},status_code=401)
@app.post('/logout')
def logout(request:Request):
    request.session.clear(); return redirect('/login')

@app.get('/',response_class=HTMLResponse)
def home(request:Request):
    if not authorized(request): return redirect('/login')
    with conn() as db:
        cases=db.execute('SELECT * FROM cases ORDER BY id DESC LIMIT 30').fetchall()
        stats={k:db.execute(q).fetchone()[0] for k,q in {'cases':'SELECT count(*) FROM cases','open':'SELECT count(*) FROM cases WHERE status NOT IN ("Completed","Cancelled")','policies':'SELECT count(*) FROM policies','pending':'SELECT count(*) FROM cases WHERE status IN ("New","Pending Dispatch")'}.items()}
    return render(request,'index.html',cases=cases,stats=stats)

@app.post('/cases')
def create_case(request:Request,client_name:str=Form(...),phone:str=Form(''),plate:str=Form(''),location:str=Form(''),case_type:str=Form('Towing'),notes:str=Form('')):
    if not authorized(request): raise HTTPException(401)
    if not client_name.strip(): raise HTTPException(400,'Client name required')
    with conn() as db:
        cur=db.execute('INSERT INTO cases(created_at,client_name,phone,plate,location,case_type,status,notes,provider,eta) VALUES(?,?,?,?,?,?,?,?,?,?)',(now(),client_name.strip(),phone,plate,location,case_type,'New',notes,'',''))
        db.execute('INSERT INTO case_events(case_id,created_at,actor,event) VALUES(?,?,?,?)',(cur.lastrowid,now(),'MEARCO operator','Case created'))
    return redirect('/')

STATUS_CHOICES=['New','Pending Dispatch','Assigned','En Route','Arrived','Completed','Escalated','Cancelled']
@app.get('/cases/{case_id}',response_class=HTMLResponse)
def case_detail(request:Request,case_id:int):
    if not authorized(request): return redirect('/login')
    with conn() as db:
        case=db.execute('SELECT * FROM cases WHERE id=?',(case_id,)).fetchone()
        events=db.execute('SELECT * FROM case_events WHERE case_id=? ORDER BY id DESC',(case_id,)).fetchall()
    if not case: raise HTTPException(404)
    return render(request,'case.html',case=case,events=events,status_choices=STATUS_CHOICES)
@app.post('/cases/{case_id}/update')
def case_update(request:Request,case_id:int,status:str=Form(...),provider:str=Form(''),eta:str=Form(''),note:str=Form('')):
    if not authorized(request): raise HTTPException(401)
    if status not in STATUS_CHOICES: raise HTTPException(400,'Invalid status')
    with conn() as db:
        if not db.execute('SELECT id FROM cases WHERE id=?',(case_id,)).fetchone(): raise HTTPException(404)
        db.execute('UPDATE cases SET status=?,provider=?,eta=? WHERE id=?',(status,provider,eta,case_id))
        db.execute('INSERT INTO case_events(case_id,created_at,actor,event) VALUES(?,?,?,?)',(case_id,now(),'MEARCO operator',f'Status: {status}; Provider: {provider}; ETA: {eta}; Note: {note}'))
    return redirect(f'/cases/{case_id}')

@app.get('/policies',response_class=HTMLResponse)
def policies(request:Request,q:str=''):
    if not authorized(request): return redirect('/login')
    with conn() as db:
        rows=db.execute('SELECT * FROM policies WHERE policy_number LIKE ? OR insured_name LIKE ? OR plate LIKE ? ORDER BY id DESC LIMIT 100',tuple('%'+q+'%' for _ in range(3))).fetchall()
    return render(request,'policies.html',policies=rows,q=q)
@app.post('/policies')
def add_policy(request:Request,policy_number:str=Form(...),insured_name:str=Form(''),phone:str=Form(''),plate:str=Form(''),start_date:str=Form(''),end_date:str=Form(''),towing_entitlement:str=Form('Review'),status:str=Form('Unknown')):
    if not authorized(request): raise HTTPException(401)
    with conn() as db:
        db.execute('INSERT INTO policies(policy_number,insured_name,phone,plate,start_date,end_date,towing_entitlement,status) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(policy_number) DO UPDATE SET insured_name=excluded.insured_name,phone=excluded.phone,plate=excluded.plate,start_date=excluded.start_date,end_date=excluded.end_date,towing_entitlement=excluded.towing_entitlement,status=excluded.status',(policy_number,insured_name,phone,plate,start_date,end_date,towing_entitlement,status))
    return redirect('/policies')

HEADERS=['policy_number','insured_name','phone','plate','start_date','end_date','towing_entitlement','status']
@app.post('/policies/import')
async def import_policies(request:Request,file:UploadFile=File(...)):
    if not authorized(request): raise HTTPException(401)
    data=await file.read()
    if len(data)>5_000_000: raise HTTPException(413,'File too large (5 MB maximum)')
    fname=(file.filename or '').lower()
    if fname.endswith('.xlsx'):
        try:
            book=load_workbook(io.BytesIO(data),read_only=True,data_only=True)
            sheet=book.active
            iterator=sheet.iter_rows(values_only=True)
        except Exception: raise HTTPException(400,'Unable to read XLSX file')
    elif fname.endswith('.csv'):
        try: iterator=csv.reader(io.StringIO(data.decode('utf-8-sig')))
        except Exception: raise HTTPException(400,'Unable to read CSV file')
    else: raise HTTPException(400,'Only XLSX and CSV are supported')
    headers=[str(x).strip().lower() if x is not None else '' for x in next(iterator,[])]
    if 'policy_number' not in headers: raise HTTPException(400,'Missing policy_number header. Download the sample template and try again.')
    positions={h:headers.index(h) for h in HEADERS if h in headers}
    parsed=[]
    for row in iterator:
        if len(parsed)>=10000: raise HTTPException(400,'Import limited to 10,000 records')
        d={h:str(row[i]).strip() if i<len(row) and row[i] is not None else '' for h,i in positions.items()}
        if d.get('policy_number'): parsed.append(d)
    with conn() as db:
        for d in parsed:
            vals=[d.get(h,'') for h in HEADERS]
            db.execute('INSERT INTO policies('+','.join(HEADERS)+') VALUES('+','.join('?' for _ in HEADERS)+') ON CONFLICT(policy_number) DO UPDATE SET '+','.join(f'{h}=excluded.{h}' for h in HEADERS[1:]),vals)
    return redirect('/policies')
@app.get('/health')
def health(): return {'status':'ok','app':'MEARCO Assist demo'}
