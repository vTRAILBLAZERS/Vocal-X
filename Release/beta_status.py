"""Read-only release readiness report; never reads the private signing key."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'App'))
from vocal_license import APP_VERSION,device_fingerprint
from vocal_pipeline.policy import hardware
from vocal_pipeline.paths import data_root,layout
from vocal_pipeline.models import assets
root=Path(__file__).resolve().parents[1]
print('=== VOCAL X BETA RELEASE STATUS ===')
print('Target version:',APP_VERSION)
print('Build: Development; phases 0-3 implemented; release gates pending')
print('Install path:',root)
print('User data path:',data_root(root),'| mode:',layout(root))
for k,v in hardware().items():print(k+':',v)
try:
 report=json.loads((root/'Config/core-model-download-report.json').read_text(encoding='utf-8-sig'))
 models=report['models'];ok=sum(bool(assets(root,m['engine'],m['slug'])) for m in models)
 print('Models present:',str(ok)+'/'+str(len(models)),'(existence/size, not full hash verification)')
except Exception:print('Models: inventory could not be read')
try:device_fingerprint();print('Device fingerprint: readable; raw data and hash omitted')
except Exception:print('Device fingerprint: ERROR')
print('License system: Ed25519 + activation GUI + runner/worker/CLI enforcement')
print('Beta serial slots: 10; no tester tokens issued during tests')
print('Private key bundled: NO RELEASE BUNDLE EXISTS; private tree excluded by policy')
print('WAV validation / original protection / one final: see regression suite results')
print('Hardcoded developer paths: model paths relative; development venv still depends on local Python, packaged runtime pending')
print('Installer / release SHA256 / digital signature: NOT AVAILABLE')
print('Defender: release build NOT TESTED')
print('Malwarebytes: prior launcher detection unresolved; RELEASE BLOCKER')
print('Release blockers: portable runtime, model rights, packaging, installer, antivirus, clean Windows and second NVIDIA PC tests')
print('Diagnostics: Help menu, redacted report, central logs and non-modal failure dialog implemented')
print('Clean Windows PC: NOT PERFORMED; user reports no fresh PC available')
print('Next step: model-rights review and packaging preparation')
