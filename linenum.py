import wikipedia
import json
import math
from bs4 import BeautifulSoup, NavigableString
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import re
reversions= {}

def between(cur, end):
    print(cur, end)
    while cur and cur != end:
        if isinstance(cur, NavigableString):
            text = cur.strip()
            if len(text):
                yield text
        cur = cur.next_element


def parsehtml(revision_json) :
    jsonObject = json.loads(revision_json)
    html = jsonObject["compare"]["*"]
    soup_dump = BeautifulSoup(html, 'html.parser')
    lineno = soup_dump.find_all('td', {'class': 'diff-lineno'})
    changes =soup_dump.find_all('td', {'class': 'diff-addedline'})
    # print(' '.join(text for text in between(soup_dump.find('td', {'class': 'diff-lineno'}).next_sibling,
    #                                     soup_dump.find('td', {'class': 'diff-lineno'}))))
    html = u""
    c= 0
    # print(soup_dump)
    # x= soup_dump.split("diff-lineno")
    # print(len(x))
    x= []
    x= soup_dump.prettify().split('diff-lineno')
    # print(lineno)
    
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
    print(len(reversions), reversions)
    # print(changes)
   



    # print("changes", changes)
    out = []
    
    for i in changes:
        i = re.sub('<.*?>', '', str(i))
        i = re.sub(r'([^\s\w]|_)+', '', i)
        i = i.strip()
        if (i.isspace()) or (len(i) == 0) or (i == None) or (i == ""):
            continue
        else:
            # out.append(i.split())
            out.append(i)
    
    return out, lineno


wiki_page = wikipedia.page("Taiwan", None, True, True, False)
oldrevid1 = str(944714569)
newrevid1 = str(944715017)
url = 'https://en.wikipedia.org/w/api.php?action=compare&format=json&fromrev=' + oldrevid1 +'&torev=' + newrevid1
openwebsite = urllib2.urlopen(url)
html = openwebsite.read()
insertion, lineno = parsehtml(html)
# print(insertion, lineno)
print(len(insertion), len(lineno))
