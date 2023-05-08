import os
import sys
import configparser
from pathlib import Path
from do_query import DoQuery, DataDownloader
from log_window import LogWindow
from pref_window import PrefWindow
from dl_window import DlWindow
# from qt_material import apply_stylesheet
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QGroupBox, QPushButton, QComboBox, QTableWidget, QAbstractScrollArea, QAbstractItemView, QTableWidgetItem, QScrollArea, QProgressBar, QRadioButton, QButtonGroup
from PyQt5.QtGui import QFont


"""
Main window
"""
class MainQuery(QMainWindow):
    def __init__(self, parent=None):
        super(MainQuery, self).__init__(parent)
        self.setStyleSheet(open(os.path.dirname(os.path.realpath(sys.argv[0]))+"/style.qss", "r").read())
        """
        Add the geometry
        """
        screen = QApplication.primaryScreen()
        rect = screen.availableGeometry()
        width, height = int(rect.width()*2./3), int(rect.height()*2./3.)
        xpos = int(rect.width()/2.-width/2)
        ypos = int(rect.height()/2.-height/2)
        self.setGeometry(xpos,ypos, width, height)
        self.setWindowTitle("ESOquery")
        """
        A menu bar
        """
        self.MenuBar = self.menuBar()
        # if platform.system() == 'Darwin':
        #     self.MenuBar.setNativeMenuBar(False)
        """
        Add the status bar
        """
        self.status = self.statusBar()

        self.query_window = QueryWindow(self)
        self.setCentralWidget(self.query_window)
        self.show()

