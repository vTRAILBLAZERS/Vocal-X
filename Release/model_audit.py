"""Inventory installed weights and preset usage; no downloads or redistribution."""
import hashlib,json,tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEWS={
 'leap':('pcunwa','https://huggingface.co/pcunwa/BS-Roformer-Leap','Unclear','No explicit license found on original model card.'),
 'resurrection':('unwa','https://huggingface.co/Politrees/UVR_resources','Conflicting metadata','Mirror says MIT; installed registry says CC-BY-NC-SA-4.0. A mirror cannot establish the original author grant.'),
 'revive':('unwa','https://huggingface.co/Politrees/UVR_resources','Conflicting metadata','Mirror says MIT; installed registry says CC-BY-NC-SA-4.0. Author/weight-specific terms required.'),
 'big-beta7':('pcunwa/unwa','https://huggingface.co/pcunwa/Mel-Band-Roformer-big','Unclear','No model card/license shown; original weight permission required.'),
 'deux':('becruily','https://huggingface.co/becruily/mel-band-roformer-deux','CC-BY-NC-4.0','Original model card explicitly noncommercial. Beta purpose must be assessed.'),
 'kim-vocals':('Kimberley Jensen','https://huggingface.co/KimberleyJSN/melbandroformer','MIT on original card','Registry incorrectly/differently labels CC-BY-NC-SA. Resolve pinned weight attribution and separately sourced YAML before packaging.'),
 'viperx':('ViperX','https://github.com/nomadkaraoke/python-audio-separator/releases/tag/model-configs','Unclear','Download mirror does not establish weight redistribution permission.'),
 'super-big':('Sucial','https://huggingface.co/Sucial/Dereverb-Echo_Mel_Band_Roformer','CC-BY-NC-SA-4.0; mirror mapping pending','Original family is noncommercial/share-alike; exact renamed mirror weight must be matched.'),
 'echo-v2':('Sucial','https://huggingface.co/Sucial/Dereverb-Echo_Mel_Band_Roformer','CC-BY-NC-SA-4.0','Original model card lists the V2 checkpoint. Noncommercial, attribution and share-alike terms apply.'),
}

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def inventory(root=ROOT):
 presets=[];usage={}
 for path in sorted((root/'Pipelines').rglob('*.json')):
  p=json.loads(path.read_text(encoding='utf-8-sig'));needed=sorted({s['model'] for s in p['stages'] if s['enabled'] and s['model']})
  presets.append({'name':p['name'],'file':path.relative_to(root).as_posix(),'models':needed})
  for model in needed:usage.setdefault(model,[]).append(p['name'])
 registries={}
 for package in ('bs_roformer','mel_band_roformer'):
  source=root/'.venv/Lib/site-packages'/package/'config/checkpoints.toml'
  registries.update(tomllib.loads(source.read_text(encoding='utf-8'))['models'])
 result=[]
 for m in json.loads((root/'Config/core-model-download-report.json').read_text(encoding='utf-8-sig'))['models']:
  slug=m['slug'];author,source,license_name,notes=next(v for k,v in REVIEWS.items() if k in slug);files=[];meta=registries[slug]
  for kind in ('checkpoint','config'):
   path=(root/m[kind]['path']).resolve()
   if not path.is_relative_to(root/'Models'):raise ValueError('Outside Models')
   artifact=next(a for a in meta['artifacts'] if a['kind']==kind)
   actual=sha(path)
   files.append({'path':path.relative_to(root).as_posix(),'size':path.stat().st_size,'sha256':actual,'registry_hash_matches':actual==artifact['sha256'],'download_source':artifact['url']})
  nc='NC' in license_name
  result.append(dict(model=slug,author=author,source=source,license=license_name,redistribution='Conditional noncommercial only' if nc else 'Unresolved for exact package',commercial_use='No under stated NC license' if nc else 'Conditional under MIT' if 'MIT on' in license_name else 'Unclear',attribution='Required' if nc or 'MIT on' in license_name else 'Unclear',modification='Conditional; share-alike applies to adapted material' if 'SA' in license_name else 'Conditional' if nc or 'MIT on' in license_name else 'Unclear',notes=notes,release_allowed=False,used_by=usage.get(slug,[]),files=files))
 for slug,folder,author,source,lic,notes in [
  ('anyenhance-v1-baseline','AnyEnhance-v1','AnyEnhance / CCF-AATC baseline authors','https://github.com/viewfinder-annn/AnyEnhance-v1','Weight license unclear','Code license alone does not grant checkpoint rights.'),
  ('anyenhance-360m-selfcritic-v2','AnyEnhance-360M','Amphion','https://modelscope.cn/models/amphion/anyenhance','CC-BY-NC-4.0 in local provenance; live confirmation pending','Source page confirms model; license was not visible in current text retrieval. Recovered code provenance also needs review.')]:
  path=root/'Models'/folder/'model.pt';result.append(dict(model=slug,author=author,source=source,license=lic,redistribution='Unresolved / noncommercial constraint',commercial_use='Not cleared',attribution='Required if CC license confirmed',modification='Not cleared',notes=notes,release_allowed=False,used_by=usage.get(slug,[]),files=[{'path':path.relative_to(root).as_posix(),'size':path.stat().st_size,'sha256':sha(path)}]))
 return {'reviewed_on':'2026-09-06','scope':'Current preset set; conservative release decisions, not a blanket prohibition of private local use','models':result,'presets':presets,'dependencies':[{'model':'Descript DAC','source':'https://huggingface.co/descript/descript-audio-codec','license':'MIT on original card','redistribution':'Permitted subject to MIT notice; exact weight attribution pending package notices'},{'model':'w2v-BERT 2.0','source':'https://huggingface.co/facebook/w2v-bert-2.0','license':'MIT on original card','redistribution':'Permitted subject to MIT notice; use pinned revision from provenance'}]}

