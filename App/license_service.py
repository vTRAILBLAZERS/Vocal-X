"""License enforcement shared by GUI, worker and CLI, including development runs."""
import json
from pathlib import Path
import vocal_license as protocol
from vocal_pipeline.paths import data_root

def public_key(root):
 try:
  value=json.loads((Path(root)/'App/license-public-key.json').read_text(encoding='utf-8-sig'))
  if value['algorithm']!='Ed25519':raise ValueError('algorithm')
  key=protocol.decode(value['key'])
  if len(key)!=32:raise ValueError('length')
  return key
 except (OSError,ValueError,KeyError,TypeError) as e:raise protocol.LicenseError('public_key') from e

def license_path(root):return data_root(root)/'License/activation.vxlicense'
def require_license(root):return protocol.load_license(license_path(root),public_key(root),protocol.device_fingerprint())
def activation_request(serial_number):return protocol.request_code(serial_number,protocol.device_fingerprint())
def activate(root,token):return protocol.activate(token,public_key(root),protocol.device_fingerprint(),license_path(root))
def status(root):
 try:return require_license(root),None
 except protocol.LicenseError as error:return None,error
