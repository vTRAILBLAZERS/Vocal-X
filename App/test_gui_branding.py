import sys,json,copy,tempfile
from pathlib import Path
scratch=Path(tempfile.mkdtemp(prefix='VocalX-Gui-'));
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root/'App'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from unittest.mock import patch
import vocal_gui
app=QApplication([]);app.setStyle('Fusion');app.setStyleSheet(vocal_gui.STYLE);QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf')
w=vocal_gui.Window();w.timer.stop();w.queue_path=scratch/'queue.json';w.settings_path=scratch/'settings.json'
w.items=[];w.active=None;w.language.setCurrentIndex(w.language.findData('de'));w.resize(1450,940);w.show();app.processEvents()
w.presets.setCurrentIndex(w.presets.findText('AnyEnhance 360M - Song zu Vocal'));app.processEvents()
# Language changes must preserve unsaved settings.
w.editors[0].fields['wet'].setValue(.65)
w.language.setCurrentIndex(w.language.findData('en'));app.processEvents()
assert w.editors[0].fields['wet'].value()==.65
assert w.start_button.text()=='Start queue'
assert json.loads(w.settings_path.read_text())['language']=='en'
assert w.pipeline()['name']=='AnyEnhance 360M - Song zu Vocal'
assert w.table.horizontalHeaderItem(1).text()=='Preset'
w.grab().save(str(scratch/'gui-english.png'))
w.language.setCurrentIndex(w.language.findData('de'));app.processEvents()
assert w.start_button.text()=='Warteschlange starten'
w.grab().save(str(scratch/'gui-german.png'))
p=w.pipeline();sample=root/'Temp/AnyEnhance360M-Test/Vocal-Test-360M-active.wav'
w.items=[dict(id='one',source=str(sample),pipeline=copy.deepcopy(p),status='pending'),dict(id='two',source=str(sample),pipeline=copy.deepcopy(p),status='running')];w.active=w.items[1];w.render_queue();w.table.selectRow(0);w.render_queue();assert w.selected()[0]['id']=='one'
w.table.setFocus();QTest.keyClick(w.table,Qt.Key.Key_Delete);app.processEvents();assert len(w.items)==1 and w.items[0]['id']=='two';assert sample.is_file()
w.table.selectRow(0);QTest.keyClick(w.table,Qt.Key.Key_Delete);assert len(w.items)==1
w.active=None;w.items=[dict(id='done',source=str(sample),pipeline=p,status='completed',job='64be277316e740649f02cf50b9fae7f3')];w.render_queue();w.table.clearSelection()
assert w.output_directory()==root/'Output/Vocal-Test-360M-active'
with patch('vocal_gui.os.startfile') as launch:
 w.open_output();assert launch.call_args.args==(str(w.output_directory()),'open')
w.items=[];w.render_queue();assert w.output_directory()==root/'Output'
w.close();app.processEvents()
print('PASS: language DE/EN, edits preserved, Delete, running-row protection, source preserved, selection retention, output resolution and launch call, empty queue fallback')