def main():
 data=inventory();out=ROOT/'Release/model-rights-audit.json';out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 rows=['# Modellrechte – Prüfung vom 06.09.2026','','Keine automatische Freigabe für den aktuellen Modellumfang. Quellen sind Original-Modellkarten, außer ausdrücklich als Mirror/provenance bezeichnet. Details, exakte Downloadquellen, Hashes und Preset-Zuordnung stehen in model-rights-audit.json.','','| Modell | Autor | Lizenzbefund | Weitergabe / kommerzielle Nutzung | Hinweise |','|---|---|---|---|---|']
 for m in data['models']:rows.append('| '+m['model']+' | '+m['author']+' | ['+m['license']+']('+m['source']+') | '+m['redistribution']+' / '+m['commercial_use']+' | '+m['notes']+' |')
 rows+=['','Alle zwölf Hauptgewichte bleiben im Release-Plan gesperrt, bis die jeweils genannten Bedingungen geklärt sind. Dies verändert keine lokale Installation oder Presets. Kim ist ein möglicher Kandidat für einen kleineren Modellumfang; keine automatische Preset-Umstellung.','', 'CC-NC erlaubt keine kommerzielle Nutzung unter dieser Lizenz. Kostenlose Verteilung allein beantwortet die NC-Frage nicht. CC-BY-NC-SA verlangt zudem Attribution und bei Anpassungen die passende Weiterlizenzierung; ein proprietärer App-Lizenzvertrag darf Rechte am Drittmaterial nicht pauschal beschränken. [Lizenzbedingungen](https://creativecommons.org/licenses/by-nc-sa/4.0/)','']
 for dep in data['dependencies']:rows.append('- ['+dep['model']+']('+dep['source']+'): '+dep['license']+'. '+dep['redistribution'])
 rows+=['','Die lokale Amphion-Code-Lizenz ist MIT. Das ersetzt nicht die Weight-Lizenz. Zusätzlich sind PySide6/Qt, PyTorch/CUDA, Python, FFmpeg und die tatsächlich paketierten DLLs vor dem Installer einzeln in Third-Party-Notices aufzunehmen.']
 (ROOT/'Release/Documentation/Modellrechte.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
 print('Audited main weights:',len(data['models']));print('Preset definitions:',len(data['presets']));print('Registry artifact hashes matched:',sum(f.get('registry_hash_matches',False) for m in data['models'] for f in m['files']));print('Release authorization: BLOCKED');return 0
if __name__=='__main__':raise SystemExit(main())
