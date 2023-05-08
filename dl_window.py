from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit, QMainWindow, QGroupBox, QPushButton, QFileDialog, QRadioButton

"""
Download window
"""
class DlWindow(QMainWindow):
    def __init__(self, parent=None):
        super(DlWindow, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.dl = Dl(self)
        self.setCentralWidget(self.dl)



class Dl(QWidget):
    def __init__(self, parent=None):
        super(Dl, self).__init__(parent)
        self.initUI()

    @pyqtSlot()
    def on_click_ok(self):
        selector = ''
        if self.b1.isChecked():
            selector = 'sci'
        if self.b2.isChecked():
            selector = 'raw2raw'
        if self.b3.isChecked():
            selector = 'raw2master'
        self.parent().close()
        self.parent().parent()._start_download(selector)

    @pyqtSlot()
    def on_click_c(self):
        self.parent().close()

    @pyqtSlot()
    def pref_ok(self):
        self.parent().parent().pref.show()

    def initUI(self):
        """
        Preferences button
        """
        prefbut = QPushButton('Edit preferences')
        prefbut.clicked.connect(self.pref_ok)
        """
        Radio buttons
        """
        self.b1 = QRadioButton('Science files only')
        self.b1.setChecked(True)
        self.b2 = QRadioButton('Science and raw calibration files')
        self.b3 = QRadioButton('Science and processed calibration files')
        """
        Ok and cancel buttons
        """
        okbut = QPushButton('Download')
        okbut.clicked.connect(self.on_click_ok)
        cbut = QPushButton('Cancel')
        cbut.clicked.connect(self.on_click_c)
        """
        Define the layout
        """
        main = QVBoxLayout()
        grid = QVBoxLayout()
        """
        User info box
        """
        groupBox = QGroupBox('Preferences')
        vbox = QVBoxLayout()
        vbox.addWidget(prefbut)
        vbox.addStretch()
        groupBox.setLayout(vbox)
        grid.addWidget(groupBox)
        """
        Data stuff
        """
        groupBox = QGroupBox('Type of data:')
        vbox = QVBoxLayout()
        vbox.addWidget(self.b1)
        vbox.addWidget(self.b2)
        vbox.addWidget(self.b3)
        groupBox.setLayout(vbox)
        grid.addWidget(groupBox)
        """
        Add the buttons
        """
        buts = QHBoxLayout()
        buts.addStretch()
        buts.addWidget(okbut, alignment = Qt.AlignRight)
        buts.addWidget(cbut, alignment = Qt.AlignRight)

        main.addLayout(grid)
        main.addLayout(buts)
        self.setLayout(main)



