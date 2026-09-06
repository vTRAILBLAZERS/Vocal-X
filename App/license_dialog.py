"""Offline activation UI; no issuer, serial registry or private key imports."""
from datetime import timedelta
from pathlib import Path
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPlainTextEdit,QPushButton,QFileDialog,QDialogButtonBox,QApplication
from qol_audio import txt
import gui_i18n
import vocal_license as protocol
import license_service
class LicenseDialog(QDialog):
 def __init__(self,root,parent=None):
  super().__init__(parent);self.root=root;self.setWindowTitle(txt('Vocal X Beta – Lizenz','Vocal X Beta – License'));self.resize(650,540)
  layout=QVBoxLayout(self);self.summary=QLabel();self.summary.setWordWrap(True);layout.addWidget(self.summary)
  self.instructions=QLabel(txt('1. Beta-Seriennummer eingeben und Anfragecode erzeugen.\n2. Anfragecode an den Herausgeber senden.\n3. Den erhaltenen Activation Token einfügen oder importieren.','1. Enter your beta serial and generate a request code.\n2. Send the request code to the publisher.\n3. Paste or import the returned activation token.'));self.instructions.setWordWrap(True);layout.addWidget(self.instructions)
  self.serial=QLineEdit();self.serial.setPlaceholderText('VX-BETA-XXXX-XXXX-XXXX');self.serial.setMaxLength(64);layout.addWidget(self.serial)
  row=QHBoxLayout();self.generate=QPushButton(txt('Anfragecode erzeugen','Generate request'));self.generate.clicked.connect(self.make_request);row.addWidget(self.generate);self.copy=QPushButton(txt('Anfrage kopieren','Copy request'));self.copy.clicked.connect(lambda:QApplication.clipboard().setText(self.request.toPlainText()));row.addWidget(self.copy);layout.addLayout(row)
  self.request=QPlainTextEdit();self.request.setReadOnly(True);self.request.setMaximumHeight(90);layout.addWidget(self.request)
  self.token=QPlainTextEdit();self.token.setPlaceholderText('Activation Token (VXLIC1.…)');self.token.setMaximumHeight(110);layout.addWidget(self.token)
  row=QHBoxLayout();self.import_button=QPushButton(txt('Token importieren','Import token'));self.import_button.clicked.connect(self.import_token);row.addWidget(self.import_button);self.activate_button=QPushButton(txt('Aktivieren','Activate'));self.activate_button.clicked.connect(self.activate_token);row.addWidget(self.activate_button);layout.addLayout(row)
  self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
  close=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);close.button(QDialogButtonBox.StandardButton.Close).setText(txt('Schließen','Close'));close.rejected.connect(self.reject);layout.addWidget(close);self.refresh()
 def refresh(self):
  value,error=license_service.status(self.root)
  if error:self.summary.setText(txt('Status: Nicht aktiviert\n','Status: Not activated\n')+protocol.message(error,gui_i18n.LANG))
  else:
   last=protocol.timestamp(value['expires_at'])-timedelta(seconds=1)
   self.summary.setText(txt('Status: Aktiviert','Status: Activated')+'\n'+protocol.mask(value['serial'])+'\n'+txt('Gerät: Dieser PC','Device: This PC')+'\n'+txt('Gültig bis: ','Expires: ')+last.strftime('%d.%m.%Y')+' (UTC)')
  return value
 def make_request(self):
  try:self.request.setPlainText(license_service.activation_request(self.serial.text()));self.note.setText(txt('Der Anfragecode enthält nur Seriennummer und gehashte Gerätekennung. Er aktiviert die App noch nicht.','The request contains only the serial and hashed device identifier. It does not activate the app yet.'))
  except protocol.LicenseError as error:self.note.setText(protocol.message(error,gui_i18n.LANG));self.request.clear()
 def import_token(self):
  path,_=QFileDialog.getOpenFileName(self,txt('Activation Token importieren','Import activation token'),'','Vocal X License (*.vxlicense *.txt)')
  if not path:return
  try:
   if Path(path).stat().st_size>32768:raise ValueError('size')
   self.token.setPlainText(Path(path).read_text(encoding='utf-8-sig'))
  except (OSError,ValueError):self.note.setText(protocol.message(protocol.LicenseError('token'),gui_i18n.LANG))
 def activate_token(self):
  try:
   license_service.activate(self.root,self.token.toPlainText());self.token.clear();self.serial.clear();self.request.clear();self.refresh();self.note.setText(txt('Aktivierung gespeichert. Dieses Fenster kann geschlossen werden.','Activation saved. You can close this window.'))
  except protocol.LicenseError as error:self.note.setText(protocol.message(error,gui_i18n.LANG))
  except OSError:self.note.setText(txt('Lizenz konnte nicht gespeichert werden. Bitte den Benutzerdatenordner prüfen.','License could not be saved. Please check the user data folder.'))
