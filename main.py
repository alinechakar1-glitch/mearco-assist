"""MEARCO Assist prototype. Do not put real personal data into this demo."""
import os, sqlite3, io, csv, secrets, hashlib, time, hmac, re
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from openpyxl import load_workbook

ROOT=Path(__file__).parent
DB_PATH=os.environ.get('DB_PATH',str(ROOT/'assist_demo.sqlite3'))
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD')
SESSION_SECRET=os.environ.get('SESSION_SECRET')
PROVIDER_PASSWORD=os.environ.get('PROVIDER_PASSWORD','')
PUBLIC_INTAKE_ENABLED=os.environ.get('PUBLIC_INTAKE_ENABLED','0')=='1'
PUBLIC_TRACKING_ENABLED=os.environ.get('PUBLIC_TRACKING_ENABLED','0')=='1'
TRUSTED_ORIGINS=[v.strip().rstrip('/') for v in os.environ.get('TRUSTED_ORIGINS','').split(',') if v.strip()]
if not ADMIN_PASSWORD or not SESSION_SECRET:
    raise RuntimeError('Set ADMIN_PASSWORD and SESSION_SECRET environment variables before starting')
app=FastAPI(title='MEARCO Assist 24/7 — Standalone')

@app.get('/version')
def version(): return {'version': '0.2.3', 'csrf_protection': 'session-form-token'}

