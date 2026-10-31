"""Helper tests (requires project backend requirements)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from main import _plate, _tow_kind, _entitlement

def test_normalize_plate():
 assert _plate('793131/B') == _plate('793131 b')
 assert _plate('18012/S') == '18012S'

def test_kind():
 assert _tow_kind('Mechanical')=='mechanical'
 assert _tow_kind('accident')=='accident'

def test_entitlement_explicit_only():
 assert _entitlement('Towing 75 km- 2 Mechanical')==2
 assert _entitlement('Accident unlimited')==0
