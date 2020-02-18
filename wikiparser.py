try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import re
import wikipedia
import random

def getRevisions(pageTitle):
    pageTitle = pageTitle.replace(" ", "_")
    url = "https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=revisions&rvlimit=500&titles=" + pageTitle
    revisions = []                                        #list of all accumulated revisions
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

    return len(revisions)

def getKeyWordScore(wiki_title, keywords):

    summary= re.sub(r'[^\w\s]', '', wikipedia.summary(wiki_title)).lower().split()
    score= 0
    for k in keywords :
        if k in summary :
            score += summary.count(k)
    return score 

def getLinks(wiki_page) :
    return wiki_page.links

#get wiki page
wiki_title =input("wiki page title: ")
depth_limit = 3
keywords = ["bad", "taiwan", "china", "good", "bean", "beans", "caffeine", "organic", "coffee", "consume", "quality", "country", "asia", "war", "goods", "pacific", "organization", "republic", "west" ]

results= []
i = 0 
def runalgo(wiki_title, depth_limit) :
    if depth_limit<= 0 :
        return 

    wiki_page = wikipedia.page(wiki_title, None, True, True, False)
    rev = getRevisions(wiki_title)
    kw_score = getKeyWordScore(wiki_title,keywords)
    results.append([wiki_title, rev, kw_score])

    links= getLinks(wiki_page)

    i = 0 
    while i < 2 : 
        runalgo(links[random.randint(0, len(links)-1)], depth_limit-1)
        i+=1

runalgo(wiki_title, depth_limit)
#summary= wikipedia.summary(wiki_title).lower().split()

print(results)

