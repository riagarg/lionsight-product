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

def getKeyWordScore(wiki_title, keywords):
    summary = re.sub(r'[^\w\s]', '', wikipedia.summary(wiki_title)).lower().split()
    score = 0
    print(wikipedia.summary(wiki_title))
    for k in keywords:
        if k in summary:
            score += summary.count(k) #use better search algo
    return score 


keywords = ["bad", "china", "good", "quality", "country", "asia", "war", "asian", "east", "power", "democracy", "republic"]


print(getKeyWordScore("Taiwan",keywords))