@app.middleware('http')
async def security_headers(request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    return response

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
        db.execute('CREATE TABLE IF NOT EXISTS public_tokens(case_id INTEGER PRIMARY KEY, token_hash TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS provider_jobs(case_id INTEGER PRIMARY KEY, provider_note TEXT, assigned_driver TEXT, updated_at TEXT)')
init_db()

def authorized(req): return bool(req.session.get('signed_in')) and req.session.get('role')=='admin'
def provider_authorized(req): return bool(req.session.get('signed_in')) and req.session.get('role')=='provider'
def new_csrf(req):
    if not req.session.get('csrf'): req.session['csrf']=secrets.token_urlsafe(24)
    return req.session['csrf']
def csrf_ok(req,token): return bool(token) and secrets.compare_digest(str(token),str(req.session.get('csrf','')))
def enforce_csrf(req,token):
    # A synchronizer CSRF token is generated on GET and required on every POST.
    # Do not compare Origin to Render's proxy-facing URL: proxies and browsers
    # may vary these headers. SameSite=Lax and a per-session secret token
    # protect the form without an unreliable deployment-specific origin check.
    if not csrf_ok(req, token):
        raise HTTPException(403, 'Invalid form token; refresh page')

def redirect(location): return RedirectResponse(location,status_code=303)
def render(req,name,**kw): return templates.TemplateResponse(req,name,{'logged_in':authorized(req),'provider_logged_in':provider_authorized(req),'csrf_token':new_csrf(req),'public_enabled':PUBLIC_INTAKE_ENABLED,**kw})

@app.get('/login',response_class=HTMLResponse)
def login_form(request:Request): return render(request,'login.html',error=None)
@app.post('/login')
def login(request:Request,password:str=Form(...),csrf_token:str=Form('')):
    enforce_csrf(request,csrf_token)
    if secrets.compare_digest(password,ADMIN_PASSWORD):
        request.session['signed_in']=True
        request.session['role']='admin'
        return redirect('/')
    return templates.TemplateResponse(request,'login.html',{'logged_in':False,'error':'Incorrect password'},status_code=401)
@app.post('/logout')
def logout(request:Request,csrf_token:str=Form('')):
    enforce_csrf(request,csrf_token)
    request.session.clear(); return redirect('/login')

@app.get('/',response_class=HTMLResponse)
def home(request:Request):
    if not authorized(request): return redirect('/login')
    with conn() as db:
        cases=db.execute('SELECT * FROM cases ORDER BY id DESC LIMIT 30').fetchall()
        stats={k:db.execute(q).fetchone()[0] for k,q in {'cases':'SELECT count(*) FROM cases','open':'SELECT count(*) FROM cases WHERE status NOT IN ("Completed","Cancelled")','policies':'SELECT count(*) FROM policies','pending':'SELECT count(*) FROM cases WHERE status IN ("New","Pending Dispatch")'}.items()}
    return render(request,'index.html',cases=cases,stats=stats)

@app.post('/cases')
def create_case(request:Request,client_name:str=Form(...),phone:str=Form(''),plate:str=Form(''),location:str=Form(''),case_type:str=Form('Towing'),notes:str=Form(''),csrf_token:str=Form('')):
    if not authorized(request): raise HTTPException(401)
    enforce_csrf(request,csrf_token)
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
def case_update(request:Request,case_id:int,status:str=Form(...),provider:str=Form(''),eta:str=Form(''),note:str=Form(''),csrf_token:str=Form('')):
    if not authorized(request): raise HTTPException(401)
    enforce_csrf(request,csrf_token)
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
def add_policy(request:Request,policy_number:str=Form(...),insured_name:str=Form(''),phone:str=Form(''),plate:str=Form(''),start_date:str=Form(''),end_date:str=Form(''),towing_entitlement:str=Form('Review'),status:str=Form('Unknown'),csrf_token:str=Form('')):
    if not authorized(request): raise HTTPException(401)
    enforce_csrf(request,csrf_token)
    with conn() as db:
        db.execute('INSERT INTO policies(policy_number,insured_name,phone,plate,start_date,end_date,towing_entitlement,status) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(policy_number) DO UPDATE SET insured_name=excluded.insured_name,phone=excluded.phone,plate=excluded.plate,start_date=excluded.start_date,end_date=excluded.end_date,towing_entitlement=excluded.towing_entitlement,status=excluded.status',(policy_number,insured_name,phone,plate,start_date,end_date,towing_entitlement,status))
    return redirect('/policies')

HEADERS=['policy_number','insured_name','phone','plate','start_date','end_date','towing_entitlement','status']
@app.post('/policies/import')
async def import_policies(request:Request,file:UploadFile=File(...),csrf_token:str=Form('')):
    if not authorized(request): raise HTTPException(401)
    enforce_csrf(request,csrf_token)
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


# Customer requests are restricted by default. Before enabling, configure a durable
# data volume, staffed monitoring, incident response and privacy controls.
REQUEST_LIMIT={}   # process-local abuse friction; use edge/WAF rate limits in production

def limit_request(request):
    ip=request.client.host if request.client else 'unknown'
    now_t=time.monotonic()
    hits=[t for t in REQUEST_LIMIT.get(ip,[]) if now_t-t<600]
    if len(hits)>=5: raise HTTPException(429,'Too many requests. Please contact MEARCO directly.')
    hits.append(now_t); REQUEST_LIMIT[ip]=hits

def validate_fields(name,phone,plate,location,notes):
    if not 2<=len(name.strip())<=120: raise HTTPException(400,'Please enter your name (2–120 characters)')
    if not 6<=len(phone.strip())<=30: raise HTTPException(400,'Please enter a valid contact number')
    if len(plate)>40 or len(location)>350 or len(notes)>2500: raise HTTPException(400,'Request field too long')

@app.get('/assist',response_class=HTMLResponse)
def assist(request:Request):
    return render(request,'assist.html',intake_enabled=PUBLIC_INTAKE_ENABLED)

@app.post('/assist',response_class=HTMLResponse)
def customer_request(request:Request,client_name:str=Form(...),phone:str=Form(...),plate:str=Form(''),location:str=Form(''),case_type:str=Form('Towing'),notes:str=Form(''),is_safe:str=Form(''),website:str=Form(''),csrf_token:str=Form('')):
    if not PUBLIC_INTAKE_ENABLED: raise HTTPException(503,'Online intake is not activated. Call MEARCO for help.')
    enforce_csrf(request,csrf_token)
    if website: raise HTTPException(400,'Invalid request')
    limit_request(request)
    validate_fields(client_name,phone,plate,location,notes)
    if case_type not in ['Towing','Motor accident','Complaint','Claim follow-up']: raise HTTPException(400,'Unsupported request')
    if is_safe not in ['Yes','No','Unsure']: raise HTTPException(400,'Please answer the safety question')
    with conn() as db:
        cur=db.execute('INSERT INTO cases(created_at,client_name,phone,plate,location,case_type,status,notes,provider,eta) VALUES(?,?,?,?,?,?,?,?,?,?)',(now(),client_name.strip(),phone.strip(),plate.strip(),location.strip(),case_type,'Escalated' if is_safe!='Yes' else 'New',f'SAFETY: {is_safe}. {notes.strip()}','',''))
        case_id=cur.lastrowid
        token=secrets.token_urlsafe(24)
        db.execute('INSERT INTO public_tokens(case_id,token_hash) VALUES(?,?)',(case_id,hashlib.sha256(token.encode()).hexdigest()))
        db.execute('INSERT INTO case_events(case_id,created_at,actor,event) VALUES(?,?,?,?)',(case_id,now(),'Client','Online assistance request submitted; safety: '+is_safe))
    return render(request,'submitted.html',case_id=case_id,tracking_token=token,tracking_enabled=PUBLIC_TRACKING_ENABLED)

@app.get('/track',response_class=HTMLResponse)
def track_page(request:Request,case:str='',token:str=''):
    status=None; invalid=False
    if case or token:
        try: cid=int(case.replace('MA-',''))
        except (TypeError,ValueError): cid=0
        if not PUBLIC_TRACKING_ENABLED or not cid or len(token)<20: invalid=True
        else:
            with conn() as db:
                row=db.execute('SELECT token_hash FROM public_tokens WHERE case_id=?',(cid,)).fetchone()
                if not row or not hmac.compare_digest(row['token_hash'],hashlib.sha256(token.encode()).hexdigest()): invalid=True
                else:
                    result=db.execute('SELECT id,status,case_type,eta FROM cases WHERE id=?',(cid,)).fetchone()
                    status=dict(result) if result else None
    return render(request,'track.html',status=status,invalid=invalid,tracking_enabled=PUBLIC_TRACKING_ENABLED)

@app.get('/provider/login',response_class=HTMLResponse)
def provider_login_page(request:Request): return render(request,'provider_login.html',error=None)

@app.post('/provider/login')
def provider_login(request:Request,password:str=Form(...),csrf_token:str=Form('')):
    enforce_csrf(request,csrf_token)
    if PROVIDER_PASSWORD and secrets.compare_digest(password,PROVIDER_PASSWORD):
        request.session['signed_in']=True;request.session['role']='provider'
        return redirect('/provider')
    return templates.TemplateResponse(request,'provider_login.html',{'csrf_token':new_csrf(request),'logged_in':False,'provider_logged_in':False,'error':'Incorrect credentials'},status_code=401)

@app.get('/provider',response_class=HTMLResponse)
def provider_jobs(request:Request):
    if not provider_authorized(request): return redirect('/provider/login')
    with conn() as db:
        rows=db.execute("SELECT c.*,p.assigned_driver,p.provider_note FROM cases c LEFT JOIN provider_jobs p ON p.case_id=c.id WHERE c.provider != '' AND c.case_type='Towing' AND c.status NOT IN ('Completed','Cancelled') ORDER BY c.id DESC LIMIT 100").fetchall()
    return render(request,'provider.html',jobs=rows)

@app.post('/provider/jobs/{case_id}/update')
def provider_job_update(request:Request,case_id:int,status:str=Form(...),driver:str=Form(''),note:str=Form(''),csrf_token:str=Form('')):
    if not provider_authorized(request): raise HTTPException(401)
    enforce_csrf(request,csrf_token)
    if status not in ['Assigned','En Route','Arrived','Completed']: raise HTTPException(400,'Status not allowed')
    with conn() as db:
        case=db.execute("SELECT id FROM cases WHERE id=? AND provider!='' AND case_type='Towing'",(case_id,)).fetchone()
        if not case: raise HTTPException(404)
        db.execute('UPDATE cases SET status=? WHERE id=?',(status,case_id))
        db.execute('INSERT INTO provider_jobs(case_id,assigned_driver,provider_note,updated_at) VALUES(?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET assigned_driver=excluded.assigned_driver,provider_note=excluded.provider_note,updated_at=excluded.updated_at',(case_id,driver[:120],note[:1000],now()))
        db.execute('INSERT INTO case_events(case_id,created_at,actor,event) VALUES(?,?,?,?)',(case_id,now(),'Towing provider',f'{status}; driver: {driver[:120]}; note: {note[:1000]}'))
    return redirect('/provider')
