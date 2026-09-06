"""Developer-only offline issuer. The entire Tools/LicenseAdmin and Private tree must be excluded from releases."""
import argparse,hashlib,json,sqlite3,sys
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'App'))
from vocal_license import parse_request,canonical,encode,BETA_EXPIRES,timestamp,verify,mask
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dpapi import transform
PRIVATE=ROOT/'Private/LicenseAdmin'
def initialize(private=PRIVATE,public=ROOT/'App/license-public-key.json'):
 private=Path(private);private.mkdir(parents=True,exist_ok=True)
 keypath=private/'signing-key.dpapi';public=Path(public)
 if keypath.exists() or public.exists():raise ValueError('Key already exists. Refusing to overwrite.')
 key=Ed25519PrivateKey.generate();encrypted=transform(key.private_bytes_raw(),True)
 with keypath.open('xb') as f:f.write(encrypted)
 public.write_text(json.dumps({'algorithm':'Ed25519','key':encode(key.public_key().public_bytes_raw())}),encoding='ascii')
 return keypath

def issue(request,expires=BETA_EXPIRES,private=PRIVATE,now=None):
 private=Path(private);req=parse_request(request);now=now or datetime.now(timezone.utc);expiry=timestamp(expires)
 if expiry<=now or expiry>timestamp(BETA_EXPIRES):raise ValueError('Expiry must be in the future, no later than the beta deadline.')
 allowed=json.loads((private/'serial-hashes.json').read_text(encoding='ascii'))
 hashed=hashlib.sha256(req['serial'].encode('ascii')).hexdigest()
 if len(allowed)!=10 or len(set(allowed))!=10 or hashed not in allowed:raise ValueError('Serial not in the ten beta licenses.')
 with closing(sqlite3.connect(private/'issuance.sqlite',timeout=10)) as db, db:
  db.execute('CREATE TABLE IF NOT EXISTS licenses (serial_hash TEXT PRIMARY KEY, device TEXT NOT NULL, token TEXT NOT NULL)')
  db.execute('BEGIN IMMEDIATE')
  old=db.execute('SELECT device,token FROM licenses WHERE serial_hash=?',(hashed,)).fetchone()
  if old:
   if old[0]!=req['device']:raise ValueError('This serial is already bound to another device. Offline tokens cannot be remotely revoked.')
   return old[1]
  key=Ed25519PrivateKey.from_private_bytes(transform((private/'signing-key.dpapi').read_bytes(),False))
  value=dict(schema=1,serial=req['serial'],product='Vocal X',edition='Beta',device=req['device'],issued_at=now.strftime('%Y-%m-%dT%H:%M:%SZ'),expires_at=expires,max_devices=1,version_prefix='0.1.')
  payload=canonical(value);token='VXLIC1.'+encode(payload)+'.'+encode(key.sign(payload))
  verify(token,key.public_key().public_bytes_raw(),req['device'],now)
  db.execute('INSERT INTO licenses VALUES (?,?,?)',(hashed,req['device'],token))
 return token

def main():
 parser=argparse.ArgumentParser(description='Vocal X developer license issuer')
 parser.add_argument('action',choices=['init','issue']);parser.add_argument('--request-file',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--expires',default=BETA_EXPIRES)
 args=parser.parse_args()
 try:
  if args.action=='init':initialize();print('Signing key created in Private/LicenseAdmin; DO NOT DISTRIBUTE.');return 0
  if not args.request_file or not args.output:parser.error('issue requires --request-file and --output')
  if args.output.exists():raise ValueError('Output already exists; refusing to overwrite.')
  token=issue(args.request_file.read_text(encoding='utf-8-sig').strip(),args.expires)
  args.output.write_text(token,encoding='ascii');print('Activation token saved. Serial masked in console.');return 0
 except Exception as e:print('License operation failed: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
