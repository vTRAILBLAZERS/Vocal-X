"""Isolated inference process used by the desktop queue."""
import argparse
import os
import json
import traceback
from pathlib import Path
from vocal_pipeline.runner import run

def event(**data):
    print('VOCAL_GUI_EVENT ' + json.dumps(data), flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--request', required=True)
    p.add_argument('--data-root')
    a = p.parse_args()
    if a.data_root:os.environ['VOCAL_X_DATA_ROOT']=a.data_root
    try:
        item = json.loads(Path(a.request).read_text(encoding='utf-8'))
        job, state = run(a.root, item['pipeline'], item['source'], item.get('job'),
                         on_job=lambda job: event(job=job.name), control=item.get('control'), preview=item.get('preview',False))
        event(job=job.name, status=state['status'], output=state.get('output',''))
    except __import__('vocal_license').LicenseError as e:
        from vocal_license import message
        from vocal_pipeline.policy import settings
        event(error=message(e,settings(a.root)['language']),license_error=e.code)
        raise SystemExit(2)
    except BaseException as e:
        traceback.print_exc()
        event(error=str(e))
        raise SystemExit(1)
