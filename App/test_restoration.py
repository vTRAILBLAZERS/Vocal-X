import unittest
import copy,json
from pathlib import Path
import numpy as np
from vocal_pipeline.restoration import overlap_restore, assets
from vocal_pipeline.schema import validate

class RestorationTests(unittest.TestCase):
    def test_chunk_lengths_and_seams(self):
        for length in (1,1023,1024,8192,8193,15000,17123):
            x=np.random.default_rng(7).normal(0,.1,length).astype('float32')
            y=overlap_restore(x,8192,1024,lambda a,i:a)
            np.testing.assert_allclose(y,x,atol=1e-7)
    def test_reject_broken_generation(self):
        with self.assertRaises(ValueError): overlap_restore(np.ones(20),8192,1024,lambda a,i:np.zeros(2))
        with self.assertRaises(ValueError): overlap_restore(np.ones(20),8192,1024,lambda a,i:np.full(8192,np.nan))
    def test_installed_presets_and_limits(self):
        root=Path(__file__).resolve().parent.parent
        p=json.loads((root/'Pipelines/Presets/KI-Restaurierung - Experimentell.json').read_text(encoding='utf-8'))
        validate(p,root);assets(root)
        for value in (3,41,20.5,True):
            bad=copy.deepcopy(p);bad['stages'][1]['parameters']['timesteps']=value
            with self.assertRaises(ValueError):validate(bad,root)

if __name__=='__main__':unittest.main(verbosity=2)
