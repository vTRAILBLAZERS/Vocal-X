from .paths import anyenhance_packages
"""Experimental AnyEnhance-v1 baseline adapter; no downloads during inference."""
import gc
import hashlib
import inspect
import json
import sys
from pathlib import Path

MODEL = 'anyenhance-v1-baseline'

def assets(root):
    root=Path(root)
    paths=[root/'Models/AnyEnhance-v1/model.pt',root/'Models/AnyEnhance-v1/dac.pth',
           root/'Models/AnyEnhance-v1/provenance.json',
           root/'Tools/AnyEnhance-v1/config/anyenhance_v1.json',Path(__file__)]
    paths+=sorted((root/'Tools/AnyEnhance-v1/anyenhance').glob('*.py'))
    for p in paths:
        if not p.is_file() or not p.stat().st_size: raise FileNotFoundError('AnyEnhance installation incomplete: '+str(p))
    if not (anyenhance_packages(root)/'dac').is_dir():
        raise FileNotFoundError('AnyEnhance dependencies missing')
    return paths

def load_model(root,device):
    root=Path(root); assets(root)
    sys.path.insert(0,str(anyenhance_packages(root)))
    sys.path.insert(0,str(root/'Tools/AnyEnhance-v1'))
    import torch
    import dac
    import json5
    from anyenhance import AnyEnhance_v1,MaskGitTransformer,AudioEncoder
    folder=root/'Models/AnyEnhance-v1'
    provenance=json.loads((folder/'provenance.json').read_text())
    for name in ('model.pt','dac.pth'):
        with open(folder/name,'rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=provenance['sha256'][name]: raise ValueError('AnyEnhance checksum mismatch: '+name)
    # Official DAC weights include constructor metadata; checked above before load.
    weights=torch.load(folder/'dac.pth',map_location='cpu',weights_only=False)
    kwargs={k:v for k,v in weights['metadata']['kwargs'].items() if k in inspect.signature(dac.DAC).parameters}
    codec=dac.DAC(**kwargs)
    codec.load_state_dict(weights['state_dict'],strict=True)
    codec.eval().requires_grad_(False)
    config=json5.loads((root/'Tools/AnyEnhance-v1/config/anyenhance_v1.json').read_text())['model']
    model=AnyEnhance_v1(vq_model=codec,transformer=MaskGitTransformer(**config['MaskGitTransformer']),
        audio_encoder=AudioEncoder(**config['AudioEncoder']),**config['AnyEnhance_v1'])
    params=torch.load(folder/'model.pt',map_location='cpu',weights_only=True)
    params={k.removeprefix('module.'):v for k,v in params.items()}
    mismatch=model.load_state_dict(params,strict=False)
    missing=[k for k in mismatch.missing_keys if not k.startswith('vq_model.')]
    if missing or mismatch.unexpected_keys: raise ValueError(f'Checkpoint mismatch: {missing}, {mismatch.unexpected_keys}')
    return model.to(device).eval()

def overlap_restore(mono, window, overlap, generate):
    import numpy as np
    if len(mono)==0 or not 0<overlap<window: raise ValueError('Invalid audio/chunk configuration')
    step=window-overlap
    total=np.zeros(len(mono),dtype=np.float32); weight=np.zeros(len(mono),dtype=np.float32)
    starts=list(range(0,max(1,len(mono)-overlap),step))
    for index,start in enumerate(starts):
        part=mono[start:start+window]; valid=len(part)
        padded=np.pad(part,(0,window-valid),mode='reflect' if valid>1 else 'edge')
        result=np.asarray(generate(padded,index),dtype=np.float32).reshape(-1)
        if len(result)!=window or not np.isfinite(result).all(): raise ValueError('Invalid generated block')
        fade=np.ones(window,dtype=np.float32)
        if index>0: fade[:overlap]=np.linspace(0,1,overlap)
        if index<len(starts)-1: fade[-overlap:]=np.linspace(1,0,overlap)
        total[start:start+valid]+=result[:valid]*fade[:valid]
        weight[start:start+valid]+=fade[:valid]
        print(f'AnyEnhance block {index+1}/{len(starts)}',flush=True)
    if np.any(weight<=0): raise ValueError('Uncovered output samples')
    return total/weight

def infer(root,stage,source,target,folder):
    from .audio import read,write,resample
    import numpy as np
    import torch
    p=stage['parameters']; device=p.get('device','cuda')
    if device=='cuda' and not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable')
    model=None
    try:
        x,sr=read(source)
        wet=p.get('wet',1.0)
        if wet==0: write(target,x,sr); return [target]
        model=load_model(root,device)
        mono=resample(x.mean(axis=1,keepdims=True),sr,44100)[:,0]
        def generate(part,index):
            torch.manual_seed(p.get('seed',42)+index)
            with torch.inference_mode():
                _,audio=model.generate(torch.from_numpy(part.copy()).to(device)[None,None,:],
                    timesteps=p.get('timesteps',20),cond_scale=1)
            return audio.detach().float().cpu().numpy().reshape(-1)
        restored=overlap_restore(mono,512*model.seq_len,1024,generate)
        restored=resample(restored[:,None],44100,sr)[:len(x)]
        if len(restored)!=len(x): raise ValueError('Restoration changed duration')
        # Model reconstructs mono. Stereo inputs get identical restored channels.
        result=x*(1-wet)+restored*wet
        write(target,result,sr)
        return [target]
    finally:
        if model is not None: del model
        gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache()
