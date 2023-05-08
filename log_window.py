from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget,QTextEdit,QVBoxLayout,QHBoxLayout,QMainWindow, QGroupBox, QPushButton 


"""
Log Window
"""
class LogWindow(QMainWindow):
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        # self.setGeometry(200,200,450,600)
        self.lt = Log(self)
        self.setCentralWidget(self.lt)

class Log(QWidget):
    def __init__(self, parent=None):
        super(Log, self).__init__(parent)
        self.initUI()

    @pyqtSlot()
    def on_click_clear(self):
        self.parent().parent().logwindow.lt.logframe.clear()

    @pyqtSlot()
    def on_click_close(self):
        self.parent().close()

    def initUI(self):
        """
        The main window
        """
        self.logframe = QTextEdit()
        self.logframe.setReadOnly(True)
        clearbut = QPushButton('Clear')
        clearbut.clicked.connect(self.on_click_clear)
        closebut = QPushButton('Close')
        closebut.clicked.connect(self.on_click_close)

        main = QVBoxLayout()
        grid = QVBoxLayout()
        groupBox = QGroupBox('Log Information')
        vbox = QVBoxLayout()
        vbox.addWidget(self.logframe)
        groupBox.setLayout(vbox)
        grid.addWidget(groupBox)

        buts = QHBoxLayout()
        buts.addStretch()
        buts.addWidget(clearbut, alignment = Qt.AlignRight)
        buts.addWidget(closebut, alignment = Qt.AlignRight)

        main.addLayout(grid)
        main.addLayout(buts)
        self.setLayout(main)


