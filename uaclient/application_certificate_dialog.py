from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox

from uaclient.applicationcertificate_ui import Ui_ApplicationCertificateDialog
from uawidgets.utils import trycatchslot

if TYPE_CHECKING:
    from uaclient.mainwindow import Window


class ApplicationCertificateDialog(QDialog):
    def __init__(self, parent: "Window") -> None:
        QDialog.__init__(self)
        self.ui = Ui_ApplicationCertificateDialog()
        self.ui.setupUi(self)

        self.uaclient = parent.uaclient
        self._parent = parent

        self.ui.certificateLabel.setText(self.uaclient.application_certificate_path or "")
        self.ui.privateKeyLabel.setText(self.uaclient.application_private_key_path or "")

        self.ui.certificateButton.clicked.connect(self.get_certificate)
        self.ui.privateKeyButton.clicked.connect(self.get_private_key)
        self.ui.generateButton.clicked.connect(self.generate)

    def show_error(self, ex: Exception) -> None:
        QMessageBox.warning(self, "Certificate generation failed", str(ex))

    @trycatchslot
    def generate(self) -> None:
        cert, key = self.uaclient.generate_application_certificate()
        self.ui.certificateLabel.setText(cert)
        self.ui.privateKeyLabel.setText(key)

    @property
    def certificate_path(self) -> str | None:
        text = self.ui.certificateLabel.text()
        if text == "None":
            return None
        return text

    @certificate_path.setter
    def certificate_path(self, value: str | None) -> None:
        self.ui.certificateLabel.setText(value or "")

    @property
    def private_key_path(self) -> str | None:
        text = self.ui.privateKeyLabel.text()
        if text == "None":
            return None
        return text

    @private_key_path.setter
    def private_key_path(self, value: str | None) -> None:
        self.ui.privateKeyLabel.setText(value or "")

    def get_certificate(self) -> None:
        path, ok = QFileDialog.getOpenFileName(
            self,
            "Select application certificate",
            self.uaclient.application_certificate_path or "",
            "Certificate (*.der)",
        )
        if ok:
            self.ui.certificateLabel.setText(path)

    def get_private_key(self) -> None:
        path, ok = QFileDialog.getOpenFileName(
            self,
            "Select application private key",
            self.uaclient.application_private_key_path or "",
            "Private key (*.pem)",
        )
        if ok:
            self.ui.privateKeyLabel.setText(path)
