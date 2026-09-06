import unittest,tempfile,json,copy,hashlib,sys
from pathlib import Path
from unittest.mock import patch
import numpy as np,soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vocal_pipeline.runner import run
from vocal_pipeline.policy import wav_info
from vocal_pipeline.output_layout import track_directory
class QOLCoreTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'Config').mkdir();(self.root/'Config/core-model-download-report.json').write_text('{"models":[]}');self.source=self.root/'song.wav';sf.write(self.source,np.random.default_rng(0).normal(0,.05,(44100,2)),44100,subtype='FLOAT');self.hash=self.digest(self.source)
  from test_license_fixture import provision
  provision(self.root)
  self.p={'version':1,'name':'Export test','stages':[dict(id='cleanup',type='cleanup',input='previous',output='clean',enabled=True,optional=False,model=None,engine='DSP',parameters={}),dict(id='export',type='export',input='previous',output='final',enabled=True,optional=False,model=None,engine='DSP',parameters={'flac':True})]}
 def tearDown(self):self.temp.cleanup()
 def digest(self,p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 def test_single_final_history_and_original(self):
  j,a=run(self.root,self.p,self.source);j,b=run(self.root,self.p,self.source)
  self.assertEqual(a['output'],b['output']);self.assertEqual(len(list(Path(b['output']).parent.iterdir())),1);self.assertTrue(list((Path(b['output_folder'])/'History').rglob('*.wav')));self.assertEqual(self.hash,self.digest(self.source));self.assertTrue((Path(b['output_folder'])/'Formats/song_VocalX.flac').exists())
 def test_model_stem_capitalization(self):
  from vocal_pipeline.models import select_stem
  entries=[{'output_id':'Vocals','output_path':'voice.wav'},{'output_id':'Instrumental','output_path':'music.wav'}]
  self.assertEqual(select_stem(entries,'vocals'),'voice.wav')
  self.assertEqual(select_stem(entries,'INSTRUMENTAL'),'music.wav')
  with self.assertRaises(RuntimeError):select_stem(entries,'dry')
  with self.assertRaises(RuntimeError):select_stem(entries+[entries[0]],'vocals')
 def test_custom_output_and_name(self):
  dest=self.root/'elsewhere';(self.root/'Config/gui-settings.json').write_text(json.dumps({'output_dir':str(dest),'filename':'{OriginalName}_Done.wav'}));_,s=run(self.root,self.p,self.source);self.assertEqual(Path(s['output']),dest/'song/Finale Vocal/song_Done.wav')
 def test_preview_never_publishes(self):
  _,s=run(self.root,self.p,self.source,preview=True);self.assertFalse((self.root/'Output').exists());self.assertTrue(Path(s['output']).is_file())
 def test_pause_and_resume(self):
  control=self.root/'pause';control.touch();j,s=run(self.root,self.p,self.source,control=control);self.assertEqual(s['status'],'interrupted');self.assertFalse((self.root/'Output').exists());control.unlink();_,s=run(self.root,self.p,self.source,j.name);self.assertEqual(s['status'],'completed')
 def test_wav_only_and_headers(self):
  fake=self.root/'fake.wav';fake.write_bytes(b'bad')
  for p in [fake,self.source.with_suffix('.mp3')]:
   with self.assertRaises(ValueError):wav_info(p)
  renamed=self.root/'encoded.wav';sf.write(renamed,np.zeros(200),44100,format='FLAC')
  with self.assertRaises(ValueError):wav_info(renamed)
 def test_existing_original_in_final_is_protected(self):
  folder=track_directory(self.root,self.source)/'Finale Vocal';folder.mkdir(parents=True);original=folder/'original.wav';original.write_bytes(self.source.read_bytes())
  with self.assertRaises(ValueError):run(self.root,self.p,self.source)
  self.assertEqual(self.hash,self.digest(original))
 def test_same_basename_different_source(self):
  run(self.root,self.p,self.source);other=self.root/'other/song.wav';other.parent.mkdir();other.write_bytes(self.source.read_bytes());self.assertNotEqual(track_directory(self.root,self.source),track_directory(self.root,other))
if __name__=='__main__':unittest.main(verbosity=2)
