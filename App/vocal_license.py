"""Public-key-only offline license protocol. No serial allow-list or signing key."""
import base64, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
PRODUCT='Vocal X'
EDITION='Beta'
APP_VERSION='0.1.0-beta.1'
BETA_EXPIRES='2027-01-01T00:00:00Z'  # Exclusive UTC boundary: includes 31 December 2026.
SERIAL=re.compile(r'VX-BETA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\Z')
FINGERPRINT=re.compile(r'[0-9a-f]{64}\Z')
class LicenseError(ValueError):
 def __init__(self,code):self.code=code;super().__init__(code)
MESSAGES={
 'public_key':('Die Lizenzprüfung ist unvollständig installiert. Bitte Vocal X reparieren.','License verification is not installed correctly. Please repair Vocal X.'),
 'serial':('Ungültiges Seriennummernformat.','Invalid serial number format.'),
 'token':('Ungültiger oder beschädigter Activation Token.','Invalid or damaged activation token.'),
 'signature':('Die Lizenzsignatur ist ungültig.','License signature verification failed.'),
 'device':('Diese Lizenz gehört zu einem anderen Gerät.','This license belongs to another device.'),
 'expired':('Diese Beta-Lizenz ist abgelaufen.','This beta license has expired.'),
 'clock':('Bitte Datum und Uhrzeit des PCs prüfen.','Please check this PC’s date and time.'),
 'version':('Diese Lizenz gilt nicht für diese App-Version.','This license does not cover this app version.'),
 'fingerprint':('Die stabile Gerätekennung konnte nicht gelesen werden.','The stable device identifier could not be read.'),
 'missing':('Vocal X ist noch nicht aktiviert.','Vocal X has not been activated yet.')}
def message(error,language='de'):return MESSAGES.get(error.code,MESSAGES['token'])[language=='en']
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def encode(data):return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')
def decode(value):
 if not isinstance(value,str) or len(value)>32768 or not re.fullmatch('[A-Za-z0-9_-]+',value):raise LicenseError('token')
 try:return base64.b64decode(value+'='*(-len(value)%4),altchars=b'-_',validate=True)
 except ValueError as e:raise LicenseError('token') from e
def serial(value):
 value=str(value).strip().upper()
 if not SERIAL.fullmatch(value):raise LicenseError('serial')
 return value
def mask(value):return 'VX-BETA-****-****-'+serial(value)[-4:]
def timestamp(value):
 try:
  dt=datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
  return dt
 except (ValueError,TypeError):raise LicenseError('token')
def fingerprint_from(values):
 # Fixed components only; USB devices, NICs, username and hostname are excluded.
 required=('machine_guid','system_manufacturer','system_product')
 if any(not isinstance(values.get(k),str) or not values[k].strip() for k in required):raise LicenseError('fingerprint')
 return hashlib.sha256(canonical({'schema':'VX-device-v1',**{k:values[k].strip().casefold() for k in required}})).hexdigest()
def device_fingerprint():
 import winreg
 try:
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Cryptography',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:guid=winreg.QueryValueEx(key,'MachineGuid')[0]
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\BIOS') as key:
   maker=winreg.QueryValueEx(key,'SystemManufacturer')[0];product=winreg.QueryValueEx(key,'SystemProductName')[0]
  return fingerprint_from(dict(machine_guid=guid,system_manufacturer=maker,system_product=product))
 except OSError as e:raise LicenseError('fingerprint') from e
def request_code(serial_number,device):
 if not FINGERPRINT.fullmatch(device):raise LicenseError('fingerprint')
 return 'VXREQ1.'+encode(canonical({'product':PRODUCT,'serial':serial(serial_number),'device':device,'schema':1}))
def parse_request(code):
 try:
  prefix,data=code.strip().split('.')
  if prefix!='VXREQ1':raise LicenseError('token')
  value=json.loads(decode(data))
  if set(value)!={'product','serial','device','schema'} or value['product']!=PRODUCT or value['schema']!=1:raise LicenseError('token')
  value['serial']=serial(value['serial'])
  if not FINGERPRINT.fullmatch(value['device']):raise LicenseError('fingerprint')
  return value
 except (ValueError,TypeError,KeyError,AttributeError) as e:
  if isinstance(e,LicenseError):raise
  raise LicenseError('token') from e
def verify(token,public_key,device,now=None,version=APP_VERSION):
 try:
  prefix,body,sig=token.strip().split('.')
  if prefix!='VXLIC1':raise LicenseError('token')
  payload=decode(body);signature=decode(sig)
  Ed25519PublicKey.from_public_bytes(public_key).verify(signature,payload)
  value=json.loads(payload)
  if canonical(value)!=payload:raise LicenseError('token')
  if set(value)!={'schema','serial','product','edition','device','issued_at','expires_at','max_devices','version_prefix'}:raise LicenseError('token')
  serial(value['serial'])
  if value['schema']!=1 or value['product']!=PRODUCT or value['edition']!=EDITION or type(value['max_devices'])!=int or value['max_devices']!=1:raise LicenseError('token')
  if not FINGERPRINT.fullmatch(value['device']):raise LicenseError('token')
  if value['device']!=device:raise LicenseError('device')
  issued,expires=timestamp(value['issued_at']),timestamp(value['expires_at']);now=now or datetime.now(timezone.utc)
  if issued>=expires:raise LicenseError('token')
  if now<issued:raise LicenseError('clock')
  if now>=expires:raise LicenseError('expired')
  if value['version_prefix']!='0.1.' or not version.startswith(value['version_prefix']):raise LicenseError('version')
  return value
 except InvalidSignature as e:raise LicenseError('signature') from e
 except (ValueError,TypeError,KeyError,AttributeError) as e:
  if isinstance(e,LicenseError):raise
  raise LicenseError('token') from e
def activate(token,public_key,device,destination,now=None):
 value=verify(token,public_key,device,now)
 p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True)
 import uuid
 tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
 try:tmp.write_text(token.strip(),encoding='ascii');tmp.replace(p)
 finally:tmp.unlink(missing_ok=True)
 return value
def load_license(path,public_key,device,now=None):
 try:
  p=Path(path)
  if p.stat().st_size>32768:raise LicenseError('token')
  return verify(p.read_text(encoding='ascii'),public_key,device,now)
 except FileNotFoundError as e:raise LicenseError('missing') from e
 except (OSError,UnicodeError) as e:raise LicenseError('token') from e
