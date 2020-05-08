import wikipedia
import json
import math
from bs4 import BeautifulSoup, NavigableString
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import re
from datetime import datetime, timedelta
import pprint



reversions= {}

# def between(cur, end):
#     print(cur, end)
#     while cur and cur != end:
#         if isinstance(cur, NavigableString):
#             text = cur.strip()
#             if len(text):
#                 yield text
#         cur = cur.next_element

def getUsersandTime(revisions) :
    i = 0
    userandtime = []
    usercount = {}
    revertedids=[]
    print("revisions", len(revisions))
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
        parent = line.find('parentid="')
        parent = parent + 10
        parent1 = line.find('"',parent)
        parid = line[parent:parent1]
        comment = line.find('comment="')
        comment = comment + 9
        comment1 = line.find('"',comment)
        comment = line[comment:comment1]
        i = 0
        if re.findall('bot',username):
            i = 1
        if username in usercount:
            usercount[username] = usercount[username]+1
        else:
            usercount[username] = 1
        revscore= 0
        if ("reverted" in comment) or ("Undid" in comment) or ("undid" in comment) or ("Reverted" in comment) :
            revertedids.append([revid,parid])
            # print(revid,parid)
            revscore =1
        userandtime.append([revid,username,time,usercount[username],i, comment, revscore])
    # print("userntime", len(userandtime))
    # print("reverted ids", revertedids)
    return revertedids

def getRevisions(pageTitle):

    pageTitle = pageTitle.replace(" ", "_")
    url = "https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=revisions&rvlimit=500&titles=" + pageTitle

    revisions = []                                  #list of all accumulated revisions
    
    next = ''                                             #information for the next request
    while True:
        #print(pageTitle)
        try :
            response = urllib2.urlopen(url + next).read()     #web request
            revisions+=(re.findall('<rev [^>]*>', response.decode("utf-8")))  #adds all revisions from the current request to the list
            cont = re.search('<continue rvcontinue="([^"]+)"', response.decode("utf-8"))
            if not cont:                                      #break the loop if 'continue' element missing
                break
            next = "&rvcontinue=" + cont.group(1)             #gets the revision Id from which to start the next request
        except :
            return 0 
    print(len(revisions))
    reversions = getUsersandTime(revisions)
    getchanges(reversions)
    
def getchanges(reversions) :
    changesarr = []
    d = {}
    for x in reversions:
        oldrevid = x[0]
        newrevid = x[1]

        url = 'https://en.wikipedia.org/w/api.php?action=compare&format=json&fromrev=' + oldrevid +'&torev=' + newrevid
        try:
            openwebsite = urllib2.urlopen(url)
        except:
            pass
        html = openwebsite.read()
        # print(html)
        try :
            insertion, lineno = parsehtml(html)
            if lineno[0] not in d :
                d[lineno[0]]= [(oldrevid,newrevid,insertion)]
            else :
                d[lineno[0]].append((oldrevid,newrevid,insertion))
        except :
            print("didn'twork")

    # print(d)
    tracked_reversions = {}
    for x in d.keys() :
        soup_dump = BeautifulSoup(x, 'html.parser')
        lineno = soup_dump.find_all('td', {'class': 'diff-lineno'})
        tracked_reversions[lineno]=d[x]
        print("len",len(d[x]) ,"line no:", lineno, "changes", d[x])
        # print(len(insertion), len(lineno))

def parsehtml(revision_json) :
    jsonObject = json.loads(revision_json)
    # print("jsonobj", jsonObject)
    html = jsonObject['compare']['*']
    soup_dump = BeautifulSoup(html, 'html.parser')
    lineno = soup_dump.find_all('td', {'class': 'diff-lineno'})
    changes =soup_dump.find_all('td', {'class': 'diff-addedline'})
    
    html = u""
    c= 0
    
    x= []
    x= soup_dump.prettify().split('diff-lineno')

    c =1
    while c < len(x) :
        soup = BeautifulSoup(x[c], "html.parser")
        changes =soup.find_all('td', {'class': 'diff-addedline'})
        for i in changes:
            i = re.sub('<.*?>', '', str(i))
            i = re.sub(r'([^\s\w]|_)+', '', i)
            i = i.strip()
            if lineno[c-1].get_text() in reversions:
                reversions[lineno[c-1].get_text()].append(i)
            else : 
                reversions[lineno[c-1].get_text()]= [i]
        c+=1
    # print(len(reversions), reversions)

    out = []
    
    for i in changes:
        i = re.sub('<.*?>', '', str(i))
        i = re.sub(r'([^\s\w]|_)+', '', i)
        i = i.replace('\n','')
        i = i.strip()
        if (i.isspace()) or (len(i) == 0) or (i == None) or (i == ""):
            continue
        else:
            # out.append(i.split())
            out.append(i)
    # print(out,lineno)
    return out, lineno


# wiki_page = wikipedia.page("Coronavirus", None, True, True, False)
getRevisions("Coronavirus disease 2019")
# oldrevid1 = str(944714569)
# newrevid1 = str(944715017)


# url = 'https://en.wikipedia.org/w/api.php?action=compare&format=json&fromrev=' + oldrevid1 +'&torev=' + newrevid1
# openwebsite = urllib2.urlopen(url)
# html = openwebsite.read()
# insertion, lineno = parsehtml(html)
# print(insertion, lineno)

