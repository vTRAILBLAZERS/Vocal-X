from license_service import require_license
from diagnostics import record
from .paths import data_root
import hashlib
import json
import logging
import uuid
import time
from pathlib import Path
import msvcrt
from . import __version__
from .schema import validate
from .stages import execute
from .models import assets

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def save(path, data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2),encoding='utf-8')
    temp.replace(path)

def run(root, pipeline, source, resume=None, on_job=None, control=None, preview=False):
    root, source = Path(root).resolve(), Path(source).resolve()
    require_license(root)
    validate(pipeline,root)
    from .policy import wav_info
    wav_info(source)
    if any(s['enabled'] and s['engine']!='DSP' for s in pipeline['stages']):
        import torch
        if not torch.cuda.is_available():raise RuntimeError('Vocal X requires an NVIDIA CUDA GPU for AI processing')
    for stage in pipeline['stages']:
        if stage['enabled'] and stage['parameters'].get('prompt_path'): wav_info(stage['parameters']['prompt_path'])
    identity={'engine_version':__version__, 'pipeline':pipeline, 'source':str(source), 'source_sha256':digest(source), 'models':{}}
    if preview: identity['preview']=True
    for s in pipeline['stages']:
        if s['enabled'] and s['engine'] in ('BS','MEL'):
            try:
                identity['models'][s['model']]=[digest(p) for p in assets(root,s['engine'],s['model'])]
            except Exception:
                if not s['optional']: raise
                identity['models'][s['model']]=None
    for s in pipeline['stages']:
        if s['enabled'] and s['engine']=='ANYENHANCE':
            if s['model']=='anyenhance-360m-selfcritic-v2':
                from .restoration_full import assets as restoration_assets
            else:
                from .restoration import assets as restoration_assets
            try:
                identity['models'][s['model']]=[digest(p) for p in restoration_assets(root)]
                if s['parameters'].get('prompt_path'):
                    identity['models'][s['id']+'_prompt']=digest(s['parameters']['prompt_path'])
            except Exception:
                if not s['optional']: raise
                identity['models'][s['model']]=None
    jobs=data_root(root)/'Processing/Jobs'
    job=(jobs/resume).resolve() if resume else jobs/uuid.uuid4().hex
    if job.parent!=jobs.resolve(): raise ValueError('Invalid job id')
    if resume and not job.is_dir(): raise FileNotFoundError(job)
    job.mkdir(parents=True,exist_ok=True)
    lock=open(job/'job.lock','a+b')
    lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
    try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        lock.close(); raise RuntimeError('Job is already running')
    logger=logging.getLogger('pipeline.'+job.name)
    handler=logging.FileHandler(job/'job.log',encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler); logger.setLevel(logging.INFO)
    state_path=job/'state.json'
    started=False
    try:
        state=json.loads(state_path.read_text()) if resume else {'identity':identity,'stages':{}}
        if state['identity']!=identity: raise ValueError('Resume refused: input, pipeline, engine version or model assets changed')
        started=True
        state['status']='running'; state['started_at']=time.time(); save(state_path,state)
        if on_job is not None:
            on_job(job)
        values={'source':source}; previous=source
        dirty=False
        for s in pipeline['stages']:
            require_license(root)
            src=previous if s['input']=='previous' else values[s['input']]
            old=state['stages'].get(s['id'],{})
            if not s['enabled']:
                values[s['output']]=previous=src
                state['stages'][s['id']]={'status':'disabled'}; save(state_path,state); continue
            valid=old.get('status')=='completed' and all(Path(p).is_file() and digest(p)==h for p,h in old.get('files',{}).items()) and bool(old.get('files'))
            if valid and not dirty:
                previous=Path(old['output']); values[s['output']]=previous
                logger.info('RESUME %s',s['id']); continue
            dirty=True
            folder=job/'Temp'/s['id']
            target=(job/'Export' if s['type']=='export' else folder)/(s['output']+'.wav')
            state['stages'][s['id']]={'status':'running','started_at':time.time()}; save(state_path,state)
            try:
                logger.info('START %s input=%s',s['id'],src)
                record(root,'stage_start',job=job.name,preset=pipeline['name'],stage=s['id'],model=s['model'])
                stage_started=time.monotonic()
                files=execute(root,s,src,target,folder)
                state['stages'][s['id']]={'status':'completed','output':str(target),'files':{str(p):digest(p) for p in files}}
                previous=target
                state['stages'][s['id']]['finished_at']=time.time()
                logger.info('DONE %s',s['id'])
                record(root,'stage_completed',job=job.name,stage=s['id'],model=s['model'],duration=time.monotonic()-stage_started)
            except Exception as e:
                record(root,'stage_failed',job=job.name,stage=s['id'],model=s['model'],error=str(e))
                logger.exception('FAILED %s',s['id'])
                state['stages'][s['id']]={'status':'optional_failed' if s['optional'] else 'failed','error':str(e)}
                save(state_path,state)
                if not s['optional']: raise
                previous=src
            values[s['output']]=previous; save(state_path,state)
            if control and Path(control).exists() and s is not pipeline['stages'][-1]:
                state['status']='interrupted';state['paused']=True;save(state_path,state);return job,state
        state['status']='completed_with_warnings' if any(s['status']=='optional_failed' for s in state['stages'].values()) else 'completed'
        require_license(root)
        state['internal_output']=str(previous)
        from .output_layout import publish
        if preview:
            state['output']=str(previous);state['output_folder']=str(job/'Export')
        else: publish(root, job, state)
        save(state_path,state)
        return job,state
    except BaseException:
        if started and state_path.exists():
            failed=json.loads(state_path.read_text()); failed['status']='failed'; save(state_path,failed)
        raise
    finally:
        handler.close(); logger.removeHandler(handler)
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1); lock.close()
