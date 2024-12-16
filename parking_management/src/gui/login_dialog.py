from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                              QPushButton, QFormLayout, QMessageBox)
from PySide6.QtCore import Qt

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理员登录")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("用户名:", self.username_input)
        form_layout.addRow("密码:", self.password_input)

        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.verify_credentials)

        layout.addLayout(form_layout)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def verify_credentials(self):
        """验证管理员账号密码"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        # 默认管理员账号为admin，密码为1234
        if username == "admin" and password == "1234":
            self.accept()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("登录失败")
            msg_box.setText("密码错误")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setText("确定")
            msg_box.exec() 