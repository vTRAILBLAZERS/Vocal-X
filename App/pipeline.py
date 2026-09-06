import os
from vocal_pipeline.paths import preset_files,prepare
import argparse,json,sys,traceback
from pathlib import Path
from vocal_pipeline.runner import run
from vocal_pipeline.schema import validate
from vocal_pipeline.models import catalog,assets

def main():
    p=argparse.ArgumentParser(description='VOCAL AI Pipeline Engine v1')
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--data-root',type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('check')
    r=sub.add_parser('run'); r.add_argument('--preset',required=True); r.add_argument('--input',required=True); r.add_argument('--resume')
    args=p.parse_args()
    if args.data_root:os.environ['VOCAL_X_DATA_ROOT']=str(args.data_root)
    prepare(args.root)
    if args.command=='check':
        import torch
        for slug,m in catalog(args.root).items():
            assets(args.root,m['engine'],slug); print('MODEL OK',slug)
        for f in preset_files(args.root):
            validate(json.loads(f.read_text(encoding='utf-8-sig')),args.root); print('PRESET OK',f.name)
        print('Python:',sys.executable,'CUDA:',torch.cuda.is_available(),'GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')
    else:
        f=Path(args.preset)
        if not f.is_file(): f=args.root/'Pipelines/Presets'/(args.preset+'.json')
        job,state=run(args.root,json.loads(f.read_text(encoding='utf-8-sig')),args.input,args.resume)
        print(json.dumps({'job':str(job),'status':state['status'],'output':state['output']},indent=2))
if __name__=='__main__':
    try: main()
    except __import__('vocal_license').LicenseError as e:
        from vocal_license import message
        print(message(e,'en'),file=sys.stderr);sys.exit(2)
    except Exception: traceback.print_exc(); sys.exit(1)
