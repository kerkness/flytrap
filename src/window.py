# import os
# import sys
# import ctypes
# import time
# from tempfile import TemporaryDirectory
# import tempfile
# import random
# import signal
# import requests
from threading import Thread, Event
from PySide6.QtCore import Slot, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QComboBox, QFileDialog, QSystemTrayIcon, QStyle, QCheckBox, QWidget, QPushButton, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout
from papers import threadedFetch, threadedSwap, swapPaper

class MainWindow(QMainWindow):

    check_box = None
    tray_icon = None

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("FlyTrap for FlyPaper")

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

        self.showDownloadOptions()

        threadedFetch(self.download_group, self.user_name)
        # self.downloader = PaperChanger()
        # self.paperChanger = Thread(target = papers.loadPaper, args = ())
        # self.paperChanger.setDaemon(True)
        # self.paperChanger.start()

    # @Slot()
    # def fetchPapers(self):
    #     fetchThread = Thread(target = fetchPaper, args = ())
    #     fetchThread.setDaemon(True)
    #     fetchThread.start()

    @Slot()
    def showDownloadOptions(self):

        self.showingOptions = True
        self.instructions = QLabel()
        self.instructions.setText('FlyPaper filters:')

        self.optionsGroup = QHBoxLayout()

        self.downloadGroup = QComboBox()
        self.downloadGroup.addItem('All Paper')
        self.downloadGroup.addItem('Featured')
        self.downloadGroup.addItem('Liked by')
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
       
        self.statusMessage = QLabel()
        self.statusMessage.setText('')
        self.layout.addWidget(self.statusMessage)

        self.check_box = QCheckBox('Run in background when closed')
        self.layout.addWidget(self.check_box)

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
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
 
    @Slot()
    def selectDownloadGroup(self, value):
        self.download_group = value
        if value == 'Liked by':
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
        print("Swap paper now")
        swapPaper(self.download_group, self.user_name)

    @Slot()
    def handleDownloadButton(self):
        if self.running:
            self.stopDownload()
        else:
            self.startDownload()

    @Slot()
    def startDownload(self):
        print("Start button clicked")
        # self.downloading = True
        self.running = True
        self.current_event = Event()
        threadedSwap(self.download_schedule, self.download_group, self.user_name, self.current_event)
        # startThread = Thread(target = scheduledPaperSwap, args = ())
        # startThread.setDaemon(True)
        # startThread.start()
        # self.paperChanger.onThread(papers.schedulePaperSwap())
        # papers.running = True
        # papers.schedulePaperSwap()
        
        self.downloadButton.setText('Stop')
        self.downloadGroup.setEnabled(False)
        self.userName.setEnabled(False)
        self.downloadSchedule.setEnabled(False)

    @Slot()
    def stopDownload(self):
        print("Stop button clicked")
        self.current_event.set()
        self.running = False

        self.downloadButton.setText('Start')
        self.downloadGroup.setEnabled(True)
        if self.download_group == 'Liked by':
            self.userName.setEnabled(True)
        self.downloadSchedule.setEnabled(True)

    # @Slot()
    # def minimizeToTray(self):
    #     print("Minimize to Tray")

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
