from .paths import data_root
"""Atomic publication: one current WAV, with prior application outputs in History."""
import hashlib,json,re,shutil,uuid,msvcrt
from pathlib import Path
from .policy import output_root,settings
LABELS={'restoration':'KI-Restaurierung','vocal_separation':'Vocal Separation','dereverb':'De-Reverb','deecho':'De-Echo','deesser':'De-Esser','cleanup':'Cleanup','export':'Export'}
def safe_name(value,limit=80):
 value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',str(value)).strip().rstrip('. ')[:limit].rstrip('. ')
 if not value:value='Unbenannt'
 if value.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:value='_'+value
 return value

def digest(path):
 with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def track_directory(root,source):
 source=Path(source).resolve();base=output_root(root)/safe_name(source.stem)
 marker=base/'source.json'
 if marker.exists():
  known=json.loads(marker.read_text(encoding='utf-8'))['source']
  if Path(known).resolve()!=source:base=base.with_name(base.name+'_'+hashlib.sha256(str(source).casefold().encode()).hexdigest()[:8])
 return base

def publish(root,job,state):
 root,job=Path(root).resolve(),Path(job).resolve()
 if state['status'] not in ('completed','completed_with_warnings'):raise ValueError('Only finished jobs can publish')
 if job.parent!=(data_root(root)/'Processing/Jobs').resolve():raise ValueError('Invalid job location')
 source=Path(state['identity']['source']).resolve();pipeline=state['identity']['pipeline'];destination=track_directory(root,source)
 destination.mkdir(parents=True,exist_ok=True)
 lock=open(destination/'.publish.lock','a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
 msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
 staged=[];moved=[]
 try:
  if track_directory(root,source)!=destination:return publish(root,job,state)
  # Only known application outputs may be archived; arbitrary files remain protected.
  known=set()
  for manifest in destination.glob('Verarbeitung__*.json'):
   try:
    data=json.loads(manifest.read_text(encoding='utf-8'))
    for stage in data['stages']:
     known.update(str(Path(f).resolve()) for f in stage['files'])
   except (OSError,ValueError,KeyError):pass
  cfg=settings(root);name=cfg['filename']
  if '{OriginalName}' not in name or Path(name).name!=name or not name.lower().endswith('.wav'):raise ValueError('Filename must be {OriginalName}...wav without directories')
  name=safe_name(name.replace('{OriginalName}',source.stem),150)
  final=destination/'Finale Vocal'/name
  if final.resolve()==source:raise ValueError('Output would overwrite original WAV')
  transfers=[];records=[]
  for index,stage in enumerate(pipeline['stages'],1):
   result=state['stages'].get(stage['id'],{});record={'stage':stage['id'],'model':stage['model'],'status':result.get('status'),'files':[]};records.append(record)
   if not stage['enabled'] or result.get('status')!='completed':continue
   for src,expected in result['files'].items():
    src=Path(src).resolve()
    if not src.is_relative_to(job) or not src.is_file() or digest(src)!=expected:raise ValueError('Missing or changed stage artifact: '+str(src))
    is_final=index==len(pipeline['stages']) and stage['type']=='export'
    if is_final:dst=final if src.suffix.lower()=='.wav' else destination/'Formats'/Path(name).with_suffix(src.suffix)
    else:dst=destination/safe_name(f'{index:02d} - {LABELS[stage["type"]]} - {stage["model"] or "DSP"}',65)/(safe_name(pipeline['name'],24)+'__'+job.name+src.suffix)
    if dst.resolve()==source:raise ValueError('Output would overwrite original')
    transfers.append((src,dst,expected,is_final));record['files'].append(str(dst))
  finals=[t for t in transfers if t[1]==final]
  if len(finals)!=1:raise ValueError('Expected one final WAV')
  final.parent.mkdir(exist_ok=True)
  existing=list(final.parent.iterdir())
  for old in existing:
   if not old.is_file() or old.resolve()==source:raise ValueError('Protected original or directory in Final folder: '+str(old))
   if str(old.resolve()) not in known and old!=final:
    if not re.search(r'__[0-9a-f]{32}\.wav(?:\.asd)?$',old.name,re.I):raise ValueError('Unrecognized file in Final folder; preserve it outside Final: '+str(old))
   if old==final and str(old.resolve()) not in known:raise ValueError('Unrecognized existing final; original protection: '+str(old))
  # Check sharing locks before moving any existing final file.
  import ctypes
  kernel=ctypes.WinDLL('kernel32',use_last_error=True)
  kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p];kernel.CreateFileW.restype=ctypes.c_void_p
  kernel.CloseHandle.argtypes=[ctypes.c_void_p]
  for old in existing:
   handle=kernel.CreateFileW(str(old),0x10000,7,None,3,0,None)
   if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
   kernel.CloseHandle(handle)
  for src,dst,expected,is_final in transfers:
   dst.parent.mkdir(parents=True,exist_ok=True)
   temp=destination/('publish-'+uuid.uuid4().hex+'.tmp');shutil.copyfile(src,temp)
   if digest(temp)!=expected:raise IOError('Output verification failed')
   staged.append((temp,dst))
  history=destination/'History'/uuid.uuid4().hex
  if existing:
   history.mkdir(parents=True)
   # Archive a copy of the current target, then replace it atomically below.
   for old in existing:
    if old==final:shutil.copy2(old,history/old.name)
    else:old.replace(history/old.name);moved.append((history/old.name,old))
  for tmp,dst in staged:tmp.replace(dst)
  manifest=destination/('Verarbeitung__'+job.name+'.json');tmp=manifest.with_suffix('.tmp')
  tmp.write_text(json.dumps({'source':str(source),'pipeline':pipeline['name'],'job':str(job),'status':state['status'],'stages':records},ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(manifest)
  (destination/'source.json').write_text(json.dumps({'source':str(source)}),encoding='utf-8')
  state.update(output=str(final),output_folder=str(destination),published_stages=records)
  return state
 except BaseException:
  for archived,old in reversed(moved):
   if archived.exists() and not old.exists():archived.replace(old)
  for temp,dst in staged:
   if temp.exists():temp.unlink()
  raise
 finally:
  lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
