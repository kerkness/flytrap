import os
import ctypes
import time
import json
import tempfile
import requests
from threading import Thread, Event
from screeninfo import get_monitors
from flytrap import *


# version = 'v0.1.6'
# activeParams = { "group": "", "": "username" }
# displayed = []
# paper_count = 0

# displays = get_monitors()
# primary_display = False

# for m in displays:
#     if primary_display == False or m.width > primary_display.width:
#         primary_display = m

# tempdir = tempfile.gettempdir()
# alldir = list(filter(os.path.isdir, os.listdir(tempdir)))

# flypaperdir = ''

# for d in alldir:
#     dirname = os.path.dirname(d)
#     if dirname.startswith('flypaper'):
#         flypaperdir = d

# if len(flypaperdir) == 0:
#     flypaperdir = tempfile.mkdtemp(prefix='flypaper')

# papers = []
# for (dirpath, dirnames, filenames) in os.walk(flypaperdir):
#     papers.extend(filenames)
#     break

def logPaper(paperId):
    print("Log Paper ID", paperId)
    displayed.append(paperId)

def logParams(group, username):

    if group != activeParams['group'] or username != activeParams['username']:
        print("Clearing displayed")
        displayed.clear()

    activeParams['group'] = group
    activeParams['username'] = username


def fetchPaper(group, username, progress_callback):
    # print("fetch paper")
    if len(papers) > 1:
        # print("Already has paper in queue")
        return

    logParams(group, username)

    # If we have almost viewed all matching papers, clear
    if len(displayed) >= activeParams['count']:
        displayed.clear()

    # statusMessage.setText('Searching for FlyPaper')
    progress_callback.emit({ "papers": papers, "status": "Searching for FlyPaper" })
    query = {'limit': 1, 'search': '', 'skip': json.dumps(displayed) }

    if group == 'Featured':
        query['search'] = 'featured'

    if group == 'Liked by':
        query['search'] = 'liked:' + username

    if group == 'Created by':
        query['search'] = username

    response = requests.get('https://flypaper.theflyingfabio.com/api/paper/random', params=query)
    data = response.json()

    if data['count'] == 0:
        progress_callback.emit({ "papers": papers, "status": "No Flypaper Found" })    

    activeParams['count'] = data['count']

    # print("Paper Count", activeParams['count'])

    for paper in data['papers']:
        if paper['id']:
            savePaper(paper, group, username, progress_callback)

    return { "fetched": True }

def savePaper(paper, group, username, progress_callback):
    # statusMessage.setText('Downloading FlyPaper')
    progress_callback.emit({ "papers": papers, "status": "Downloading FlyPaper" })

    id = paper['id']
    filename = paper['filename']

    url = "https://flypaper.theflyingfabio.com/render/" + str(id) 

    query = { 'w': primary_display.width }
    response = requests.get(url, stream=True, params=query, verify=False)

    block_size = 1024 #1 Kibibyte
    file_path = os.path.join(flypaperdir, filename)
    with open(file_path, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)

    # insert at the start of the array
    # print("save the paper")
    papers.append(paper)
    progress_callback.emit({ "papers": papers, "status": "" })
    # statusMessage.setText('')

    # if len(papers) < 1:
    #     fetchPaper(group, username, statusMessage)

# def threadedFetch(group, username):
#     fetchThread = Thread(target = fetchPaper, args = (group, username))
#     fetchThread.setDaemon(True)
#     fetchThread.start()

def swapPaper(group, username, progress_callback):
    # statusMessage.setText('Swapping')
    progress_callback.emit({ "papers": papers, "status": "Swapping" })

    # print("swap the papers from ", papers)
    if (len(papers) >= 1):
        paper = papers.pop()
        logPaper(paper['id'])
        path = os.path.join(flypaperdir, paper['filename'])
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path , 0)
        currentPaper = paper
    # statusMessage.setText('')
    progress_callback.emit({ "papers": papers, "status": "", "fetch": True })
    if len(papers) < 1:
        return { "fetch": True }

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

def scheduledPaperSwap(schedule, group, username, exit_event, progress_callback):

    start_time = time.time()
    seconds = getScheduleInSeconds(schedule)
    # print("start scheduler")

    # print("tick")
    swapPaper(group, username, progress_callback)

    # print("sleeping for ", seconds)
    # statusMessage.setText('')
    progress_callback.emit({ "papers": papers, "status": "" })
    time.sleep(seconds - ((time.time() - start_time) % seconds))
    # print("awake", exit_event.is_set())

    if not exit_event.is_set():
        # threadedSwap(schedule, group, username, exit_event)
        return { "swap": True }


# def threadedSwap(schedule, group, username, exit_event):
#     fetchThread = Thread(target = scheduledPaperSwap, args = (schedule, group, username, exit_event))
#     fetchThread.setDaemon(True)
#     fetchThread.start()

