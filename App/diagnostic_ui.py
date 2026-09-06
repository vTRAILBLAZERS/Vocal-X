from datetime import datetime
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QPlainTextEdit,QFileDialog,QMessageBox
from qol_audio import txt
from diagnostics import redact,save_report

def export_report(window,item=None):
 path,_=QFileDialog.getSaveFileName(window,txt('Diagnosebericht speichern','Save diagnostic report'),'VocalX-Diagnostic-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.txt','Text (*.txt)')
 if not path:return
 try:
  save_report(path,window.root,window.hw,item);window.status_label.setText(txt('Diagnosebericht gespeichert.','Diagnostic report saved.'))
 except (OSError,ValueError) as error:
  QMessageBox.warning(window,'Vocal X',txt('Speichern fehlgeschlagen. Bitte einen neuen Dateinamen wählen. ','Save failed. Please choose a new filename. ')+redact(error))

class FailureDialog(QDialog):
 def __init__(self,window,item):
  super().__init__(window);self.setWindowTitle(txt('Verarbeitung fehlgeschlagen','Processing failed'));self.resize(580,240)
  layout=QVBoxLayout(self);label=QLabel(txt('Bei der Verarbeitung eines Tracks ist ein Fehler aufgetreten. Die Warteschlange kann mit dem nächsten Track fortfahren.','An error occurred while processing a track. The queue can continue with the next track.'));label.setWordWrap(True);layout.addWidget(label)
  details=QPlainTextEdit(redact(item.get('error','')));details.setReadOnly(True);details.hide();layout.addWidget(details)
  row=QHBoxLayout();show=QPushButton('Details');show.clicked.connect(lambda:details.setVisible(not details.isVisible()))
  retry=QPushButton(txt('Erneut versuchen','Try again'))
  def retry_item():
   if item in window.items and item is not window.active and item.get('status') in ('failed','interrupted'):
    item['status']='pending';window.persist();window.render_queue();window.status_label.setText(txt('Track eingereiht. Start / Fortsetzen drücken.','Track queued. Press Start / Resume.'))
   self.close()
  retry.clicked.connect(retry_item);save=QPushButton(txt('Diagnose speichern','Save diagnostic'));save.clicked.connect(lambda:export_report(window,item));close=QPushButton(txt('Schließen','Close'));close.clicked.connect(self.close)
  for button in (show,retry,save,close):row.addWidget(button)
  layout.addLayout(row)
