import os,sys,json,copy,time,unittest
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='windows'
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'App'))
import soundfile as sf,numpy as np
from vocal_pipeline.runner import run
from vocal_pipeline.schema import validate
from vocal_pipeline.restoration_full import assets,MODEL
from PySide6.QtWidgets import QApplication
APP=QApplication.instance() or QApplication([])
class FullTests(unittest.TestCase):
 def test_gui_presets(self):
  from PySide6.QtWidgets import QApplication
  from vocal_gui import StageEditor
  app=QApplication.instance() or QApplication([])
  for path in (ROOT/'Pipelines/Presets').glob('*.json'):
   p=json.loads(path.read_text(encoding='utf-8'));validate(p,ROOT)
   for s in p['stages']:
    if s['type']=='restoration':
     editor=StageEditor(s,{})
     validate(dict(p,stages=[editor.value() if t is s else t for t in p['stages']]),ROOT)
     if s['model']==MODEL:
      editor.prompt.setText('C:/Reference.wav');self.assertEqual(editor.value()['parameters']['prompt_path'],'C:/Reference.wav')
     import shiboken6
     editor.close();shiboken6.delete(editor)
 def test_model_assets(self):
  self.assertGreater(len(assets(ROOT)),8)
 def test_invalid_reference(self):
  p=json.loads((ROOT/'Pipelines/Presets/KI-Restaurierung - Bereits isolierte Vocal.json').read_text(encoding='utf-8'))
  p['stages'][0]['parameters']['prompt_path']='C:/reference.wav'
  with self.assertRaises(ValueError):validate(p,ROOT)
def gpu():
 import torch
 folder=ROOT/'Temp/AnyEnhance360M-Test';source=folder/'Vocal-Test-360M-active.wav'
 if not source.is_file():raise FileNotFoundError('Test audio missing: '+str(source))
 p=json.loads((ROOT/'Pipelines/Presets/AnyEnhance 360M - Isolierte Vocal.json').read_text(encoding='utf-8'))
 x,sr=sf.read(source,always_2d=True,dtype='float32')
 report={'gpu':torch.cuda.get_device_name(),'tests':[]}
 for use_prompt in (False,True):
  current=copy.deepcopy(p)
  if use_prompt:current['stages'][0]['parameters']['prompt_path']=str(source)
  start=time.time();torch.cuda.reset_peak_memory_stats()
  job,state=run(ROOT,current,source)
  out=Path(state['internal_output']);y,ysr=sf.read(out,always_2d=True,dtype='float32')
  assert y.shape==x.shape and ysr==sr and np.isfinite(y).all() and sf.info(out).subtype=='FLOAT'
  stamp=out.stat().st_mtime_ns
  _,resumed=run(ROOT,current,source,job.name)
  assert resumed['status']=='completed' and out.stat().st_mtime_ns==stamp
  report['tests'].append({'prompt':use_prompt,'job':str(job),'status':state['status'],'seconds':round(time.time()-start,2),'frames':len(y),'channels':y.shape[1],'sample_rate':ysr,'input_rms':float(np.sqrt(np.mean(x*x))),'output_rms':float(np.sqrt(np.mean(y*y))),'peak':float(np.abs(y).max()),'peak_vram_gb':round(torch.cuda.max_memory_allocated()/2**30,2),'resume':'PASS','format':'WAV FLOAT'})
  print(json.dumps(report['tests'][-1]),flush=True)
 (folder/'verified-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('GPU AUDIO + PROMPT + RESUME: PASS',flush=True)
if __name__=='__main__':
 if '--gpu' in sys.argv:gpu()
 else:unittest.main(verbosity=2)


