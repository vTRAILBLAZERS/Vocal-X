import unittest,tempfile,json,os,sys,subprocess,hashlib,shutil
from pathlib import Path
from unittest.mock import patch
import numpy as np,soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vocal_pipeline.paths import data_root,prepare,preset_files,python_executable
from vocal_pipeline.models import assets
from vocal_pipeline.runner import run
class PortabilityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.install=self.base/'Programme mit Leerzeichen/Vocal X';self.user=self.base/'Benutzer Daten';self.install.mkdir(parents=True);(self.install/'App').mkdir();(self.install/'App/runtime-layout.json').write_text('{"mode":"installed"}');(self.install/'Config').mkdir();(self.install/'Config/core-model-download-report.json').write_text('{"models":[]}')
  self.env=patch.dict(os.environ,{'VOCAL_X_DATA_ROOT':str(self.user)});self.env.start()
  from test_license_fixture import provision
  provision(self.install)
  self.source=self.base/'Original.wav';sf.write(self.source,np.zeros((1000,2)),44100,subtype='FLOAT')
  self.p={'version':1,'name':'Portable export','stages':[dict(id='export',type='export',input='previous',output='final',enabled=True,optional=False,model=None,engine='DSP',parameters={})]}
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def snapshot(self):return {str(p.relative_to(self.install)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.install.rglob('*') if p.is_file()}
 def test_run_resume_no_program_writes(self):
  before=self.snapshot();original=self.source.read_bytes();job,state=run(self.install,self.p,self.source)
  self.assertTrue(job.is_relative_to(self.user));self.assertTrue(Path(state['output']).is_relative_to(self.user));self.assertEqual(before,self.snapshot());_,resumed=run(self.install,self.p,self.source,job.name);self.assertEqual(resumed['status'],'completed');self.assertEqual(original,self.source.read_bytes());self.assertEqual(len(list(Path(state['output']).parent.iterdir())),1)
 def test_default_localappdata_and_boundary(self):
  with patch.dict(os.environ,{'LOCALAPPDATA':str(self.base/'Local')}):
   override=os.environ.pop('VOCAL_X_DATA_ROOT')
   try:self.assertEqual(data_root(self.install),self.base/'Local/Vocal X')
   finally:os.environ['VOCAL_X_DATA_ROOT']=override
  with patch.dict(os.environ,{'VOCAL_X_DATA_ROOT':str(self.install/'Data')}):
   with self.assertRaises(ValueError):data_root(self.install)
 def test_relative_and_legacy_model_paths(self):
  target=self.install/'Models/test';target.mkdir(parents=True);(target/'weights').write_bytes(b'weight');(target/'config').write_bytes(b'config')
  for prefix in ['Models/test/','Z:/old/developer/Models/test/']:
   report={'models':[dict(slug='test',engine='BS',checkpoint={'path':prefix+'weights'},config={'path':prefix+'config'})]};(self.install/'Config/core-model-download-report.json').write_text(json.dumps(report));self.assertEqual(assets(self.install,'BS','test'),[target/'weights',target/'config'])
  report['models'][0]['checkpoint']['path']='../outside';(self.install/'Config/core-model-download-report.json').write_text(json.dumps(report))
  with self.assertRaises(ValueError):assets(self.install,'BS','test')
 def test_presets_and_runtime_fail_closed(self):
  prepare(self.install);folder=self.install/'Pipelines/Presets';folder.mkdir(parents=True);(folder/'built-in.json').write_text(json.dumps(self.p));custom=self.user/'Pipelines/Custom/custom.json';custom.write_text(json.dumps(self.p));self.assertEqual(set(preset_files(self.install)),{folder/'built-in.json',custom})
  with self.assertRaises(FileNotFoundError):python_executable(self.install)
 def test_worker_explicit_data_path(self):
  prepare(self.install);request=self.base/'request.json';request.write_text(json.dumps({'pipeline':self.p,'source':str(self.source)}));before=self.snapshot()
  result=subprocess.run([sys.executable,str(Path(__file__).parent/'gui_worker.py'),'--root',str(self.install),'--data-root',str(self.user),'--request',str(request)],capture_output=True,text=True,timeout=30)
  self.assertEqual(result.returncode,0,result.stderr);self.assertIn('completed',result.stdout);self.assertEqual(before,self.snapshot());self.assertTrue(list((self.user/'Processing/Jobs').glob('*/state.json')))
 def test_installed_gui_writes_only_user_data(self):
  from PySide6.QtWidgets import QApplication
  from qol_window import Window
  app=QApplication.instance() or QApplication([])
  folder=self.install/'Pipelines/Presets';folder.mkdir(parents=True);(folder/'export.json').write_text(json.dumps(self.p));before=self.snapshot()
  window=Window(self.install,startup=False);window.timer.stop();window.session_timer.stop()
  try:
   window.add_paths([self.source]);window.save_session()
   self.assertEqual(window.settings_path,self.user/'Config/gui-settings.json');self.assertTrue(window.queue_path.is_file());self.assertEqual(before,self.snapshot())
  finally:window.close();app.processEvents()
 def test_cli_explicit_data_path(self):
  preset=self.base/'export.json';preset.write_text(json.dumps(self.p));before=self.snapshot()
  result=subprocess.run([sys.executable,str(Path(__file__).parent/'pipeline.py'),'--root',str(self.install),'--data-root',str(self.user),'run','--preset',str(preset),'--input',str(self.source)],capture_output=True,text=True,timeout=30)
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(before,self.snapshot())
if __name__=='__main__':unittest.main(verbosity=2)
