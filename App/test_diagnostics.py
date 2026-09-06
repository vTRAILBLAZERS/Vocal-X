import json
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QProcess, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton
import test_activation as activation_tests
APP=activation_tests.APP
from qol_window import Window
from diagnostics import report, record, save_report, redact

class DiagnosticTests(unittest.TestCase):
 def setUp(self):
  self.fixture=activation_tests.ActivationTests();self.fixture.setUp();self.root=self.fixture.root
 def tearDown(self):self.fixture.tearDown()
 def test_secrets_and_audio_excluded(self):
  item={'source':str(self.fixture.source),'pipeline':self.fixture.p,'error':'VX-BETA-ABCD-EFGH-1234 VXLIC1.abc.def VXREQ1.abc -----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----','audio':'AUDIO_CONTENT'}
  text=report(self.root,{'gpu':'test'},item)
  for secret in ['ABCD-EFGH','VXLIC1.abc','VXREQ1.abc','\nsecret','AUDIO_CONTENT']:self.assertNotIn(secret,text)
  self.assertIn('Input WAV Validation: OK',text);self.assertIn('NOT PERFORMED',text)
  record(self.root,'failure',error=item['error'],audio='AUDIO_CONTENT')
  log=next((self.root/'Logs').glob('*.log')).read_text(encoding='utf-8');self.assertNotIn('ABCD-EFGH',log);self.assertNotIn('AUDIO_CONTENT',log);json.loads(log)
 def test_export_protects_existing_file(self):
  source=self.fixture.source;original=source.read_bytes()
  with self.assertRaises(FileExistsError):save_report(source,self.root)
  self.assertEqual(original,source.read_bytes());save_report(self.root/'report.txt',self.root);self.assertIn('DIAGNOSTIC',(self.root/'report.txt').read_text())
 def test_log_failure_is_nonfatal(self):
  (self.root/'Logs').write_text('blocked')
  record(self.root,'test',error='error')
 def test_failure_dialog_retry_and_queue_continuation(self):
  window=Window(self.root,startup=False);window.timer.stop();window.session_timer.stop()
  item=dict(id='failed',source=str(self.fixture.source),pipeline=self.fixture.p,status='running',error='test failure')
  window.items=[item];window.active=item;window.cancelled=False;window.buffer='';window.auto=True
  try:
   with patch.object(window,'next_job') as next_job:
    window.finished(1,QProcess.ExitStatus.NormalExit);QTest.qWait(300);APP.processEvents();next_job.assert_called_once()
   self.assertEqual(item['status'],'failed');self.assertEqual(window.failure_dialog.windowModality(),Qt.WindowModality.NonModal)
   buttons=window.failure_dialog.findChildren(QPushButton);next(b for b in buttons if b.text() in ('Erneut versuchen','Try again')).click();self.assertEqual(item['status'],'pending');self.assertTrue(self.fixture.source.exists())
  finally:window.auto=False;window.close();APP.processEvents()

if __name__=='__main__':unittest.main(verbosity=2)
