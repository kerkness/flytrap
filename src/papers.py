import os
# import sys
import ctypes
import time
# from tempfile import TemporaryDirectory
import tempfile
# import random
# import signal
import requests
from threading import Thread, Event
from screeninfo import get_monitors

# from threading import Thread, Event
# from flytrap import exit_event, primary_display
# from appdata import AppDataPaths
# app_paths = AppDataPaths()

# exit_event = Event()
# start_event = Event()


displays = get_monitors()
primary_display = False

for m in displays:
    if(m.is_primary):
        primary_display = m

# group = 'Recent'
# schedule = 'Every minute'
# username = 'kerkness'
# currentPaper = ''

# Set up the 
tempdir = tempfile.gettempdir()

alldir = list(filter(os.path.isdir, os.listdir(tempdir)))

flypaperdir = ''

for d in alldir:
    dirname = os.path.dirname(d)
    if dirname.startswith('flypaper'):
        flypaperdir = d

if len(flypaperdir) == 0:
    flypaperdir = tempfile.mkdtemp(prefix='flypaper')

papers = []
for (dirpath, dirnames, filenames) in os.walk(flypaperdir):
    papers.extend(filenames)
    break


def fetchPaper(group, username):
    print("fetch paper")
    query = {'limit': 1, 'search': ''}

    if group == 'Featured':
        query['search'] = 'featured'

    if group == 'Liked by':
        query['search'] = 'liked:' + username

    response = requests.get('https://flypaper.theflyingfabio.com/api/paper/random', params=query)
    data = response.json()

    paper = data[0]

    if paper['id']:
        savePaper(paper['id'], paper['filename'], group, username)


def savePaper(id, filename, group, username):
    url = "https://flypaper.theflyingfabio.com/render/" + str(id) 

    query = { 'w': primary_display.width }
    response = requests.get(url, stream=True, params=query)

    block_size = 1024 #1 Kibibyte
    file_path = os.path.join(flypaperdir, filename)
    with open(file_path, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)

    # insert at the start of the array
    print("save the paper")
    papers.insert(0, filename)

    if len(papers) < 2:
        fetchPaper(group, username)

def threadedFetch(group, username):
    fetchThread = Thread(target = fetchPaper, args = (group, username))
    fetchThread.setDaemon(True)
    fetchThread.start()

def swapPaper(group, username):
    print("swap the papers from ", papers)
    filename = papers.pop()
    path = os.path.join(flypaperdir, filename)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path , 0)
    currentPaper = filename
    threadedFetch(group, username)

def getScheduleInSeconds(schedule):
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
    return seconds.get(schedule, 60)

def scheduledPaperSwap(schedule, group, username, exit_event):

    start_time = time.time()
    seconds = getScheduleInSeconds(schedule)
    print("start scheduler")

    # if exit_event.is_set():
    #     break

    print("tick")
    swapPaper(group, username)

    print("sleeping for ", seconds)
    time.sleep(seconds - ((time.time() - start_time) % seconds))
    print("awake", exit_event.is_set())

    if not exit_event.is_set():
        print("Start a new thread")
        threadedSwap(schedule, group, username, exit_event)


def threadedSwap(schedule, group, username, exit_event):
    fetchThread = Thread(target = scheduledPaperSwap, args = (schedule, group, username, exit_event))
    fetchThread.setDaemon(True)
    fetchThread.start()


# class PaperChanger():
#     def __init__(self, primary_display, exit_event, start_event):

#         # self.flypaperdir = app_paths.app_data_path #cross platform folder path

#         # print("Save paper to", self.flypaperdir)
#         # gather existing files

#         self.exit_event = exit_event
#         self.start_event = start_event
#         self.primary_display = primary_display
        
#         self.group = 'Recent'
#         self.schedule = 'Once a day'
#         self.username = 'kerkness'
#         self.currentPaper = ''
#         self.running = False
        
#         self.tempdir = tempfile.gettempdir()

#         alldir = list(filter(os.path.isdir, os.listdir(self.tempdir)))

#         self.flypaperdir = ''

#         for d in alldir:
#             dirname = os.path.dirname(d)
#             if dirname.startswith('flypaper'):
#                 self.flypaperdir = d

#         if len(self.flypaperdir) == 0:
#             self.flypaperdir = tempfile.mkdtemp(prefix='flypaper')

#         self.papers = []
#         for (dirpath, dirnames, filenames) in os.walk(self.flypaperdir):
#             self.papers.extend(filenames)
#             break

#     def loadPaper(self):
#         print("existing papers", self.papers)
#         self.fetchPaper()


#     def start(self):
#         print("start the paper")
#         self.group = group
#         self.schedule = schedule
#         self.username = user

#         self.fetchPaper()
#         # if self.exit_event.is_set():
#         #     self.running = False
#         #     self.exit_event.clear()

#         # self.fetchPaper()
#         if not self.running:
#             self.running = True
#             self.schedulePaperSwap()



#     def stop(self):
#         print("stop the paper")
#         self.running = False
#         if self.exit_event.is_set():
#             self.running = False
#             self.exit_event.clear()



#     def fetchPaper(self):
#         print("fetch the paper")
#         query = {'limit': 1, 'search': ''}

#         if self.group == 'Featured':
#             query['search'] = 'featured'

#         if self.group == 'Liked by':
#             query['search'] = 'liked:' + self.username

#         response = requests.get('https://flypaper.theflyingfabio.com/api/paper/random', params=query)
#         data = response.json()

#         paper = data[0]

#         if paper['id']:
#             self.savePaper(paper['id'], paper['filename'])

#     def savePaper(self, id, filename):
#         url = "https://flypaper.theflyingfabio.com/render/" + str(id) 

#         query = { 'w': self.primary_display.width }
#         response = requests.get(url, stream=True, params=query)

#         block_size = 1024 #1 Kibibyte
#         file_path = os.path.join(self.flypaperdir, filename)
#         with open(file_path, 'wb') as file:
#             for data in response.iter_content(block_size):
#                 file.write(data)

#         # insert at the start of the array
#         print("save the paper")
#         self.papers.insert(0, filename)

#         if len(self.papers) < 2:
#             self.fetchPaper()
#         # self.swapPaper(filename)


#     def swapPaper(self):
#         print("swap the papers from ", self.papers)
#         filename = self.papers.pop()
#         path = os.path.join(self.flypaperdir, filename)
#         ctypes.windll.user32.SystemParametersInfoW(20, 0, path , 0)
#         self.currentPaper = filename
#         self.fetchPaper()
#         # if not self.running:
#         #     self.running = True
#         #     self.schedulePaperSwap()

#     def getScheduleInSeconds(self):
#         seconds = {
#             'Every 2 hours': 60 * 120, 
#             'Every hour': 60 * 60, 
#             'Every 30 mins': 60 * 30, 
#             'Every 10 mins': 60 * 10, 
#             'Every 5 mins': 60 * 5, 
#             'Every minute': 60,
#             'Every 30 seconds': 30,
#             'Every 10 seconds': 10,
#             }
#         return seconds.get(self.schedule, 60)

#     def schedulePaperSwap(self):

#         start_time = time.time()
#         seconds = self.getScheduleInSeconds()
#         print("start scheduler")

#         while self.running:
#             if self.exit_event.is_set():
#                 break

#             print("tick")
#             self.swapPaper()

#             time.sleep(seconds - ((time.time() - start_time) % seconds))
