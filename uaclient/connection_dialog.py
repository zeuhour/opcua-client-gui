from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QListWidgetItem,
    QMessageBox,
    QRadioButton,
)

from asyncua import ua

from uaclient.connection_ui import Ui_ConnectionDialog
from uawidgets.utils import trycatchslot

if TYPE_CHECKING:
    from uaclient.mainwindow import Window

MODE_ORDER = ["None", "Sign", "SignAndEncrypt"]

_TOKEN_RADIO = {
    ua.UserTokenType.Anonymous: "anonymousRadioButton",
    ua.UserTokenType.UserName: "usernameRadioButton",
    ua.UserTokenType.Certificate: "certificateRadioButton",
}


def _mode_label(name: str) -> str:
    return "None" if name == "None_" else name


class ConnectionDialog(QDialog):
    def __init__(self, parent: "Window", uri: str) -> None:
        QDialog.__init__(self)
        self.ui = Ui_ConnectionDialog()
        self.ui.setupUi(self)

        self.uaclient = parent.uaclient
        self.uri = uri
        self._parent = parent
        self._endpoints: list[ua.EndpointDescription] = []

        self._security_group = QButtonGroup(self)
        self._auth_group = QButtonGroup(self)
        self._auth_group.addButton(self.ui.anonymousRadioButton)
        self._auth_group.addButton(self.ui.usernameRadioButton)
        self._auth_group.addButton(self.ui.certificateRadioButton)

        self.ui.refreshButton.clicked.connect(self.query)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.connectButton.clicked.connect(self.accept)
        self.ui.userCertificateButton.clicked.connect(self._pick_user_certificate)
        self.ui.userPrivateKeyButton.clicked.connect(self._pick_user_private_key)
        self._auth_group.buttonToggled.connect(self._update_auth_enabled)
        self._security_group.buttonToggled.connect(self._rebuild_endpoint_list)
        self.ui.endpointListWidget.currentItemChanged.connect(self._update_connect_enabled)

        self._seed_auth_fields()
        self.query()
        self._update_connect_enabled()

        self.ui.connectButton.setDefault(True)
        self.ui.connectButton.setFocus()

    def show_error(self, ex: Exception) -> None:
        QMessageBox.warning(self, "Connection error", str(ex))

    def _seed_auth_fields(self) -> None:
        radios = {
            "username": self.ui.usernameRadioButton,
            "certificate": self.ui.certificateRadioButton,
        }
        radios.get(self.uaclient.auth_mode, self.ui.anonymousRadioButton).setChecked(True)
        self.ui.usernameLineEdit.setText(self.uaclient.username or "")
        self.ui.userCertificateLineEdit.setText(self.uaclient.user_certificate_path or "")
        self.ui.userPrivateKeyLineEdit.setText(self.uaclient.user_private_key_path or "")
        self._update_auth_enabled()

    @trycatchslot
    def query(self) -> None:
        self._endpoints = self.uaclient.get_endpoints(self.uri)
        self._build_security_radios()
        self._rebuild_endpoint_list()

    def _build_security_radios(self) -> None:
        self._security_group.blockSignals(True)
        for button in self._security_group.buttons():
            self._security_group.removeButton(button)
            self.ui.securityModeLayout.removeWidget(button)
            button.deleteLater()

        offered = {_mode_label(edp.SecurityMode.name) for edp in self._endpoints}
        remembered = self.uaclient.security_mode or "None"
        for mode in MODE_ORDER:
            if mode not in offered:
                continue
            button = QRadioButton(mode, self)
            self._security_group.addButton(button)
            self.ui.securityModeLayout.addWidget(button)
        self._security_group.blockSignals(False)

        buttons = self._security_group.buttons()
        if not buttons:
            return
        chosen = next((b for b in buttons if b.text() == remembered), buttons[0])
        chosen.setChecked(True)

    @trycatchslot
    def _rebuild_endpoint_list(self) -> None:
        self.ui.endpointListWidget.clear()
        button = self._security_group.checkedButton()
        if button is None:
            self._update_connect_enabled()
            return
        mode = button.text()
        remembered = self.uaclient.endpoint_url
        selected_row = 0
        for edp in self._endpoints:
            if _mode_label(edp.SecurityMode.name) != mode:
                continue
            policy = edp.SecurityPolicyUri.split("#")[1]
            item = QListWidgetItem(f"{policy} | {edp.SecurityMode.name} | {edp.EndpointUrl}")
            item.setData(Qt.ItemDataRole.UserRole, edp)
            self.ui.endpointListWidget.addItem(item)
            if edp.EndpointUrl == remembered:
                selected_row = self.ui.endpointListWidget.count() - 1
        if self.ui.endpointListWidget.count():
            self.ui.endpointListWidget.setCurrentRow(selected_row)
        self._update_connect_enabled()

    def _selected_endpoint(self) -> ua.EndpointDescription | None:
        item = self.ui.endpointListWidget.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _update_connect_enabled(self, *args: object) -> None:
        endpoint = self._selected_endpoint()
        self.ui.connectButton.setEnabled(endpoint is not None)
        self._update_supported_auth(endpoint)

    def _update_supported_auth(self, endpoint: ua.EndpointDescription | None) -> None:
        if endpoint is None:
            return
        supported = {token.TokenType for token in endpoint.UserIdentityTokens}
        for token_type, radio_name in _TOKEN_RADIO.items():
            getattr(self.ui, radio_name).setEnabled(token_type in supported)
        checked = self._auth_group.checkedButton()
        if checked is not None and checked.isEnabled():
            return
        for token_type in (ua.UserTokenType.Anonymous, ua.UserTokenType.UserName, ua.UserTokenType.Certificate):
            if token_type in supported:
                getattr(self.ui, _TOKEN_RADIO[token_type]).setChecked(True)
                break

    def _update_auth_enabled(self, *args: object) -> None:
        is_username = self.ui.usernameRadioButton.isChecked()
        is_certificate = self.ui.certificateRadioButton.isChecked()
        self.ui.usernameLineEdit.setEnabled(is_username)
        self.ui.passwordLineEdit.setEnabled(is_username)
        self.ui.userCertificateLineEdit.setEnabled(is_certificate)
        self.ui.userCertificateButton.setEnabled(is_certificate)
        self.ui.userPrivateKeyLineEdit.setEnabled(is_certificate)
        self.ui.userPrivateKeyButton.setEnabled(is_certificate)

    def _pick_user_certificate(self) -> None:
        path, ok = QFileDialog.getOpenFileName(self, "Select certificate", self.user_certificate_path, "Certificate (*.der *.pem)")
        if ok:
            self.ui.userCertificateLineEdit.setText(path)

    def _pick_user_private_key(self) -> None:
        path, ok = QFileDialog.getOpenFileName(self, "Select private key", self.user_private_key_path, "Private key (*.pem)")
        if ok:
            self.ui.userPrivateKeyLineEdit.setText(path)

    @property
    def security_mode(self) -> str | None:
        endpoint = self._selected_endpoint()
        if endpoint is None:
            return None
        name = endpoint.SecurityMode.name
        return None if name == "None_" else name

    @property
    def security_policy(self) -> str | None:
        endpoint = self._selected_endpoint()
        if endpoint is None:
            return None
        policy = endpoint.SecurityPolicyUri.split("#")[1]
        return None if policy == "None" else policy

    @property
    def endpoint_url(self) -> str | None:
        endpoint = self._selected_endpoint()
        return endpoint.EndpointUrl if endpoint is not None else None

    @property
    def auth_mode(self) -> str:
        if self.ui.usernameRadioButton.isChecked():
            return "username"
        if self.ui.certificateRadioButton.isChecked():
            return "certificate"
        return "anonymous"

    @property
    def username(self) -> str | None:
        return self.ui.usernameLineEdit.text() or None

    @property
    def password(self) -> str | None:
        return self.ui.passwordLineEdit.text() or None

    @property
    def user_certificate_path(self) -> str:
        return self.ui.userCertificateLineEdit.text()

    @property
    def user_private_key_path(self) -> str:
        return self.ui.userPrivateKeyLineEdit.text()
