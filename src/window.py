from threading import Thread, Event
from PySide6.QtCore import Slot, QSize, Qt, QThreadPool, QRunnable, QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QComboBox, QFileDialog, QSystemTrayIcon, QStyle, QCheckBox, QWidget, QPushButton, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout
from papers import version, swapPaper, fetchPaper, scheduledPaperSwap
import traceback, sys
from flytrap import *


# Thread pool information
# https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''
    finished = Signal()  # QtCore.Signal
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(object)

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        try:
            result = self.fn(
                *self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class MainWindow(QMainWindow):

    check_box = None
    tray_icon = None

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.threadpool = QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.setWindowTitle("FlyTrap for FlyPaper (" + version + ")")

        self.running = False
        # self.thread_events = []
        self.current_event = False

        # Download Directory
        self.download_group = 'Recent'
        self.download_schedule = 'Every hour'
        self.user_name = ''
        # self.downloading = False
        self.showingOptions = False

        # Main Layout box
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10,10,10,10)
        self.layout.setSpacing(5)

        # Main Container
        container = QWidget()
        container.setFixedSize(QSize(440,200))
        container.setLayout(self.layout)

        # Set central widget
        self.setCentralWidget(container)

        # Define status message label
        self.statusMessage = QLabel()
        self.statusMessage.setAlignment(Qt.AlignCenter)
        self.statusMessage.setStyleSheet("QLabel {background-color: #E1E1E1;}")
        self.statusMessage.setText('')


        self.showDownloadOptions()

        self.fetchThread()
        # threadedFetch(self.download_group, self.user_name, self.statusMessage)

    @Slot()
    def showDownloadOptions(self):

        self.optionsGroup = QHBoxLayout()

        self.randomButton = QPushButton("Swap FlyPaper")
        self.randomButton.setCheckable(False)
        self.randomButton.clicked.connect(self.swapPaperNow)
        self.layout.addWidget(self.randomButton)

        self.showingOptions = True
        self.instructions = QLabel()
        self.instructions.setText('FlyPaper filters:')


        self.downloadGroup = QComboBox()
        self.downloadGroup.addItem('All Paper')
        self.downloadGroup.addItem('Featured')
        self.downloadGroup.addItem('Liked by')
        self.downloadGroup.addItem('Created by')
        self.downloadGroup.setMinimumWidth(150)
        self.downloadGroup.currentTextChanged.connect(self.selectDownloadGroup)


        self.userName = QLineEdit()
        self.userName.textChanged.connect(self.usernameChanged)
        self.userName.setPlaceholderText('Enter a username')
        self.userName.setEnabled(False)

        self.layout.addWidget(self.instructions)
        self.optionsGroup.addWidget(self.downloadGroup)
        self.optionsGroup.addWidget(self.userName)
        self.layout.addLayout(self.optionsGroup)


        self.scheduleLabel = QLabel()
        self.scheduleLabel.setText('FlyPaper update schedule:')
        self.layout.addWidget(self.scheduleLabel)

        # Download buttons layout
        self.downloadButtonsLayout = QHBoxLayout()

        self.downloadOptionBox = QHBoxLayout()
        self.downloadSchedule = QComboBox()
        self.downloadSchedule.addItem('Every 2 hours')
        self.downloadSchedule.addItem('Every hour')
        self.downloadSchedule.addItem('Every 30 mins')
        self.downloadSchedule.addItem('Every 10 mins')
        self.downloadSchedule.addItem('Every 5 mins')
        self.downloadSchedule.addItem('Every minute')
        self.downloadSchedule.addItem('Every 30 seconds')
        self.downloadSchedule.addItem('Every 10 seconds')
        self.downloadSchedule.currentTextChanged.connect(self.selectDownloadSchedule)
        self.downloadButtonsLayout.addWidget(self.downloadSchedule)

        # 
        self.downloadButton = QPushButton("Start")
        self.downloadButton.setCheckable(True)
        self.downloadButton.clicked.connect(self.handleDownloadButton)
        self.downloadButtonsLayout.addWidget(self.downloadButton)

        self.layout.addLayout(self.downloadButtonsLayout)
       

        self.footerBox = QHBoxLayout()

        self.check_box = QCheckBox('Run in background when closed')
        self.footerBox.addWidget(self.check_box)

        self.footerBox.addWidget(self.statusMessage)

        self.layout.addLayout(self.footerBox)

        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            self.style().standardIcon(QStyle.SP_DesktopIcon))

        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        swap_action = QAction("Change Paper", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        swap_action.triggered.connect(self.swapPaperNow)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(swap_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.activated.connect(self.onTrayActivated)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
 
    def onTrayActivated(self, reason):
        # print("tray activated", reason)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # print("tray activated", reason)
            self.show()

    @Slot()
    def selectDownloadGroup(self, value):
        self.download_group = value
        if value == 'Liked by' or value == 'Created by':
            self.userName.setEnabled(True)
        else:
            self.userName.setEnabled(False)

    @Slot()
    def selectDownloadSchedule(self, value):
        self.download_schedule = value

    @Slot()
    def usernameChanged(self, value):
        self.user_name = value

    @Slot()
    def swapPaperNow(self):
        # print("Swap paper now")
        self.swapThread()

    @Slot()
    def handleDownloadButton(self):
        if self.running:
            self.stopDownload()
        else:
            self.startDownload()

    @Slot()
    def startDownload(self):
        # print("Start button clicked")
        self.running = True
        self.current_event = Event()

        self.swapScheduledThread()
        
        self.downloadButton.setText('Stop')
        self.downloadGroup.setEnabled(False)
        self.userName.setEnabled(False)
        self.downloadSchedule.setEnabled(False)

    @Slot()
    def stopDownload(self):
        # print("Stop button clicked")
        self.current_event.set()
        self.running = False

        self.downloadButton.setText('Start')
        self.downloadGroup.setEnabled(True)
        if self.download_group == 'Liked by' or self.download_group == 'Created by':
            self.userName.setEnabled(True)
        self.downloadSchedule.setEnabled(True)

    @Slot()
    def fetchThread(self):
        worker = Worker(fetchPaper, self.download_group, self.user_name) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)


    @Slot()
    def swapScheduledThread(self):
        worker = Worker(scheduledPaperSwap, self.download_schedule, self.download_group, self.user_name, self.current_event) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    @Slot()
    def swapThread(self):
        worker = Worker(swapPaper, self.download_group, self.user_name) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    # Override closeEvent, to intercept the window closing event
    # The window will be closed only if there is no check mark in the check box
    def closeEvent(self, event):
        if self.check_box.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "FlyTrap for FlyPaper",
                "Application was minimized to Tray",
                QSystemTrayIcon.Information,
                2000
            )

    def progress_fn(self, prog):
        # print("progress status", prog['status'])
        if 'fetch' in prog and prog['fetch']:
            # print("FETCH AGAIN")
            self.fetchThread()

        if 'status' in prog:
            self.statusMessage.setText(prog['status'])

        if 'papers' in prog:
            if len(prog['papers']) >= 1:
                self.randomButton.setEnabled(True)
            else:
                self.randomButton.setEnabled(False)


    def print_output(self, s):
        # print("THREAD OUTPUT", s)
        if s and 'swap' in s and s['swap']:
            # print("YES. SWAP AGAIN")
            self.swapScheduledThread()

    def thread_complete(self):
        print("THREAD COMPLETE!")