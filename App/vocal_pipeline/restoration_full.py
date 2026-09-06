from .paths import anyenhance_packages
import gc,hashlib,inspect,json,sys
from pathlib import Path
MODEL='anyenhance-360m-selfcritic-v2'
def assets(root):
 root=Path(root); folder=root/'Models/AnyEnhance-360M'; source=root/'Tools/AnyEnhance-360M-Recovered'
 source_required=[source/'models/se/anyenhance/modules/encoder_loss.py',source/'models/se/anyenhance/anyenhance_model.py',source/'models/se/anyenhance/modules/anyenhance_modules.py']
 for p in source_required:
  if not p.is_file() or not p.stat().st_size: raise FileNotFoundError('AnyEnhance 360M source incomplete: '+str(p))
 paths=[folder/'w2v-bert-2.0/model.safetensors',folder/'w2v-bert-2.0/config.json',folder/'w2v-bert-2.0/preprocessor_config.json',folder/'model.pt',folder/'dac.pth',folder/'anyenhance-360M-selfcritic-v2.json',folder/'provenance.json',Path(__file__),root/'App/vocal_pipeline/restoration.py']+sorted((source/'models').rglob('*.py'))
 for p in paths:
  if not p.is_file() or not p.stat().st_size: raise FileNotFoundError(str(p))
 return paths

def load_model(root,device):
 root=Path(root); assets(root)
 sys.path.insert(0,str(anyenhance_packages(root)))
 sys.path.insert(0,str(root/'Tools/AnyEnhance-360M-Recovered'))
 import torch,dac,json5
 import models.se.anyenhance.modules.encoder_loss as encoder_loss
 encoder_loss.pretrained_path=str(root/'Models/AnyEnhance-360M')
 from models.se.anyenhance.anyenhance_model import AnyEnhance,AudioEncoder_v2
 from models.se.anyenhance.modules.anyenhance_modules import MaskGitTransformer
 folder=root/'Models/AnyEnhance-360M'; provenance=json.loads((folder/'provenance.json').read_text(encoding='utf-8-sig'))
 for name,expected in provenance['sha256'].items():
  with open(folder/name,'rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
  if actual.lower()!=expected.lower(): raise ValueError('Checksum mismatch: '+name)
 weights=torch.load(folder/'dac.pth',map_location='cpu',weights_only=False)
 kwargs={k:v for k,v in weights['metadata']['kwargs'].items() if k in inspect.signature(dac.DAC).parameters}
 codec=dac.DAC(**kwargs);codec.load_state_dict(weights['state_dict'],strict=True);codec.eval().requires_grad_(False)
 cfg=json5.loads((folder/'anyenhance-360M-selfcritic-v2.json').read_text())['model']
 model=AnyEnhance(vq_model=codec,transformer=MaskGitTransformer(**cfg['MaskGitTransformer']),audio_encoder=AudioEncoder_v2(**cfg['AudioEncoder']),**cfg['AnyEnhance'])
 params=torch.load(folder/'model.pt',map_location='cpu',weights_only=True)
 params={k.removeprefix('module.'):v for k,v in params.items()}
 mismatch=model.load_state_dict(params,strict=False)
 missing=[k for k in mismatch.missing_keys if not k.startswith('vq_model.')]
 if missing or mismatch.unexpected_keys: raise ValueError(f'Checkpoint mismatch: {missing}, {mismatch.unexpected_keys}')
 print(f'AnyEnhance 360M: {len(params)} tensors matched; codec loaded separately; SelfCritic_V2 active',flush=True)
 return model.to(device).eval()

def infer(root,stage,source,target,folder):
 from .audio import read,write,resample
 from .restoration import overlap_restore
 import numpy as np
 import torch
 p=stage['parameters']; device=p.get('device','cuda'); model=None
 if device=='cuda' and not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable')
 try:
  x,sr=read(source);wet=p.get('wet',1.)
  if wet==0: write(target,x,sr);return [target]
  model=load_model(root,device)
  mono=resample(x.mean(axis=1,keepdims=True),sr,44100)[:,0]
  prompt=None
  if p.get('prompt_path'):
   ref,refsr=read(p['prompt_path']);ref=resample(ref.mean(axis=1,keepdims=True),refsr,44100)[:,0]
   if len(ref)==0: raise ValueError('Empty reference audio')
   ref=np.tile(ref,int(np.ceil(model.prompt_len*512/len(ref))))[:model.prompt_len*512]
   prompt=torch.from_numpy(ref.copy()).to(device)[None,None,:]
  task=torch.tensor([0],dtype=torch.long,device=device)
  window=512*(model.seq_len if prompt is not None else model.seq_len+model.prompt_len)
  def generate(part,index):
   torch.manual_seed(p.get('seed',42)+index)
   kw=dict(timesteps=p.get('timesteps',20),cond_scale=1,task_type=task,force_not_use_token_critic=False)
   with torch.inference_mode():
    inp=torch.from_numpy(part.copy()).to(device)[None,None,:]
    _,audio=model.generate(inp,**kw) if prompt is None else model.generate_with_prompt(inp,prompt,**kw)
   return audio.detach().float().cpu().numpy().reshape(-1)
  restored=overlap_restore(mono,window,1024,generate)
  restored=resample(restored[:,None],44100,sr)[:len(x)]
  if len(restored)!=len(x): raise ValueError('Restoration changed duration')
  write(target,x*(1-wet)+restored*wet,sr)
  return [target]
 finally:
  if model is not None: del model
  gc.collect()
  if torch.cuda.is_available():torch.cuda.empty_cache()

