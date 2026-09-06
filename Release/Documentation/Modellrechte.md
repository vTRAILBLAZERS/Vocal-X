# Modellrechte – Prüfung vom 06.09.2026

Keine automatische Freigabe für den aktuellen Modellumfang. Quellen sind Original-Modellkarten, außer ausdrücklich als Mirror/provenance bezeichnet. Details, exakte Downloadquellen, Hashes und Preset-Zuordnung stehen in model-rights-audit.json.

| Modell | Autor | Lizenzbefund | Weitergabe / kommerzielle Nutzung | Hinweise |
|---|---|---|---|---|
| roformer-model-bs-roformer-leap-xe-vocals-by-pcunwa | pcunwa | [Unclear](https://huggingface.co/pcunwa/BS-Roformer-Leap) | Unresolved for exact package / Unclear | No explicit license found on original model card. |
| roformer-model-bs-roformer-leap-vocals-by-pcunwa | pcunwa | [Unclear](https://huggingface.co/pcunwa/BS-Roformer-Leap) | Unresolved for exact package / Unclear | No explicit license found on original model card. |
| roformer-model-bs-roformer-vocals-resurrection-by-unwa | unwa | [Conflicting metadata](https://huggingface.co/Politrees/UVR_resources) | Unresolved for exact package / Unclear | Mirror says MIT; installed registry says CC-BY-NC-SA-4.0. A mirror cannot establish the original author grant. |
| roformer-model-bs-roformer-vocals-revive-v3e-by-unwa | unwa | [Conflicting metadata](https://huggingface.co/Politrees/UVR_resources) | Unresolved for exact package / Unclear | Mirror says MIT; installed registry says CC-BY-NC-SA-4.0. Author/weight-specific terms required. |
| melband-roformer-big-beta7 | pcunwa/unwa | [Unclear](https://huggingface.co/pcunwa/Mel-Band-Roformer-big) | Unresolved for exact package / Unclear | No model card/license shown; original weight permission required. |
| roformer-model-melband-roformer-deux-by-becruily | becruily | [CC-BY-NC-4.0](https://huggingface.co/becruily/mel-band-roformer-deux) | Conditional noncommercial only / No under stated NC license | Original model card explicitly noncommercial. Beta purpose must be assessed. |
| melband-roformer-kim-vocals | Kimberley Jensen | [MIT on original card](https://huggingface.co/KimberleyJSN/melbandroformer) | Unresolved for exact package / Conditional under MIT | Registry incorrectly/differently labels CC-BY-NC-SA. Resolve pinned weight attribution and separately sourced YAML before packaging. |
| roformer-model-mel-roformer-viperx-1143 | ViperX | [Unclear](https://github.com/nomadkaraoke/python-audio-separator/releases/tag/model-configs) | Unresolved for exact package / Unclear | Download mirror does not establish weight redistribution permission. |
| roformer-model-melband-roformer-de-reverb-super-big-by-sucial | Sucial | [CC-BY-NC-SA-4.0; mirror mapping pending](https://huggingface.co/Sucial/Dereverb-Echo_Mel_Band_Roformer) | Conditional noncommercial only / No under stated NC license | Original family is noncommercial/share-alike; exact renamed mirror weight must be matched. |
| roformer-model-melband-roformer-de-reverb-echo-v2-by-sucial | Sucial | [CC-BY-NC-SA-4.0](https://huggingface.co/Sucial/Dereverb-Echo_Mel_Band_Roformer) | Conditional noncommercial only / No under stated NC license | Original model card lists the V2 checkpoint. Noncommercial, attribution and share-alike terms apply. |
| anyenhance-v1-baseline | AnyEnhance / CCF-AATC baseline authors | [Weight license unclear](https://github.com/viewfinder-annn/AnyEnhance-v1) | Unresolved / noncommercial constraint / Not cleared | Code license alone does not grant checkpoint rights. |
| anyenhance-360m-selfcritic-v2 | Amphion | [CC-BY-NC-4.0 in local provenance; live confirmation pending](https://modelscope.cn/models/amphion/anyenhance) | Unresolved / noncommercial constraint / Not cleared | Source page confirms model; license was not visible in current text retrieval. Recovered code provenance also needs review. |

Alle zwölf Hauptgewichte bleiben im Release-Plan gesperrt, bis die jeweils genannten Bedingungen geklärt sind. Dies verändert keine lokale Installation oder Presets. Kim ist ein möglicher Kandidat für einen kleineren Modellumfang; keine automatische Preset-Umstellung.

CC-NC erlaubt keine kommerzielle Nutzung unter dieser Lizenz. Kostenlose Verteilung allein beantwortet die NC-Frage nicht. CC-BY-NC-SA verlangt zudem Attribution und bei Anpassungen die passende Weiterlizenzierung; ein proprietärer App-Lizenzvertrag darf Rechte am Drittmaterial nicht pauschal beschränken. [Lizenzbedingungen](https://creativecommons.org/licenses/by-nc-sa/4.0/)

- [Descript DAC](https://huggingface.co/descript/descript-audio-codec): MIT on original card. Permitted subject to MIT notice; exact weight attribution pending package notices
- [w2v-BERT 2.0](https://huggingface.co/facebook/w2v-bert-2.0): MIT on original card. Permitted subject to MIT notice; use pinned revision from provenance

Die lokale Amphion-Code-Lizenz ist MIT. Das ersetzt nicht die Weight-Lizenz. Zusätzlich sind PySide6/Qt, PyTorch/CUDA, Python, FFmpeg und die tatsächlich paketierten DLLs vor dem Installer einzeln in Third-Party-Notices aufzunehmen.
