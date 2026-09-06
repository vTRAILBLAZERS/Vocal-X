import unittest,tempfile,json,sys,subprocess
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
import numpy as np,soundfile as sf
from PySide6.QtWidgets import QApplication
from test_license_fixture import provision
from vocal_license import LicenseError,parse_request
import license_service
from license_dialog import LicenseDialog
from vocal_pipeline.runner import run
from qol_window import Window
APP=QApplication.instance() or QApplication([])
class ActivationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'Config').mkdir();(self.root/'Config/core-model-download-report.json').write_text('{"models":[]}');self.token,self.key=provision(self.root);self.source=self.root/'source.wav';sf.write(self.source,np.zeros((1000,2)),44100,subtype='FLOAT')
  self.p=dict(version=1,name='License export test',stages=[dict(id='export',type='export',input='previous',output='final',enabled=True,optional=False,model=None,engine='DSP',parameters={})]);folder=self.root/'Pipelines/Presets';folder.mkdir(parents=True);(folder/'export.json').write_text(json.dumps(self.p))
 def tearDown(self):self.tmp.cleanup()
 def test_gui_activation_and_masked_persistence(self):
  license_service.license_path(self.root).unlink();dialog=LicenseDialog(self.root);dialog.serial.setText('VX-BETA-TEST-ONLY-0001');dialog.make_request();self.assertEqual(parse_request(dialog.request.toPlainText())['serial'],'VX-BETA-TEST-ONLY-0001');dialog.token.setPlainText(self.token);dialog.activate_token()
  self.assertFalse(dialog.token.toPlainText());self.assertFalse(dialog.serial.text());self.assertNotIn('TEST-ONLY',dialog.summary.text());self.assertIn('****',dialog.summary.text());dialog.close()
  reopened=LicenseDialog(self.root);self.assertIn('****',reopened.summary.text());self.assertTrue(license_service.require_license(self.root));reopened.close()
 def test_invalid_token_preserves_activation(self):
  dialog=LicenseDialog(self.root);dialog.token.setPlainText('invalid');dialog.activate_token();self.assertEqual(license_service.license_path(self.root).read_text(),self.token);self.assertTrue(dialog.note.text());dialog.close()
 def test_missing_license_blocks_gui_and_no_output_picker(self):
  license_service.license_path(self.root).unlink();window=Window(self.root,startup=False);window.timer.stop();window.session_timer.stop()
  try:
   with patch('qol_window.QMessageBox.information'),patch.object(window,'show_license') as activation,patch('qol_window.QFileDialog.getExistingDirectory') as output:
    window.hardware_ready(dict(cuda=True,gpu='Test',runtime='test',vram=16));activation.assert_called_once();output.assert_not_called()
   window.settings['setup_complete']=True;window.add_paths([self.source]);window.start_queue();window.render_preview(0,1)
   self.assertIsNone(window.process);self.assertFalse(window.start_button.isEnabled());self.assertFalse(list((self.root/'Processing/Jobs').glob('*/state.json')))
  finally:window.close();APP.processEvents()
 def test_cli_and_worker_reject_invalid_licenses(self):
  request=self.root/'request.json';request.write_text(json.dumps({'source':str(self.source),'pipeline':self.p}));preset=self.root/'Pipelines/Presets/export.json'
  variants=['missing','corrupt','expired','wrong-device','tampered']
  for variant in variants:
   provision(self.root)
   if variant=='missing':license_service.license_path(self.root).unlink()
   elif variant=='corrupt':license_service.license_path(self.root).write_text('broken')
   elif variant=='expired':provision(self.root,expires=datetime.now(timezone.utc)-timedelta(seconds=10))
   elif variant=='wrong-device':provision(self.root,device='b'*64)
   else:
    p=license_service.license_path(self.root);parts=p.read_text().split('.');from vocal_license import decode,encode,canonical
    payload=json.loads(decode(parts[1]));payload['expires_at']='2099-01-01T00:00:00Z';parts[1]=encode(canonical(payload));p.write_text('.'.join(parts))
   for entry,args in [('pipeline.py',['run','--preset',str(preset),'--input',str(self.source)]),('gui_worker.py',['--request',str(request)])]:
    result=subprocess.run([sys.executable,str(Path(__file__).parent/entry),'--root',str(self.root),*args],capture_output=True,text=True,timeout=20)
    self.assertEqual(result.returncode,2,(variant,result.stderr));self.assertNotIn('Traceback',result.stderr);self.assertNotIn('VX-BETA-',result.stdout+result.stderr)
   self.assertFalse((self.root/'Output').exists());self.assertFalse(list((self.root/'Processing/Jobs').glob('*/state.json')))
 def test_expiry_rechecked_before_publish(self):
  original=license_service.require_license
  calls=[]
  def check(root):
   calls.append(1)
   if len(calls)==3:raise LicenseError('expired')
   return original(root)
  with patch('vocal_pipeline.runner.require_license',side_effect=check):
   with self.assertRaisesRegex(LicenseError,'expired'):run(self.root,self.p,self.source)
  self.assertFalse((self.root/'Output').exists());self.assertEqual(json.loads(next((self.root/'Processing/Jobs').glob('*/state.json')).read_text())['status'],'failed')
if __name__=='__main__':unittest.main(verbosity=2)
