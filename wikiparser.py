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
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np


def get_revisions(page_title):
    page_title = page_title.replace(" ", "_")
    url = "https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=revisions&rvlimit=500&titles=" + page_title
    revisions = []  # list of all accumulated revisions
    next_req = ''  # information for the next request

    while True:
        try:
            response = urllib2.urlopen(url + next_req).read()  # web request
            revisions += (re.findall('<rev [^>]*>', response.decode(
                "utf-8")))  # adds all revisions from the current request to the list
            cont = re.search('<continue rvcontinue="([^"]+)"', response.decode("utf-8"))
            if not cont:  # break the loop if 'continue' element missing
                break
            next_req = "&rvcontinue=" + cont.group(1)  # gets the revision Id from which to start the next request
        except:
            return 0

    user_and_time = get_users_and_time(revisions)
    net_edit_score, velocity_score = get_edit_scores(user_and_time)
    get_velocity(user_and_time)
    changes = get_changes(user_and_time)
    similarities = get_similarities(changes)
    return net_edit_score, velocity_score, similarities


def get_velocity(userandtime):
    # timecomp = []
    # prevtime = None
    # for line in userandtime:
    #     if prevtime != None:
    #         dif = prevtime - line[2]
    #         timecomp.append(dif)
    #     prevtime = line[2]
    # print("timecomp", timecomp)

    # get data and create df
    times = []
    ids = []
    for line in userandtime:
        t = line[2]
        times.append(t.timestamp())
        ids.append(line[0])
    data = {'time': times, 'revid': ids}
    df = pd.DataFrame(data=data, columns=['time', 'revid'])

    cluster_count = math.floor(math.sqrt(len(userandtime)))
    # print(userandtime)
    print("cluster_count", cluster_count)
    kmeans = KMeans(n_clusters=cluster_count).fit(df)
    # centroids = kmeans.cluster_centers_
    # get number of items per cluster
    # find the time frame of the cluster (subtract latest time from earliest)

    # itemsincluster = []
    # top = 0
    scores = []
    for num in range(0, cluster_count):
        cluster = np.where(kmeans.labels_ == num)[0]
        # datetime_cluster = []
        # for time in cluster:
        #     datetime_cluster.append(datetime.utcfromtimestamp(time))
        timeframe = max(cluster) - min(cluster)
        clusterscore = timeframe / len(cluster)
        scores.append(clusterscore)
        # if clusterscore < smallest: smallest = clusterscore
        # itemsincluster.append(len(cluster))
    scores.sort()
    remove = math.ceil(.5 * cluster_count)
    scores = scores[remove:]

    print("mean", np.mean(scores))  # smaller number = more volatile


def get_edit_scores(user_and_time):
    net_edit_score = 0
    velocity_score = 0
    delta_hours = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=6, weeks=0)
    delta_day = timedelta(days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
    delta_week = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=1)
    delta_month = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=4)
    delta_halfyear = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=26)
    delta_year = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=52)

    now = datetime.now(tz=None)
    for line in user_and_time:
        if line[2] > (now - delta_hours):
            velocity_score += 2
        elif line[2] > (now - delta_day):
            velocity_score += 1.5
        elif line[2] > (now - delta_week):
            velocity_score += 1.2
        elif line[2] > (now - delta_month):
            velocity_score += .2
        elif line[2] > (now - delta_halfyear):
            velocity_score += .15
        elif line[2] > (now - delta_year):  # LOOK AT EDITS IN WINDOWS SO THAT YOU FIND PAST WINDOWS
            velocity_score += .1  # could be assigned to past thing
        else:
            velocity_score += .01

        if line[4] == 1:
            edit_score = .5  # if the edit is done by a bot
        else:
            edit_score = line[3]

        if edit_score > 1:
            edit_score = math.sqrt(edit_score)  # if the edit is done by a normal person

        net_edit_score = net_edit_score + edit_score
    return net_edit_score, velocity_score


def get_users_and_time(revisions):
    user_and_time = []
    user_count = {}

    for line in revisions:
        p = line.find('user="')
        p = p + 6
        p1 = line.find('"', p)
        username = line[p:p1]
        t = line.find('timestamp=')
        t = t + 11
        t1 = line.find('Z', t)
        time = line[t:t1]
        time = datetime.fromisoformat(time)
        revise = line.find('revid="')
        revise = revise + 7
        revise1 = line.find('"', revise)
        revid = line[revise:revise1]
        i = 0
        if re.findall('bot', username):
            i = 1
        if username in user_count:
            user_count[username] = user_count[username] + 1
        else:
            user_count[username] = 1
        user_and_time.append([revid, username, time, user_count[username], i])
    return user_and_time


def get_changes(user_and_time):
    changes_arr = []
    for i in range(100):
        oldrevid = user_and_time[i][0]
        newrevid = user_and_time[i + 1][0]
        url = 'https://en.wikipedia.org/w/api.php?action=compare&format=json&fromrev=' + str(oldrevid) +\
              '&torev=' + str(newrevid)
        open_website = urllib2.urlopen(url)
        html = open_website.read()
        insertion = parse_html(html)
        changes = [oldrevid, newrevid, insertion]
        changes_arr.append(changes)
    return changes_arr


def get_similarities(word_arr):
    count = 0
    similarities = 0
    while count < (len(word_arr) - 3):
        for x in word_arr[count + 3]:
            for i in range(3):
                for y in word_arr[count + i]:
                    if x == y:
                        similarities += 1
        count += 1
    return similarities


def parse_html(revision_json):
    json_object = json.loads(revision_json)
    html = json_object["compare"]["*"]
    soup_dump = BeautifulSoup(html, 'html.parser')
    changes = soup_dump.find_all('ins', {'class': 'diffchange'})
    out = []

    for i in changes:
        i = re.sub('<.*?>', '', str(i))
        i = re.sub(r'([^\s\w]|_)+', '', i)
        i = i.strip()
        if (i.isspace()) or (len(i) == 0) or (i is None) or (i == ""):
            continue
        else:
            out.append(i)
    return out


def get_key_word_score(wiki_title, keywords):
    summary = re.sub(r'[^\w\s]', '', wikipedia.summary(wiki_title)).lower().split()
    score = 0
    for k in keywords:
        if k in summary:
            score += summary.count(k)  # use better search algo
    return score


def get_links(wiki_page):
    return wiki_page.links


def run_algo(wiki_title, depth_limit, keywords):
    if depth_limit <= 0:
        return

    results = []
    wiki_page = wikipedia.page(wiki_title, None, True, True, False)
    rev, vscore, similarities = get_revisions(wiki_title)
    kw_score = get_key_word_score(wiki_title, keywords)

    results.append([wiki_title, vscore, kw_score, similarities])
    links = get_links(wiki_page)

    i = 0
    while i < 2:
        run_algo(links[random.randint(0, len(links) - 1)], depth_limit - 1, keywords)
        i += 1
    return results


def parse_wiki():
    wiki_title = input("wiki page title: ")
    depth_limit = 1
    keywords = ["bad", "china", "good", "quality", "country", "asia", "war", "asian", "east", "power", "democracy",
                "republic"]
    results = run_algo(wiki_title, depth_limit, keywords)
    print(results)


parse_wiki()
