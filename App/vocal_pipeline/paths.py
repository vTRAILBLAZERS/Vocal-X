"""Resolve immutable installation resources separately from writable user data.
Development checkouts retain their current workspace unless installed mode is set.
"""
import json,os,sys
from pathlib import Path

def layout(root):
 p=Path(root).resolve()/'App/runtime-layout.json'
 if not p.exists():return 'development'
 value=json.loads(p.read_text(encoding='utf-8-sig'))
 if value.get('mode') not in ('development','installed'):raise ValueError('Invalid runtime layout')
 return value['mode']
def data_root(root):
 root=Path(root).resolve();override=os.environ.get('VOCAL_X_DATA_ROOT')
 if override:
  if not Path(override).is_absolute():raise ValueError('User data path must be absolute')
  target=Path(override).resolve()
 elif layout(root)=='installed':
  local=os.environ.get('LOCALAPPDATA')
  if not local or not Path(local).is_absolute():raise ValueError('Windows LOCALAPPDATA is unavailable')
  target=Path(local)/'Vocal X'
 else:return root
 if layout(root)=='installed' and target.is_relative_to(root):raise ValueError('User data must be outside the installation')
 return target

def prepare(root):
 data=data_root(root)
 for part in ('Config','Logs','Cache','Temp','Session','License','Processing/Jobs','Preview','Pipelines/Custom'): (data/part).mkdir(parents=True,exist_ok=True)
 return data

def preset_files(root):
 root=Path(root).resolve();data=data_root(root)
 folders=[root/'Pipelines/Presets',data/'Pipelines/Custom']
 if data==root:return sorted((root/'Pipelines').rglob('*.json'))
 return sorted(f for folder in folders for f in folder.rglob('*.json'))

def python_executable(root):
 root=Path(root).resolve()
 packaged=root/'Runtime/python.exe'
 if packaged.is_file():return packaged
 if layout(root)=='installed':raise FileNotFoundError('Bundled Python runtime is missing')
 candidate=root/'.venv/Scripts/python.exe'
 if candidate.is_file():return candidate
 raise FileNotFoundError('Development Python runtime is missing')

def anyenhance_packages(root):
 root=Path(root).resolve();packaged=root/'Runtime/anyenhance'
 if packaged.is_dir():return packaged
 if layout(root)=='installed':raise FileNotFoundError('Bundled AnyEnhance dependencies are missing')
 return root/'.venv-anyenhance/Lib/site-packages'
