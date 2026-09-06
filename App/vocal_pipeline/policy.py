"""Shared input, settings and hardware policy for every entry point."""
import json,os
from pathlib import Path
import soundfile as sf
from .paths import data_root
DEFAULTS={'language':'de','output_dir':'','filename':'{OriginalName}_VocalX.wav','setup_complete':False,'advanced':False,'sound':False,'notify':True,'open_after':False,'after':'nothing','theme':'dark','performance':'Balanced','favorites':[],'recent':[]}
def settings(root):
 try: value=json.loads((data_root(root)/'Config/gui-settings.json').read_text(encoding='utf-8-sig'))
 except (OSError,ValueError):value={}
 if not isinstance(value,dict):return dict(DEFAULTS)
 clean={k:v for k,v in value.items() if k not in DEFAULTS or type(v)==type(DEFAULTS[k])}
 result=dict(DEFAULTS,**clean)
 if result['language'] not in ('de','en'):result['language']='de'
 return result
def wav_info(path):
 p=Path(path)
 if p.suffix.lower()!='.wav':raise ValueError('WAV_ONLY')
 if not p.is_file() or p.stat().st_size==0:raise ValueError('WAV_UNREADABLE')
 try: info=sf.info(p)
 except Exception as e:raise ValueError('WAV_UNREADABLE') from e
 if info.format not in ('WAV','WAVEX','RF64') or info.frames<=0 or info.channels not in (1,2):raise ValueError('WAV_UNSUPPORTED')
 if info.subtype not in ('PCM_U8','PCM_16','PCM_24','PCM_32','FLOAT','DOUBLE'):raise ValueError('WAV_UNSUPPORTED')
 return {'rate':info.samplerate,'channels':info.channels,'frames':info.frames,'duration':info.duration,'subtype':info.subtype,'size':p.stat().st_size,'warning':info.samplerate<16000 or info.duration<.25}
def hardware():
 try:
  import torch
  ok=torch.cuda.is_available()
  return {'cuda':ok,'gpu':torch.cuda.get_device_name(0) if ok else 'No CUDA GPU','vram':round(torch.cuda.get_device_properties(0).total_memory/2**30,2) if ok else 0,'runtime':torch.version.cuda}
 except Exception as e:return {'cuda':False,'gpu':str(e),'vram':0,'runtime':None}
def output_root(root):
 s=settings(root);return Path(s['output_dir']).expanduser().resolve() if s['output_dir'] else (data_root(root)/'Output').resolve()
