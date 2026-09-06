"""Test-only signed licenses. Never include this file in a release package."""
import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from vocal_license import canonical,encode,device_fingerprint
from vocal_pipeline.paths import data_root

def provision(root,device=None,expires=None):
 root=Path(root).resolve()
 if root==Path(__file__).resolve().parent.parent:raise ValueError('Test licenses are forbidden in the real project')
 key=Ed25519PrivateKey.generate();now=datetime.now(timezone.utc)
 value=dict(schema=1,serial='VX-BETA-TEST-ONLY-0001',product='Vocal X',edition='Beta',device=device or device_fingerprint(),issued_at=(now-timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),expires_at=(expires or now+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),max_devices=1,version_prefix='0.1.')
 payload=canonical(value);token='VXLIC1.'+encode(payload)+'.'+encode(key.sign(payload))
 (root/'App').mkdir(exist_ok=True);(root/'App/license-public-key.json').write_text(json.dumps({'algorithm':'Ed25519','key':encode(key.public_key().public_bytes_raw())}))
 dest=data_root(root)/'License/activation.vxlicense';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(token,encoding='ascii')
 return token,key
