try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import re
import wikipedia
import random
import json
import math
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import csv


def getRevisions(pageTitle):
    pageTitle = pageTitle.replace(" ", "_")
    url = "https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=revisions&rvlimit=500&titles=" + pageTitle
    revisions = []                                  #list of all accumulated revisions
    next = ''                                             #information for the next request

    while True:
        try :
            response = urllib2.urlopen(url + next).read()     #web request
            revisions+=(re.findall('<rev [^>]*>', response.decode("utf-8")))  #adds all revisions from the current request to the list
            cont = re.search('<continue rvcontinue="([^"]+)"', response.decode("utf-8"))
            if not cont:                                      #break the loop if 'continue' element missing
                break
            next = "&rvcontinue=" + cont.group(1)             #gets the revision Id from which to start the next request
        except :
            return 0 

    userandtime = getUsersandTime(revisions)
    neteditscore, velocityscore = getEditScores(userandtime)
    changes = []
    changes = getChanges(userandtime)
    similarites = getSimilarities(changes)
    return neteditscore, velocityscore, similarites


def getEditScores(userandtime):
    neteditscore = 0
    velocityscore = 0 
    delta_hours = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=6, weeks=0)
    delta_day = timedelta(days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
    delta_week = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=1)
    delta_month = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=4)
    delta_halfyear = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=26)
    delta_year = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=52)

    now = datetime.now(tz=None)
    for line in userandtime:
        if line[2] > (now - delta_hours):
            velocityscore += 2
        elif line[2] > (now - delta_day):
            velocityscore += 1.5
        elif line[2] > (now - delta_week):
            velocityscore += 1.2
        elif line[2] > (now - delta_month):
            velocityscore += .2
        elif line[2] > (now - delta_halfyear):
            velocityscore += .15
        elif line[2] > (now - delta_year):  #LOOK AT EDITS IN WINDOWS SO THAT YOU FIND PAST WINDOWS
            velocityscore += .1   #could be assigned to past thing
        else :
            velocityscore += .01

        if line[4] == 1:
            editscore = .5 #if the edit is done by a bot
        else:
            editscore = line[3]

        if editscore > 1:
            editscore = math.sqrt(editscore) #if the edit is done by a normal person

        neteditscore = neteditscore + editscore
    return neteditscore, velocityscore


def getUsersandTime(revisions):
    i = 0
    userandtime = []
    usercount = {}

    for line in revisions:
        p = line.find('user="')
        p = p + 6
        p1 = line.find('"',p)
        username = line[p:p1]
        t = line.find('timestamp=')
        t = t + 11
        t1 = line.find('Z',t)
        time = line[t:t1]
        time = datetime.fromisoformat(time)
        revise = line.find('revid="')
        revise = revise + 7
        revise1 = line.find('"',revise)
        revid = line[revise:revise1]
        i = 0
        if re.findall('bot',username):
            i = 1
        if username in usercount:
            usercount[username] = usercount[username]+1
        else:
            usercount[username] = 1
        userandtime.append([revid,username,time,usercount[username],i])
    return userandtime


def getChanges(userandtime):
    changesarr = []
    for i in range(100):
        oldrevid = userandtime[i][0]
        newrevid = userandtime[i+1][0]
        oldrevid1 = str(oldrevid)
        newrevid1 = str(newrevid)
        url = 'https://en.wikipedia.org/w/api.php?action=compare&format=json&fromrev=' + oldrevid1 +'&torev=' + newrevid1
        openwebsite = urllib2.urlopen(url)
        html = openwebsite.read()
        insertion = parsehtml(html)
        changes = []
        changes.append(oldrevid)
        changes.append(newrevid)
        changes.append(insertion)
        changesarr.append(changes)
    return changesarr


def getSimilarities(wordarr):
    count = 0 
    similarties = 0
    while count < (len(wordarr)-3):
        for x in wordarr[count+3]:
            for i in range(3):
                for y in wordarr[count+i]:
                    if x == y:
                        similarties += 1
        count += 1
    return similarties


def parsehtml(revision_json) :
    jsonObject = json.loads(revision_json)
    html = jsonObject["compare"]["*"]
    soup_dump = BeautifulSoup(html, 'html.parser')
    changes = soup_dump.find_all('ins', {'class': 'diffchange'})
    out = []
    
    for i in changes:
        i = re.sub('<.*?>', '', str(i))
        i = re.sub(r'([^\s\w]|_)+', '', i)
        i = i.strip()
        if (i.isspace()) or (len(i) == 0) or (i == None) or (i == ""):
            continue
        else:
            out.append(i)
    return out


def getKeyWordScore(wiki_title, keywords):
    summary = re.sub(r'[^\w\s]', '', wikipedia.summary(wiki_title)).lower().split()
    score = 0
    for k in keywords:
        if k in summary:
            score += summary.count(k) #use better search algo
    return score 


def getLinks(wiki_page):
    return wiki_page.links


depth_limit = 1
keywords = ["bad", "china", "good", "quality", "country", "asia", "war", "asian", "east", "power", "democracy", "republic"]
results = []


def runalgo(wiki_title, depth_limit):
    if depth_limit <= 0:
        return 

    wiki_page = wikipedia.page(wiki_title, None, True, True, False)
    rev, vscore, similarities = getRevisions(wiki_title)
    kw_score = getKeyWordScore(wiki_title,keywords)
    
    results.append([wiki_title, vscore, kw_score, similarities])
    links= getLinks(wiki_page)

    i = 0 
    while i < 2: 
        runalgo(links[random.randint(0, len(links)-1)], depth_limit-1)
        i += 1
    return results


resultList = []
with open('dataset.txt') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        resultList.append(row)

print(resultList)

for item in resultList:
    try:
        results = runalgo(item[0], depth_limit)
        results.append(item[1])
    except:
        print(item[0] + "failed")
    print(results)

def parseResults(results):
    output = ''
    for page in range(0,len(results),2):
        for item in results[page]:
            output += str(item) + ', '
        output += results[page+1]
        output +='\n'
    return output

with open('dataset2.txt', mode = 'w') as dataset_file:
    dataset_writer = csv.writer(dataset_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    dataset_writer.writerow([parseResults(results)])