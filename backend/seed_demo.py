from main import SessionLocal,User,Provider,crypt
with SessionLocal() as s:
 if not s.query(User).count():
  for name,role,party in [('admin_demo','admin',None),('staff_demo','staff',None),('broker_demo','broker','BR001'),('customer_demo','customer','C001')]:
   import secrets
   pw=secrets.token_urlsafe(12)
   s.add(User(username=name,pw=crypt.hash(pw),role=role,party_code=party))
   print(f'{name}: {pw} (save securely; displayed once)')
 if not s.query(Provider).count():
  s.add_all([Provider(name='DEMO TOW PROVIDER - NOT REAL',kind='towing',area='Jbeil',phone=''),Provider(name='DEMO GARAGE - NOT REAL',kind='garage',area='Jounieh',phone='')])
 s.commit()
