import unittest,tempfile,sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Tools/LicenseAdmin'))
from vocal_license import *
from license_admin import initialize,issue
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
class LicenseTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.private=self.root/'private';self.public=self.root/'public.json';initialize(self.private,self.public)
  self.serials=[f'VX-BETA-TEST-TEST-{i:04d}' for i in range(10)]
  (self.private/'serial-hashes.json').write_text(json.dumps([hashlib.sha256(s.encode()).hexdigest() for s in self.serials]))
  self.pub=decode(json.loads(self.public.read_text())['key']);self.device='a'*64;self.now=datetime(2026,9,6,tzinfo=timezone.utc);self.req=request_code(self.serials[0],self.device)
 def tearDown(self):self.tmp.cleanup()
 def token(self):return issue(self.req,private=self.private,now=self.now)
 def test_valid_and_persistence(self):
  token=self.token();p=self.root/'license.vxlicense';value=activate(token,self.pub,self.device,p,self.now)
  self.assertEqual(value,load_license(p,self.pub,self.device,self.now));self.assertEqual(value['max_devices'],1);self.assertEqual(mask(value['serial']),'VX-BETA-****-****-0000')
 def test_wrong_device(self):
  with self.assertRaisesRegex(LicenseError,'device'):verify(self.token(),self.pub,'b'*64,self.now)
 def test_expiry_boundary(self):
  token=self.token();verify(token,self.pub,self.device,timestamp(BETA_EXPIRES)-timedelta(seconds=1))
  with self.assertRaisesRegex(LicenseError,'expired'):verify(token,self.pub,self.device,timestamp(BETA_EXPIRES))
 def test_tampering_and_wrong_signer(self):
  token=self.token();prefix,body,sig=token.split('.');payload=json.loads(decode(body));payload['device']='b'*64
  with self.assertRaisesRegex(LicenseError,'signature'):verify(prefix+'.'+encode(canonical(payload))+'.'+sig,self.pub,'b'*64,self.now)
  with self.assertRaisesRegex(LicenseError,'signature'):verify(token,Ed25519PrivateKey.generate().public_key().public_bytes_raw(),self.device,self.now)
 def test_corrupt_inputs(self):
  for text in ['', 'wrong', 'VXLIC1.abc.def', 'VXLIC1.'+'a'*33000+'.abc']:
   with self.assertRaises(LicenseError):verify(text,self.pub,self.device,self.now)
  with self.assertRaises(LicenseError):request_code('invalid',self.device)
 def test_one_device_and_idempotency(self):
  first=self.token();self.assertEqual(first,self.token())
  with self.assertRaisesRegex(ValueError,'another device'):issue(request_code(self.serials[0],'b'*64),private=self.private,now=self.now)
 def test_unknown_serial_and_ten_slots(self):
  for s in self.serials:issue(request_code(s,self.device),private=self.private,now=self.now)
  with self.assertRaisesRegex(ValueError,'ten beta'):issue(request_code('VX-BETA-TEST-TEST-9999',self.device),private=self.private,now=self.now)
 def test_future_clock_and_version(self):
  token=self.token()
  with self.assertRaisesRegex(LicenseError,'clock'):verify(token,self.pub,self.device,self.now-timedelta(days=1))
  with self.assertRaisesRegex(LicenseError,'version'):verify(token,self.pub,self.device,self.now,version='0.2.0')
 def test_device_stability(self):
  x=dict(machine_guid='abc',system_manufacturer='Maker',system_product='Board')
  self.assertEqual(fingerprint_from(x),fingerprint_from(dict(x,usb='different',hostname='different')))
  self.assertNotEqual(fingerprint_from(x),fingerprint_from(dict(x,machine_guid='def')))
 def test_key_protection_and_no_overwrite(self):
  self.assertGreater((self.private/'signing-key.dpapi').stat().st_size,32)
  with self.assertRaises(ValueError):initialize(self.private,self.public)
 def test_failed_activation_preserves_existing(self):
  p=self.root/'license';token=self.token();activate(token,self.pub,self.device,p,self.now)
  with self.assertRaises(LicenseError):activate('broken',self.pub,self.device,p,self.now)
  self.assertEqual(p.read_text(),token)
if __name__=='__main__':unittest.main(verbosity=2)
