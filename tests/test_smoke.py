"""Run with: pip install pytest; pytest tests -q (from project root)."""
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','backend'))
os.environ.setdefault('DATABASE_URL','sqlite:///./mearco_test.db')
os.environ.setdefault('JWT_SECRET','local-testing-only-long-secret')
from fastapi.testclient import TestClient
from main import app

def test_health():
 r=TestClient(app).get('/health');assert r.status_code==200;assert r.json()['real_payments'] is False

def test_private_endpoints():
 c=TestClient(app)
 for path in ['/policies','/cases','/balances','/providers','/payments','/admin/summary']:
  assert c.get(path).status_code==401

def test_auth_bad_login():
 assert TestClient(app).post('/auth/login',json={'username':'invalid','password':'wrong'}).status_code==401
