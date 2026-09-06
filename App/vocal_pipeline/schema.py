import re
from .models import catalog

def validate(pipeline, root):
    if not isinstance(pipeline,dict) or not isinstance(pipeline.get('name'),str) or not isinstance(pipeline.get('stages'),list):raise ValueError('Invalid preset structure')
    if 'info' in pipeline:
        info=pipeline['info']
        if not isinstance(info,dict):raise ValueError('Invalid preset descriptions')
        for lang in ('de','en'):
            if not isinstance(info.get(lang),dict) or any(not isinstance(info[lang].get(k),str) for k in ('short','description','use_case','intensity')):raise ValueError('Incomplete bilingual preset descriptions')
    if pipeline.get('version') != 1 or not pipeline.get('name') or not pipeline.get('stages'):
        raise ValueError('Expected version 1, name and stages')
    available = {'source'}
    ids = set()
    models = catalog(root)
    allowed = {'vocal_separation': {'device','stem','wet'}, 'dereverb': {'device','stem','wet'}, 'deecho': {'device','stem','wet'}, 'deesser': {'frequency_hz','threshold_db','max_reduction_db'}, 'cleanup': {'highpass_hz'}, 'export': {'flac'}, 'restoration': {'wet','device','timesteps','seed','prompt_path'}}
    for s in pipeline['stages']:
        for key in ('id','type','input','output','enabled','optional','parameters','model','engine'):
            if key not in s: raise ValueError('Missing stage field: '+key)
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', s['id']) or s['id'] in ids: raise ValueError('Invalid/duplicate stage id')
        ids.add(s['id'])
        if s['type'] not in allowed: raise ValueError('Unknown stage type')
        if s['input'] not in available | {'previous'}: raise ValueError('Forward/unknown input')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', s['output']) or s['output'] in available | {'previous'}: raise ValueError('Invalid/duplicate output')
        available.add(s['output'])
        if type(s['enabled']) is not bool or type(s['optional']) is not bool: raise ValueError('Flags must be boolean')
        p = s['parameters']
        if not isinstance(p, dict) or set(p)-allowed[s['type']]: raise ValueError('Unknown parameters')
        for k,v in p.items():
            if k in ('device','stem','prompt_path'):
                if not isinstance(v,str): raise ValueError(k)
            elif k=='flac':
                if type(v) is not bool: raise ValueError(k)
            else:
                import math
                if type(v) not in (int,float) or not math.isfinite(v): raise ValueError(k)
                if k=='wet' and not 0<=v<=1: raise ValueError(k)
                if k in ('frequency_hz','highpass_hz','max_reduction_db') and v<=0: raise ValueError(k)
        if s['type']=='restoration':
            if s['engine']!='ANYENHANCE' or s['model'] not in ('anyenhance-v1-baseline','anyenhance-360m-selfcritic-v2'): raise ValueError('Invalid restoration model')
            if p.get('prompt_path') and s['model']!='anyenhance-360m-selfcritic-v2': raise ValueError('Reference requires 360M model')
            if p.get('device','cuda') not in ('cuda','cpu'): raise ValueError('Invalid restoration device')
            if type(p.get('timesteps',20)) is not int or not 4<=p.get('timesteps',20)<=40: raise ValueError('timesteps must be integer 4..40')
            if type(p.get('seed',42)) is not int or not 0<=p.get('seed',42)<=2147483647: raise ValueError('Invalid seed')
        elif s['type'] in ('vocal_separation','dereverb','deecho'):
            if s['model'] not in models or models[s['model']]['engine']!=s['engine']: raise ValueError('Unknown model/engine')
        elif s['model'] is not None or s['engine']!='DSP': raise ValueError('DSP stage requires model null and engine DSP')
    last = pipeline['stages'][-1]
    if last['type']!='export' or not last['enabled'] or last['optional']: raise ValueError('Final export must be enabled and required')
