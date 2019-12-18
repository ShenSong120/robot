from PyQt5.QtWidgets import QTextEdit, QLineEdit, QWidget, QVBoxLayout
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from GlobalVar import GloVar


class ShowScriptTab(QWidget):

    signal = pyqtSignal(str)

    def __init__(self, parent):
        super(ShowScriptTab, self).__init__(parent)
        self.parent = parent
        self.setStyleSheet('font-family : %s; font-size: 13pt' % GloVar.font)
        self.initUI()


    def initUI(self):
        # script_title
        self.script_title = QLineEdit(self)
        self.script_title.setReadOnly(True)
        self.script_title.setText('空白')
        # script_edit
        self.script_edit = QTextEdit(self)
        self.script_edit.setReadOnly(True)
        # self.script_edit.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.script_edit.setWordWrapMode(QTextOption.NoWrap)
        self.script_edit.setStyleSheet('background-color:#C0D8F0')
        self.script_edit.setFont(QFont(GloVar.font, 13))
        # 布局
        self.general_layout = QVBoxLayout(self)
        self.general_layout.setSpacing(0)
        self.general_layout.setContentsMargins(0, 0, 0, 0)
        self.general_layout.addWidget(self.script_title)
        self.general_layout.addWidget(self.script_edit)
        self.setLayout(self.general_layout)