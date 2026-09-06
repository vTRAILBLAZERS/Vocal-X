import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
from vocal_pipeline.runner import run
from vocal_pipeline.audio import write

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        (self.root/'Config').mkdir()
        (self.root/'Config/core-model-download-report.json').write_text('{"models":[]}')
        from test_license_fixture import provision
        provision(self.root)
        self.source=self.root/'source.wav'
        t=np.arange(44100)/44100
        write(self.source,np.column_stack([.2*np.sin(2*np.pi*200*t)+.05*np.sin(2*np.pi*7000*t)]*2),44100)
        self.pipeline={'version':1,'name':'test','stages':[dict(id=k,type=k,input='previous',output=k+'_out',enabled=True,optional=False,parameters=({'flac':True} if k=='export' else {}),model=None,engine='DSP') for k in ['deesser','cleanup','export']]}
    def tearDown(self): self.tmp.cleanup()
    def test_export_resume_and_corruption(self):
        job,state=run(self.root,self.pipeline,self.source)
        self.assertEqual(sf.info(state['output']).subtype,'FLOAT')
        self.assertEqual(sf.info(Path(state['output_folder'])/'Formats'/Path(state['output']).with_suffix('.flac').name).subtype,'PCM_24')
        with patch('vocal_pipeline.runner.execute',side_effect=AssertionError('rerun')):
            run(self.root,self.pipeline,self.source,job.name)
        Path(state['output']).write_bytes(b'broken')
        _,fixed=run(self.root,self.pipeline,self.source,job.name)
        self.assertEqual(sf.info(fixed['output']).frames,44100)
    def test_changed_input_refused(self):
        job,_=run(self.root,self.pipeline,self.source)
        write(self.source,np.zeros((100,2)),44100)
        with self.assertRaisesRegex(ValueError,'Resume refused'): run(self.root,self.pipeline,self.source,job.name)
        self.assertEqual(json.loads((job/'state.json').read_text())['status'],'completed')
    def test_optional_failure_and_disabled_chaining(self):
        self.pipeline['stages'][0]['parameters']={'frequency_hz':50000}
        self.pipeline['stages'][0]['optional']=True
        self.pipeline['stages'][1]['enabled']=False
        job,state=run(self.root,self.pipeline,self.source)
        self.assertEqual(state['status'],'completed_with_warnings')
        np.testing.assert_array_equal(sf.read(self.source)[0],sf.read(state['output'])[0])
    def test_required_failure_resumes(self):
        with patch('vocal_pipeline.runner.execute',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError): run(self.root,self.pipeline,self.source)
        job=next((self.root/'Processing/Jobs').iterdir())
        _,state=run(self.root,self.pipeline,self.source,job.name)
        self.assertEqual(state['status'],'completed')
    def test_forward_reference_rejected(self):
        self.pipeline['stages'][0]['input']='unknown'
        with self.assertRaises(ValueError): run(self.root,self.pipeline,self.source)

if __name__=='__main__': unittest.main(verbosity=2)
