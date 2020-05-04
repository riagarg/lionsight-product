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


import os
  # accessible as a variable in index.html:
from flask import *
from flask_table import Table, Col

#tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templatesh4d')
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templatesh4d')
app = Flask(__name__, template_folder=tmpl_dir)

class ItemTable(Table):
    wiki_title = Col("Wikipedia Page")
    vscore = Col("Velocity Score")
    kw_score = Col("Keyword Score")
    similarities = Col("Similarities")

class Item(object):
    def __init__(self, wiki_title, vscore, kw_score, similarities):
        self.wiki_title = wiki_title
        self.vscore = vscore
        self.kw_score = kw_score
        self.similarities = similarities

@app.route('/')
def index():
    print(request.args)

    return (render_template("index.html"))

@app.route('/index')
def index1():
    return render_template("index.html")



@app.route('/searchpage', methods = ['POST'])
def searchPage():
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
        userandtime,leng = getUsersandTime(revisions)
        neteditscore, velocityscore = getEditScores(userandtime)
        #i = 0 
        changes = []
        changes = getchanges(userandtime,leng)
        similarites = getsimilarities(changes)

        return neteditscore, velocityscore, similarites


    def getEditScores (userandtime) :
        neteditscore = 0
        velocityscore = 0 
        delta_hours = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=6,  weeks=0)
        delta_day = timedelta( days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=0)
        delta_week = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=1)
        delta_month = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=4)
        delta_halfyear = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=26)
        delta_year = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=52)

        now = datetime.now(tz=None)
        for line in userandtime:
            if line[2] > (now- delta_hours) :
                velocityscore += 2
            elif line[2] > (now- delta_day ) :
                velocityscore += 1.5
            elif line[2] > (now- delta_week ) :
                velocityscore += 1.2
            elif line[2] > (now- delta_month ) :
                velocityscore += .2
            elif line[2] > (now- delta_halfyear ) :
                velocityscore += .2
            elif line[2] > (now- delta_year ) :  #LOOK AT EDITS IN WINDOWS SO THAT YOU FIND PAST WINDOWS
                velocityscore += .1   #could be assigned to past thing
            else :
                velocityscore += .01

            if line[4] == 1:
                editscore = .5 #if the edit is done by a bot
            else:
                editscore = line[3]
            if editscore>1:
                editscore = math.sqrt(editscore) #if the edit is done by a normal person

            neteditscore = neteditscore + editscore
        return neteditscore, velocityscore

    def getUsersandTime(revisions) :
        i = 0
        j = 0
        userandtime = []
        usercount = {}
        for line in revisions:
            if j<100:
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
                j=j+1
        return userandtime,j

    def getchanges(userandtime,leng) :
        #changes.append(getchanges(userandtime[i][0], userandtime[i+1][0]))
        changesarr = []
        for i in range(leng-1):
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

    def getsimilarities(wordarr) :
        #return 0
        count = 0 
        similarties = 0
        while count < (len(wordarr)-3) :
            #seen = {}
            for x in wordarr[count+3] :
                for i in range(3) :
                    for y in wordarr[count+i] :
                       
                        if x == y :
                            similarties += 1
            count+=1
        return similarties

    def parsehtml(revision_json) :
        #print(type(revision_json))
        jsonObject = json.loads(revision_json)
        #print(jsonObject)
        html = jsonObject["compare"]["*"]
        soup_dump = BeautifulSoup(html, 'html.parser')
        #print(html)
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

        summary= re.sub(r'[^\w\s]', '', wikipedia.summary(wiki_title)).lower().split()
        sumdict = {}
        for word in summary:
            if word in sumdict:
                sumdict[word] = sumdict[word]+1
            else:
                sumdict[word]=1

        score= 0
        for k in keywords :
            if k in sumdict:
                score += sumdict[k]
        print(score)
        return score 

    def getLinks(wiki_page) :
        return wiki_page.links

    #get wiki page
    wiki_title = request.form['wikipage']
    depth_limit = request.form['wikidepth']
    depth_limit = int(depth_limit)
    keywordstring = request.form['keywords']
    keywords = []
    keywords = keywordstring.lower().split(',')
    #keywords = ["bad", "china", "good", "quality", "country", "asia", "war", "asian", "east", "power", "democracy", "republic"]
    
    results= []
    oldlinks = set()

    def runalgo(wiki_title, depth_limit) :
        if depth_limit<= 0 :
            return 

        wiki_page = wikipedia.page(title = wiki_title, pageid = None, auto_suggest = True, redirect = True, preload = False)
        rev, vscore, similarities = getRevisions(wiki_title)
        kw_score = getKeyWordScore(wiki_title,keywords)
        #results.append([wiki_title, vscore, kw_score, similarities])
        results.append(dict(wiki_title=wiki_title, vscore = vscore, kw_score = kw_score, similarities = similarities))
        links= getLinks(wiki_page)
        i = 0  
        getlinkslength = len(links)
        getlinkslength = getlinkslength/2
        if getlinkslength>10:
            getlinkslength = 9
        #getlinkslength = 3
        while i < getlinkslength : 
            searchlink = links[random.randint(0, len(links)-1)]
            if searchlink in oldlinks:
                searchlink = links[random.randint(0, len(links)-1)]
            else:
                oldlinks.add(searchlink)
                try:
                    runalgo(searchlink, depth_limit-1)
                    i+=1
                except Exception as inst:
                    print(inst)
        return results



    results = runalgo(wiki_title, depth_limit)
    table = ItemTable(results)


    context = dict(table = table, page = wiki_title, depth = depth_limit, keywordstring = keywords)
    return render_template("index2.html", **context)


if __name__ == "__main__":
  import click
  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:
        python server.py
    Show the help text using:
        python server.py --help
    """
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
  run()



 