class QueryWindow(QWidget):
    def __init__(self,parent=None):
        super(QueryWindow, self).__init__(parent)
        self.insts = ['AMBER', 'APEX', 'APICAM', 'CES', 'CRIRES', 'EFOSC2', 'EMMI', 'ERIS', 'ESPRESSO',\
                'FEROS', 'FORS1/2', 'GIRAFFE', 'GRAVITY', 'GROND', 'HARPS', 'HAWKI', 'ISAAC', 'KMOS',\
                'LGSF', 'NACO', 'MAD', 'MASCOT', 'MATISSE', 'MIDI', 'MUSE', 'OMEGACAM', 'PIONIER',\
                'SINFONI', 'SOFI', 'SPECULOOS', 'SPHERE', 'SUSI', 'TIMMI2', 'UVES', 'VIMOS', 'VINCI',\
                'VIRCAM', 'VISIR', 'WFCAM', 'WFI', 'XSHOOTER']
        self.doquery = DoQuery()
        self.datadownloader = DataDownloader()
        self.make_connection()
        self.initUI()

    @pyqtSlot(str)
    def set_status(self, val):
        self.parent().status.showMessage(val)
        QApplication.processEvents()

    @pyqtSlot(str)
    def set_log(self, val):
        self.logwindow.lt.logframe.append(val)
        QApplication.processEvents()

    def make_connection(self):
        self.doquery.changedStatus.connect(self.set_status)
        self.doquery.changedLog.connect(self.set_log)
        self.datadownloader.changedStatus.connect(self.set_status)
        self.datadownloader.changedLog.connect(self.set_log)

    def initUI(self):
        """
        The main window
        """
        self.raw = False
        self.font = QFont()
        self.font.setPointSize(8)
        self.logwindow = LogWindow(self)
        self._create_config()
        self._read_config()
        self.pref = PrefWindow(self)
        self.dlwindow = DlWindow(self)
        self._create_menubar()
        window = QVBoxLayout()
        window.addLayout(self._create_topbar())
        window.addLayout(self._create_main_panel())
        window.addLayout(self._create_progressbar())
        self.setLayout(window)
        self._create_table()
        self._qmoved = False
        self._dmoved = False

    def _create_progressbar(self):
        """
        Progressbar
        """
        bot_bar = QHBoxLayout()
        self.pbar = QProgressBar(self)
        self.pbar.setVisible(False)
        bot_bar.addWidget(self.pbar)
        return bot_bar

    def _raw_switch(self):
        self.raw = True
        self.inst.setVisible(True)

    def _p3_switch(self):
        self.raw = False
        self.inst.setVisible(False)

    def _create_topbar(self):
        starlabel = QLabel('Star name:', self)
        # self.starname = QLineEdit('HD61005', self)
        self.starname = QLineEdit(self)
        self.starname.setPlaceholderText("Search")
        self.starname.setFixedWidth(200)
        self.starname.returnPressed.connect(self.query_star)

        phase = QButtonGroup(self)
        self.p3but = QRadioButton('Phase 3')
        self.p3but.setChecked(True)
        self.p3but.clicked.connect(self._p3_switch)
        self.rawbut = QRadioButton('Raw data')
        self.rawbut.clicked.connect(self._raw_switch)
        phase.addButton(self.p3but)
        phase.addButton(self.rawbut)

        self.inslabel = QLabel('Instruments:', self)
        self.inslabel.setVisible(False)
        self.inst = QComboBox()
        self._update_inst()
        self.inst.setVisible(False)
		
        self.searchbut= QPushButton('Ok')
        self.searchbut.clicked.connect(self.query_star)
        self.searchbut.setDefault(True);
        self.searchbut.setAutoDefault(False);
        self.dlbut= QPushButton('Download')
        self.dlbut.clicked.connect(self._prep_dl)
        self.dlbut.setEnabled(False)

        top_bar = QHBoxLayout()
        top_bar.addWidget(starlabel)
        top_bar.addWidget(self.starname)
        top_bar.addStretch()
        top_bar.addWidget(self.inslabel)
        top_bar.addWidget(self.inst)
        top_bar.addWidget(self.rawbut)
        top_bar.addWidget(self.p3but)
        top_bar.addWidget(self.searchbut)
        top_bar.addWidget(self.dlbut)
        return top_bar

    def _update_inst(self):
        self.inst.clear()
        self.inst.addItems(self.pref_insts)
        if len(self.pref_insts) > 1:
            self.inst.addItem('All above')
        if len(self.pref_insts) == 0:
            self.set_status('No instruments selected. Go to the preferences and select at least one.')

    def _prep_dl(self):
        """
        Method to download the data. There should be a
        popup window with some additional options.

        I need to pass the list of urls to that window
        """
        if self.obstable.currentRow() != -1:
            if self.raw:
                self.dlwindow.dl.b1.setEnabled(True)
                self.dlwindow.dl.b2.setEnabled(True)
                self.dlwindow.dl.b3.setEnabled(True)
            else:
                self.dlwindow.dl.b1.setEnabled(False)
                self.dlwindow.dl.b2.setEnabled(False)
                self.dlwindow.dl.b3.setEnabled(False)
            self.dlwindow.show()

    def _start_download(self, selector):
        """
        Will be called from the DlWindow
        """
        self.pbar.setVisible(True)
        row = self.obstable.currentRow()
        index = int(self.obstable.item(row,0).text())

        self.datadownloader.user = self.user
        self.datadownloader.password = self.password
        self.datadownloader.raw = self.raw
        self.datadownloader.dpath = self.dpath
        self.datadownloader.access_url = self.results[index]['access_url'].split('\n')
        if self.raw:
            self.datadownloader.datalink_url = self.results[index]['datalink_url'].split('\n')
        else:
            self.datadownloader.obs_id = self.results[index]['obs_id'].split('\n')
        self.datadownloader.selector = selector

        thread = QThread(parent = self) # To avoid the UI to freeze during the query
        if not self._dmoved:
            self.datadownloader.moveToThread(thread)
            self._dmoved = True # To avoid having to move the thread again for the 2nd query
        thread.started.connect(self.datadownloader._get_data)
        thread.start()

        self.starname.setEnabled(False)
        self.searchbut.setEnabled(False)
        self.obstable.setEnabled(False)
        self.dlbut.setEnabled(False)
        self.datadownloader.progress.connect(self._update_pbar)
        self.datadownloader.finished.connect(thread.quit)
        self.datadownloader.finished.connect(lambda: self.searchbut.setEnabled(True))
        self.datadownloader.finished.connect(lambda: self.dlbut.setEnabled(True))
        self.datadownloader.finished.connect(lambda: self.starname.setEnabled(True))
        self.datadownloader.finished.connect(lambda: self.pbar.setVisible(False))
        self.datadownloader.finished.connect(lambda: self.pbar.setValue(0))
        self.datadownloader.finished.connect(lambda: self.obstable.setEnabled(True))

    def _update_pbar(self, value):
        self.pbar.setValue(value)

    def _create_main_panel(self):
        """
        Main panel
        """
        self.obstable = ObsTable()
        """
        Info box
        """
        scroll = QScrollArea() 
        info = QWidget()
        info.setFont(self.font)
        self.infobox = QVBoxLayout()
        info.setLayout(self.infobox)

        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(info)

        main_panel = QHBoxLayout()
        main_panel.addWidget(self.obstable, 75)
        main_panel.addWidget(scroll, 25)
        return main_panel

    def _create_config(self):
        """
        Create the config file directory
        """
        filename = str(Path.home()) + '/.config/esoquery/esoquery.conf'
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        if not Path(filename).is_file():
            output = configparser.ConfigParser()
            output.read(filename)
            output.optionxform = str
            output['ESO']={
                'login': ' ',
                'password': ' '
            }
            output['DATA']={
                'path': '{}'.format(str(Path.home()))
            }
            output['INSTRUMENTS']={}
            for inst in self.insts:
                if inst == 'SPHERE': 
                    output['INSTRUMENTS'][inst] = 'True'
                else:
                    output['INSTRUMENTS'][inst] = 'False'
            with open(filename,'w') as file_object:
                output.write(file_object)
        self.set_status('Checking for config file: {}'.format(filename))

    def _read_config(self):
        """
        Read the config file
        """
        self.pref_insts = []
        filename = str(Path.home()) + '/.config/esoquery/esoquery.conf'
        output = configparser.ConfigParser()
        output.optionxform = str
        output.read(filename)
        if output.has_section('ESO'):
            self.user = output['ESO']['login']
            self.password = output['ESO']['password']
        else:
            self.user, self.password = None, None
        if output.has_section('DATA'):
            self.dpath = output['DATA']['path']
        else:
            self.dpath = None
        if output.has_section('INSTRUMENTS'):
            for key in output['INSTRUMENTS'].keys():
                if output['INSTRUMENTS'][key] == 'True':
                    self.pref_insts.append(key)
        """
        Display some info in the log
        """
        if self.user is not None and self.user != '':
            self.set_log('User name is: {}'.format(self.user))
        if self.password is not None and self.password != '':
            self.set_log('Password is set, but not shown here.')
        if self.dpath is not None and self.dpath != '':
            self.set_log('Data will be saved in: {}'.format(self.dpath))

    def query_star(self):
        """
        Search the ESO archive for the selected star and instrument
        """
        if self.starname.text() != '':
            self.doquery.raw = self.raw
            self.doquery.starname = self.starname.text()
            self.doquery.instrument = self.inst.currentText()
            self.doquery.user = self.user
            self.doquery.password = self.password
            self.doquery.pref_insts = self.pref_insts

            thread = QThread(parent = self) # To avoid the UI to freeze during the query
            if not self._qmoved:
                self.doquery.moveToThread(thread)
                self._qmoved = True # To avoid having to move the thread again for the 2nd query
            thread.started.connect(self.doquery.start_query)
            thread.start()
            """
            Make sure we cannot do much during the query
            """
            self.starname.setEnabled(False)
            self.searchbut.setEnabled(False)
            self.dlbut.setEnabled(False)
            self.export_file.setEnabled(False)
            self.obstable.setEnabled(False)
            self.doquery.finished.connect(thread.quit)
            self.doquery.finished.connect(lambda: self._update_table(self.doquery.obinfo))
            self.doquery.finished.connect(lambda: self.searchbut.setEnabled(True))
            self.doquery.finished.connect(lambda: self.starname.setEnabled(True))
            self.doquery.finished.connect(lambda: self.obstable.setEnabled(True))
            self.doquery.finished.connect(lambda: self.export_file.setEnabled(True))
        else:
            self.set_log('No star name provide, will not do anything')
            self._update_table([])

    def _create_table(self):
        """
        Create the table that will be used.
        """
        self.obstable.setFont(self.font)
        self.obstable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.obstable.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.obstable.verticalHeader().setVisible(False)
        self.obstable.horizontalHeader().setVisible(False)
        self.obstable.horizontalHeader().setStretchLastSection(True)
        self.obstable.setSortingEnabled(True)

        self.obstable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.obstable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.obstable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.obstable.setAlternatingRowColors(True)
        self.obstable.move(0,0)
        """
        Actions on single clik and double clicks
        """
        self.obstable.clicked.connect(self.singleClicked_table)

    def _delete_infobox(self):
        """
        Delete the data in the infobox
        """
        for i in reversed(range(self.infobox.count())): 
            widgetToRemove = self.infobox.itemAt(i).widget()
            self.infobox.removeWidget(widgetToRemove)
            try:
                widgetToRemove.setParent(None)
            except:
                pass

    def singleClicked_table(self):
        """
        What happens when selecting a row
        """
        row = self.obstable.currentRow()
        index = int(self.obstable.item(row,0).text())
        self._delete_infobox()
        for key in self.doquery._keywords:
            if key not in self.doquery._ignorekey:
                tmp = QLabel('<strong>{}:</strong><br/>{}'.format(key, self.results[index][key].replace('\n','<br/>')), self)
                tmp.setTextFormat(Qt.RichText)
                tmp.setWordWrap(True)
                self.infobox.addWidget(tmp)
        self.infobox.addStretch()
        """
        Able the download button
        """
        # if not self._dmoved: # Only I am not downloading data already ...
        self.dlbut.setEnabled(True)

    def _update_table(self, results):
        """
        Update the obstable with the results
        """
        self.results = results
        if self.raw:
            self.labels = ['ID', 'object', 'instrument', 'dp_tech', 'prog_id', 'obsnight', 
                      'release_date', 'nfiles', 'pi_coi']
        else:
            self.labels = ['ID', 'target_name', 'instrument_name', 'obstech', 'proposal_id',
                      'nfiles', 'obs_creator_name']
        nr = len(self.results)
        self.obstable.setRowCount(nr)
        self.obstable.setColumnCount(len(self.labels))
        # self.obstable.setHorizontalHeaderLabels(proper_labels)
        for i in range(nr):
            self.obstable.setItem(i,0, QTableWidgetItem(str(i)))
            for j in range(1,len(self.labels)):
                self.obstable.setItem(i,j, QTableWidgetItem(str(self.results[i][self.labels[j]])))

        """
        Hide some of the columns
        """
        self.obstable.setColumnHidden(0, True)
        self.obstable.resizeColumnsToContents()
        self.obstable.resizeRowsToContents()
        """
        Refresh the infobox if a row was selected
        """
        if self.obstable.currentRow() != -1:
            # self.dlbut.setEnabled(True)
            # self.singleClicked_table()
            self.obstable.clearSelection()

    # -----------------------------------------------------------------------------
    # For the top menu bar
    # -----------------------------------------------------------------------------
    def _create_menubar(self):
        """
        To import things, either a single PDF or a bibtex
        """
        logBar = self.parent().MenuBar.addMenu('File')
        action = logBar.addAction('Preferences')
        action.triggered.connect(lambda: self.displayPref())
        self.export_file = logBar.addAction('Export')
        self.export_file.setEnabled(False)
        self.export_file.triggered.connect(lambda: self.export_csv())
        # logBar.addSeparator()
        action = logBar.addAction('Quit')
        action.triggered.connect(lambda: self.parent().close())

        logBar = self.parent().MenuBar.addMenu('Log')
        action = logBar.addAction('Show')
        action.triggered.connect(lambda: self.displayLog())
        logBar.addSeparator()
        action = logBar.addAction('Clear')
        action.triggered.connect(lambda: self.clear_log())

    def export_csv(self):
        if self.raw:
            filename = '{}/esoquery_{}_raw.csv'.format(self.dpath, self.starname.text().replace(' ', '_'))
        else:
            filename = '{}/esoquery_{}_phase3.csv'.format(self.dpath, self.starname.text().replace(' ', '_'))
        f = open(filename, 'w')
        for i in range(len(self.results)):
            txt = ''
            for j in range(1,len(self.labels)):
                txt += str(self.results[i][self.labels[j]]).replace('\n', ' ')
                if j != len(self.labels)-1:
                    txt += ';'
                else:
                    txt += '\n'
            f.write(txt)
        f.close()
        self.set_status('File saved to {}'.format(filename))

    def displayPref(self):
        self.pref.show()

    def displayLog(self):
        self.logwindow.show()

    def clear_log(self):
        self.logwindow.lt.logframe.clear()

class ObsTable(QTableWidget):
    """docstring for createTable"""
    enter_key = pyqtSignal()
    del_key = pyqtSignal()
    home_key = pyqtSignal()
    end_key = pyqtSignal()

    def __init__(self, parent = None):
        super(ObsTable, self).__init__(parent)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.enter_key.emit()
        elif key == Qt.Key_Delete:
            self.del_key.emit()
        elif key == Qt.Key_Home:
            self.home_key.emit()
        elif key == Qt.Key_End:
            self.end_key.emit()
        else:
            super(ObsTable, self).keyPressEvent(event)



if __name__ == '__main__':
        app = QApplication(sys.argv)
        win = MainQuery()
        # apply_stylesheet(app, theme='light_blue.xml')
        win.show()
        sys.exit(app.exec_())
