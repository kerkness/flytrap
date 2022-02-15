import os
import ctypes
import time
import tempfile
import requests
from threading import Thread, Event
from screeninfo import get_monitors

displays = get_monitors()
primary_display = False

for m in displays:
    if primary_display == False or m.width > primary_display.width:
        primary_display = m
    # if(m.is_primary):
    #     primary_display = m

print(displays)
print(primary_display)

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
    if len(papers) > 1:
        return

    # statusMessage.setText('Searching for FlyPaper')
    query = {'limit': 1, 'search': ''}

    if group == 'Featured':
        query['search'] = 'featured'

    if group == 'Liked by':
        query['search'] = 'liked:' + username

    if group == 'Created by':
        query['search'] = username

    response = requests.get('https://flypaper.theflyingfabio.com/api/paper/random', params=query)
    data = response.json()

    # if len(data) == 0:
        # statusMessage.setText('No FlyPaper Found')

    for paper in data:
        if paper['id']:
            savePaper(paper['id'], paper['filename'], group, username)


def savePaper(id, filename, group, username):
    # statusMessage.setText('Downloading FlyPaper')

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
    # statusMessage.setText('')

    # if len(papers) < 1:
    #     fetchPaper(group, username, statusMessage)

def threadedFetch(group, username):
    fetchThread = Thread(target = fetchPaper, args = (group, username))
    fetchThread.setDaemon(True)
    fetchThread.start()

def swapPaper(group, username):
    # statusMessage.setText('Swapping')
    print("swap the papers from ", papers)
    if (len(papers) >= 1):
        filename = papers.pop()
        path = os.path.join(flypaperdir, filename)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path , 0)
        currentPaper = filename
    # statusMessage.setText('')
    if len(papers) < 1:
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

    print("tick")
    swapPaper(group, username)

    print("sleeping for ", seconds)
    # statusMessage.setText('')
    time.sleep(seconds - ((time.time() - start_time) % seconds))
    print("awake", exit_event.is_set())

    if not exit_event.is_set():
        # threadedSwap(schedule, group, username, exit_event)
        return { "swap": True }


def threadedSwap(schedule, group, username, exit_event):
    fetchThread = Thread(target = scheduledPaperSwap, args = (schedule, group, username, exit_event))
    fetchThread.setDaemon(True)
    fetchThread.start()

