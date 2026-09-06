import sys,unittest,tempfile,shutil,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np,soundfile as sf
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QUrl,QMimeData,QPointF
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtMultimedia import QMediaPlayer
from qol_window import Window,valid_wavs
from qol_audio import AudioPrepare
APP=QApplication.instance() or QApplication([])
ROOT=Path(__file__).resolve().parent.parent
class QOLGuiTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'Config').mkdir();shutil.copy(ROOT/'Config/core-model-download-report.json',self.root/'Config');shutil.copytree(ROOT/'Pipelines',self.root/'Pipelines');shutil.copytree(ROOT/'App/assets',self.root/'App/assets')
  self.a=self.root/'a.wav';self.b=self.root/'b.wav';x=np.sin(np.arange(44100*2)*2*np.pi*300/44100)*.1;sf.write(self.a,x,44100,subtype='FLOAT');sf.write(self.b,x*.25,44100,subtype='FLOAT')
  from test_license_fixture import provision
  provision(self.root)
  self.w=Window(self.root,startup=False);self.w.timer.stop();self.w.session_timer.stop();self.w.show();APP.processEvents()
 def tearDown(self):
  self.w.close();APP.processEvents();self.w.deleteLater();APP.processEvents();self.tmp.cleanup()
 def test_first_run_and_no_cuda(self):
  with patch('qol_window.QMessageBox.information'),patch('qol_window.QFileDialog.getExistingDirectory') as choose:
   self.w.hardware_ready({'cuda':False,'gpu':'No GPU','runtime':None,'vram':0});choose.assert_not_called()
  self.assertFalse(self.w.settings['setup_complete']);self.assertFalse(self.w.start_button.isEnabled())
  with patch('qol_window.QMessageBox.information'),patch('qol_window.QFileDialog.getExistingDirectory',return_value=str(self.root/'Chosen')):
   self.w.hardware_ready({'cuda':True,'gpu':'Test GPU','runtime':'12.8','vram':16})
  self.assertTrue(self.w.settings['setup_complete']);self.assertTrue(self.w.start_button.isEnabled())
  with patch('qol_window.QFileDialog.getExistingDirectory') as choose:self.w.hardware_ready({'cuda':True,'gpu':'Test GPU','runtime':'12.8','vram':16});choose.assert_not_called()
 def test_queue_filter_delete_undo_and_selection(self):
  self.w.add_paths([self.a,self.b,'unsupported.mp3']);self.w.add_paths([self.a]);self.assertEqual(len(self.w.items),2)
  self.w.search.setText('a.wav');self.assertTrue(self.w.table.isRowHidden(1));self.w.search.clear();self.w.table.selectAll();self.w.table.setFocus();APP.processEvents();QTest.keyClick(self.w.table,Qt.Key.Key_Delete);self.assertEqual(len(self.w.items),0);self.assertTrue(self.a.exists());self.w.undo_remove();self.assertEqual(len(self.w.items),2)
 def test_descriptions_languages_and_custom_values(self):
  self.w.editors[0].fields['wet'].setValue(.35);self.w.language.setCurrentIndex(self.w.language.findData('en'));self.assertIn('35%',self.w.preset_info.text());self.assertEqual(self.w.editors[0].fields['wet'].value(),.35)
  self.w.toggle_favorite();self.assertTrue(self.w.settings['favorites']);self.assertEqual(self.w.favorite.text(),'★')
 def test_import_queue_wav_only(self):
  p=self.w.pipeline();f=self.root/'album.vxqueue';f.write_text(json.dumps({'items':[{'source':str(self.a),'pipeline':p},{'source':'bad.mp3','pipeline':p}]}))
  with patch('qol_window.QFileDialog.getOpenFileName',return_value=(str(f),'')):self.w.load_queue_file()
  self.assertEqual(len(self.w.items),1)
 def test_drop_wav_only(self):
  mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(self.a)),QUrl.fromLocalFile(str(self.root/'bad.mp3'))]);event=QDropEvent(QPointF(10,10),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier);self.w.dropEvent(event);self.assertEqual(len(self.w.items),1)
 def test_rerender_existing_track_and_beta(self):
  from PySide6.QtWidgets import QLabel
  self.w.add_paths([self.a,self.b]);item=self.w.items[0];identity=item['id'];preset=item['pipeline'].copy();item.update(status='completed',job='old-job',output='old.wav',error='old error')
  self.w.render_queue();self.w.table.selectRow(0);self.w.rerun_button.click()
  self.assertEqual(len(self.w.items),2);self.assertEqual(item['id'],identity);self.assertEqual(item['pipeline'],preset);self.assertEqual(item['status'],'pending');self.assertNotIn('job',item);self.assertNotIn('error',item);self.assertTrue(self.a.exists())
  self.w.active=item;item['status']='running';self.w.rerun();self.assertEqual(item['status'],'running');self.w.active=None
  self.assertTrue(any('BETA' in label.text() for label in self.w.findChildren(QLabel)))
 def test_context_play_and_recent(self):
  self.w.add_paths([self.a]);self.assertTrue(self.w.recent_menu.actions());self.w.table.selectRow(0);self.w.audition.audio.setVolume(0);self.w.track_selected(force=True,autoplay=True)
  # Windows multimedia initialization can exceed two seconds after a cold start.
  for _ in range(500):
   APP.processEvents();QTest.qWait(20)
   if self.w.audition.player.position()>0:break
  self.assertGreater(self.w.audition.player.position(),0)
 def test_loudness_matching_and_player(self):
  before=hashlib.sha256(self.a.read_bytes()).hexdigest();result=[];worker=AudioPrepare(self.a,self.b,self.root/'Cache',1);worker.done.connect(result.append);worker.run();self.assertTrue(result)
  d=result[0];a,_=sf.read(d['matched'][0]);b,_=sf.read(d['matched'][1]);self.assertAlmostEqual(float(np.sqrt(np.mean(a*a))),float(np.sqrt(np.mean(b*b))),places=4);self.assertEqual(before,hashlib.sha256(self.a.read_bytes()).hexdigest())
  self.w.audition.token=1;self.w.audition.ready(d);self.w.audition.audio.setVolume(0);self.w.audition.toggle()
  for _ in range(30):APP.processEvents();QTest.qWait(20)
  self.assertEqual(self.w.audition.player.error(),QMediaPlayer.Error.NoError);self.assertGreater(self.w.audition.player.position(),0);self.w.audition.choose(1)
  for _ in range(10):APP.processEvents();QTest.qWait(20)
  self.assertEqual(self.w.audition.side,1)
if __name__=='__main__':unittest.main(verbosity=2)
