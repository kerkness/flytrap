import os
import sys
import ctypes
import time
from tempfile import TemporaryDirectory
import tempfile
import random
import signal
import requests
from threading import Thread, Event
from PySide6.QtCore import Slot, QSize, Qt, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices, QAction
from PySide6.QtWidgets import QApplication, QMenu, QComboBox, QFileDialog, QSystemTrayIcon, QStyle, QCheckBox, QWidget, QProgressBar, QPushButton, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout
import tkinter

root = tkinter.Tk()
root.withdraw()
WIDTH, HEIGHT = root.winfo_screenwidth(), root.winfo_screenheight()

exit_event = Event()

class PaperChanger:
    def __init__(self):

        self.group = 'Recent'
        self.schedule = 'Once a day'
        self.username = 'kerkness'
        self.currentPaper = ''
        self.running = False
        
        self.tempdir = tempfile.gettempdir()

        alldir = list(filter(os.path.isdir, os.listdir(self.tempdir)))

        self.flypaperdir = ''

        for d in alldir:
            dirname = os.path.dirname(d)
            if dirname.startswith('flypaper'):
                self.flypaperdir = d

        if len(self.flypaperdir) == 0:
            self.flypaperdir = tempfile.mkdtemp(prefix='flypaper')

    def start(self, group, schedule, user):
        self.group = group
        self.schedule = schedule
        self.username = user
        if exit_event.is_set():
            self.running = False
            exit_event.clear()
        self.fetchPaper()


    def stop(self):
        self.running = False



    def fetchPaper(self):
        query = {'limit': 1, 'search': ''}

        if self.group == 'Featured':
            query['search'] = 'featured'

        if self.group == 'Liked by':
            query['search'] = 'liked:' + self.username

        response = requests.get('https://flypaper.theflyingfabio.com/api/paper/random', params=query)
        data = response.json()

        paper = data[0]

        if paper['id']:
            self.savePaper(paper['id'], paper['filename'])

    def savePaper(self, id, filename):
        url = "https://flypaper.theflyingfabio.com/render/" + str(id) 

        query = { 'w': WIDTH }
        response = requests.get(url, stream=True, params=query)

        block_size = 1024 #1 Kibibyte
        file_path = os.path.join(self.flypaperdir, filename)
        with open(file_path, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)

        self.swapPaper(filename)


    def swapPaper(self, filename):
        path = os.path.join(self.flypaperdir, filename)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path , 0)
        self.currentPaper = filename

        if not self.running:
            self.running = True
            self.schedulePaperSwap()

    def getScheduleInSeconds(self):
        seconds = {
            'Every 2 hours': 60 * 120, 
            'Every hour': 60 * 60, 
            'Every 30 mins': 60 * 30, 
            'Every 10 mins': 60 * 10, 
            'Every 5 mins': 60 * 5, 
            'Every minute': 60,
            'Every 30 seconds': 30,
            'Every 10 seconds': 10,
            }
        return seconds.get(self.schedule, 60)

    def schedulePaperSwap(self):
        start_time = time.time()
        seconds = self.getScheduleInSeconds()

        while self.running:
            current_time = time.time()
            elapsed_time = current_time - start_time

            if elapsed_time > seconds:
                print("Finished iterating in: " + str(int(elapsed_time))  + " seconds")
                start_time = time.time()
                self.fetchPaper()

            if exit_event.is_set():
                break
                # break

class MainWindow(QMainWindow):

    check_box = None
    tray_icon = None

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("FlyTrap for FlyPaper")

        self.downloader = PaperChanger()

        # Download Directory
        self.download_group = 'Recent'
        self.download_schedule = 'Every hour'
        self.user_name = ''
        self.downloading = False
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

        self.check_box = QCheckBox('Minimize to Tray')
        self.layout.addWidget(self.check_box)

        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            self.style().standardIcon(QStyle.SP_ComputerIcon))

        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
 
    @Slot()
    def selectDownloadGroup(self, value):
        print(value)
        self.download_group = value
        if value == 'Liked by':
            self.userName.setEnabled(True)
        else:
            self.userName.setEnabled(False)

    @Slot()
    def selectDownloadSchedule(self, value):
        self.download_schedule = value
        print(value)

    @Slot()
    def usernameChanged(self, value):
        self.user_name = value
        print(value)

    @Slot()
    def handleDownloadButton(self):
        if self.downloading:
            self.stopDownload()
        else:
            self.startDownload()

    @Slot()
    def startDownload(self):
        print("Start download")
        self.downloading = True
        self.paperChanger = Thread(target = self.downloader.start, args = (self.download_group,  self.download_schedule, self.user_name))
        self.paperChanger.setDaemon(True)

        self.paperChanger.start()
        self.downloadButton.setText('Stop')
        self.downloadGroup.setEnabled(False)
        self.userName.setEnabled(False)
        self.downloadSchedule.setEnabled(False)

    @Slot()
    def stopDownload(self):
        print("Stop download")
        exit_event.set()
        self.downloading = False
        self.downloader.stop()
        self.downloadButton.setText('Start')
        self.downloadGroup.setEnabled(True)
        if self.download_group == 'Liked by':
            self.userName.setEnabled(True)
        self.downloadSchedule.setEnabled(True)

    @Slot()
    def minimizeToTray(self):
        print("Minimize to Tray")

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

app = QApplication(sys.argv)

window = MainWindow()
window.show()

if __name__ == "__main__":
    app.exec()