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
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import dateutil.parser

def get_revisions(page_title):
    page_title = page_title.replace(" ", "_")
    url = "https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=revisions&rvlimit=500&titles=" + page_title
    revisions = []  # list of all accumulated revisions
    next_req = ''  # information for the next request

    while True:
        try:
            response = urllib2.urlopen(url + next_req).read()  # web request
            revisions += (re.findall('<rev [^>]*>', response.decode("utf-8")))  # adds all revisions from the current request to the list
            cont = re.search('<continue rvcontinue="([^"]+)"', response.decode("utf-8"))
            if not cont:  # break the loop if 'continue' element missing
                break
            next_req = "&rvcontinue=" + cont.group(1)  # gets the revision Id from which to start the next request
        except:
            return 0

    user_and_time = get_users_and_time(revisions)
    net_edit_score, velocity_score = get_edit_scores(user_and_time)
    year, month, day = get_velocity(user_and_time)
    changes = get_changes(user_and_time)
    similarities = get_similarities(changes)
    return net_edit_score, velocity_score, similarities, year, month ,day


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
    revscore = 0
    for line in userandtime:

        revscore += line[6]
        if line[2] > (now- delta_hours) :
            velocityscore += 2
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

        neteditscore = neteditscore + editscore
    return neteditscore, velocityscore, revscore


def get_users_and_time(revisions):
    user_and_time = []
    user_count = {}

    for line in revisions:

        u_start = line.find('user="')
        u_start = u_start + len('user="')
        u_end = line.find('"', u_start)
        username = line[u_start:u_end]

        t_start = line.find('timestamp="')
        t_start = t_start + len('timestamp="')
        t_end = line.find('Z', t_start)
        time = line[t_start:t_end]

        ###########################
        ###########################
        ###########################
        # time = datetime.fromisoformat(time) adjust for python 3.6.9
        time = dateutil.parser.isoparse(time)

        r_start = line.find('revid="')
        r_start = r_start + len('revid="')
        r_end = line.find('"', r_start)
        revid = line[r_start:r_end]

        comment = line.find('comment="')
        comment = comment + 9
        comment1 = line.find('"',comment)
        comment = line[comment:comment1]

        i = 0
        if re.findall('bot', username):
            i = 1
        if username in user_count:
            user_count[username] = user_count[username] + 1
        else:
            usercount[username] = 1
        revscore = 0
        if ("reverted" in comment) or ("Undid" in comment) or ("undid" in comment) or ("Reverted" in comment):
            revscore =1
        userandtime.append([revid, username, time, usercount[username], i, comment, revscore])
    print("userntime", len(userandtime))
    return userandtime

def get_changes(userandtime):
    changesarr = []
    max = len(user_and_time) if len(user_and_time) < 200 else 200
    for i in range(0,max):
      if (i + 1 < max):
        oldrevid = user_and_time[i][0]
        newrevid = user_and_time[i + 1][0]
        url = 'https://en.wikipedia.org/w/api.php?action=compare&format=json&fromrev=' + str(oldrevid) + '&torev=' + str(newrevid)
        open_website = urllib2.urlopen(url)
        html = open_website.read()
        insertion = parse_html(html)
        changes = [oldrevid, newrevid, insertion]
        changes_arr.append(changes)
    return changesarr


def get_similarities(wordarr):
    count = 0 
    score = 0
    while count < (len(wordarr)-3):
        if len(wordarr[count][2]) > 0:
            for x in wordarr[count][2][0]:
                for i in range(3):
                    similarities = 0
                    if len(wordarr[count+i+1][2]) > 0:
                        for y in wordarr[count+i+1][2][0]:
                            if x == y:
                                similarities += 1
                        s = similarities/ len(wordarr[count])
                        if s >.7 :
                            score+=1
        count+=1
    print(score)
    return score


def parse_html(revision_json):
    json_object = json.loads(revision_json)
    html = json_object["compare"]["*"]
    soup_dump = BeautifulSoup(html, 'html.parser')

    changes = soup_dump.find_all('ins', {'class': 'diffchange'})
    # change =soup_dump.find_all('td', {'class': 'diffchange'}).get_text()
    # print("changes", changes)
    out = []

    for i in changes:
        i = re.sub('<.*?>', '', str(i))
        i = re.sub(r'([^\s\w]|_)+', '', i)
        i = i.strip()
        if (i.isspace()) or (len(i) == 0) or (i is None) or (i == ""):
            continue
        else:
            out.append(i.split())
    
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
    rev, vscore, similarities, year, month, day = get_revisions(wiki_title)
    kw_score = get_key_word_score(wiki_title, keywords)

    results.append([wiki_title, vscore, kw_score, similarities])
    links = get_links(wiki_page)

    i = 0
    while i < 2:
        run_algo(links[random.randint(0, len(links) - 1)], depth_limit - 1, keywords)
        i += 1
    return results, year, month, day

# NEW VELOCITY HELPER FUNCTIONS

def leap_year(year):
    leap_year = False
    if (year % 4) == 0:
        if (year % 100) == 0:
            if (year % 400) == 0:
                leap_year = True
        leap_year = True
    return leap_year


def month_length(dt):
    ly = leap_year(dt.year)
    if dt.month == 2 and ly: return 29 # February leap year
    elif dt.month == 2 and not ly: return 28 # February normal year
    elif dt.month == 4: return 30 # April
    elif dt.month == 6: return 30 # June
    elif dt.month == 9: return 30 # September
    elif dt.month == 11: return 30 # November
    else: return 31 # Jan, Mar, May, Jul, Aug, Oct, Dec


def calc_num_days(begin, end):
    total = month_length(begin) - begin.day # add remainder of first month
    dt = datetime(begin.year, begin.month + 1, 1, 0, 0)
    while dt.year < end.year: # add days from full intervening years
        total += month_length(dt)
        new_year = dt.year
        new_month = dt.month + 1
        if new_month > 12:
            new_year += 1
            new_month = 1
        dt = datetime(new_year, new_month, 1, 0, 0)
    while dt.month < end.month: # add days from most recent year besides most recent month
        total += month_length(dt)
        dt = datetime(dt.year, dt.month + 1, 1, 0, 0)
    for i in range(1,32): # add days from most recent month
        if i == end.day: total += i 
    return total

# GROUP EDITS BY YEAR, MONTH, AND DAY

def edits_by_year(userandtime, most_recent_dt, oldest_dt):
    delta_year = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=52)
    num_years = most_recent_dt.year - oldest_dt.year
    by_year = []
    min_time = oldest_dt
    max_time = datetime(oldest_dt.year+1, 1, 1, 0, 0)
    while len(by_year) < num_years + 1:
        year = []
        for edit in userandtime:
            if min_time <= edit[2] and edit[2] < max_time:
                year.append(edit)
        by_year.append(year)
        min_time = max_time
        max_time = min_time + delta_year
    return by_year


def edits_by_month(userandtime, most_recent_dt, oldest_dt, by_year):
    delta_month = timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=4)
    num_years = most_recent_dt.year - oldest_dt.year
    num_months = (12-oldest_dt.month) + ((num_years-1)*12) + (most_recent_dt.month+1)
    by_month = []
    min_time = oldest_dt
    max_time = datetime(oldest_dt.year, oldest_dt.month + 1, 1, 0, 0)

    while len(by_month) < num_months:
        month = []
        for year in by_year:
            for edit in year:
                if min_time <= edit[2] and edit[2] < max_time:
                    month.append(edit)
        by_month.append(month)

        min_time = max_time
        max_year = min_time.year
        max_month = min_time.month + 1
        if min_time.month == 12:
            max_year = min_time.year + 1
            max_month = 1
        max_time = datetime(max_year, max_month, 1, 0, 0)
    return by_month


def edits_by_day(userandtime, most_recent_dt, oldest_dt, by_month):
    delta_day = timedelta(days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
    by_day = []
    min_time = oldest_dt
    max_time = datetime(oldest_dt.year, oldest_dt.month, oldest_dt.day+1, 0, 0)

    num_days = calc_num_days(oldest_dt, most_recent_dt)
    while len(by_day) < num_days:
        day = []
        for month in by_month:
            for edit in month:
                if min_time <= edit[2] and edit[2] < max_time:
                    day.append(edit)
        by_day.append(day)

        min_time = max_time
        if min_time.day < month_length(min_time): # stay in same month
            max_year = min_time.year
            max_month = min_time.month
            max_day = min_time.day+1
        else: # need to increment month
            max_month = min_time.month + 1
            max_day = 1
            if max_month > 12: # need to increment year
                max_month = 1
                max_year = min_time.year + 1
        max_time = datetime(max_year, max_month, max_day, 0, 0)
    return by_day

# CALCULATE VELOCITY

def get_avgs(by_date):
    avg_per_period = 0
    for period in by_date:
        avg_per_period += len(period)
    avg_per_period /= len(by_date)

    datetimeList = []
    for period in by_date:
        for edit in period:
            datetimeList.append(edit[2])
    sumOfTime = sum(map(datetime.timestamp,datetimeList))
    averageTimeInTSFormat = datetime.fromtimestamp(sumOfTime/len(datetimeList))
    times = datetime.strftime(averageTimeInTSFormat,"%H:%M:%S").split(":")
    avg_diff = timedelta(hours=int(times[0]), minutes=int(times[1]), seconds=int(times[2]))

    return avg_per_period, avg_diff

def calc_velocities_by_dates(by_date):
    avg_per_period, avg_diff = get_avgs(by_date)
    velocity = 0
    pre_date = by_date[0][0]
    for period in by_date:
        if len(period) > avg_per_period:
            velocity += 0.01 * avg_per_period
        for date in period:
            if pre_date != date:
                diff = date[2] - pre_date[2]
                if diff < (avg_diff/2):
                    velocity += 0.05 * avg_per_period
                elif (avg_diff/2) < diff and diff < avg_diff:
                    velocity += 0.03 * avg_per_period
                elif avg_diff < diff and diff < (avg_diff + (avg_diff/2)):
                    velocity += 0.02 * avg_per_period
                elif (avg_diff + (avg_diff/2)) < diff:
                    velocity += 0.01 * avg_per_period
            pre_date = date
    return math.sqrt(velocity)


def calc_total_velocity(by_year, by_month, by_day):
    year = calc_velocities_by_dates(by_year)
    month = calc_velocities_by_dates(by_month)
    day = calc_velocities_by_dates(by_day)
    return math.sqrt(year+month+day)


def get_newest_oldest_dt(userandtime):
    now = datetime.now()
    most_recent = now
    oldest = now
    for edit in userandtime:
        if most_recent == now:
            most_recent = edit
            oldest = edit
            continue
        if (datetime.now() - edit[2]) < (datetime.now() - most_recent[2]):
            most_recent = edit
        elif (datetime.now() - edit[2]) > (datetime.now() - oldest[2]):
            oldest = edit
    return most_recent[2], oldest[2]

def get_velocity(userandtime):
    most_recent_dt, oldest_dt = get_newest_oldest_dt(userandtime)
    print("most_recent_dt:", most_recent_dt)
    print("oldest_dt:", oldest_dt)

    by_year = edits_by_year(userandtime, most_recent_dt, oldest_dt)
    print("len by_year:", len(by_year))
    by_month = edits_by_month(userandtime, most_recent_dt, oldest_dt, by_year)
    print("len by_month:", len(by_month))
    by_day = edits_by_day(userandtime, most_recent_dt, oldest_dt, by_month)
    print("len by_day:", len(by_day))

    velocity = calc_total_velocity(by_year, by_month, by_day)
    print("total velocity:", velocity)

    return (by_year, by_month, by_day)

# RUN CODE

def parse_wiki():
    wiki_title = input("wiki page title: ")
    depth_limit = 1
    keywords = []
    results, year, month, day = run_algo(wiki_title, depth_limit, keywords)
    print(results)
    return (year, month, day)

# DATA COLLECTION

year, month, day = parse_wiki()

generalData = pd.DataFrame([], columns = ("revID", "Editor","DateTime","??", "?"))
for i in day:
    currentParse = pd.DataFrame(i, columns = ("revID", "Editor","DateTime","??", "?"))
    generalData = generalData.append(currentParse)

# print(generalData)

generalData['DateTime'] = pd.to_datetime(generalData['DateTime'])
generalData['Year'] = generalData['DateTime'].dt.year
generalData['Month'] = generalData['DateTime'].dt.month
generalData['Date'] = generalData['DateTime'].dt.date

# generalData

sns.set(style="darkgrid")
plt.figure(figsize=(20,10))
plot = sns.countplot(generalData['Year'], color=None)
plot.axes.set_title("Edits on Wikipedia's Coronavirus Page", fontsize=50)
plot.tick_params(labelsize=10)
plot.set_ylabel("Count of Edits")


def collect_data():
    list = ["Homosexuality", "Abortion", "Benjamin Franklin", "Elvis Presley", "Nuclear power", "Nicolaus Copernicus", "Tiger", "Euthanasia", "Alzheimer's disease", "Sherlock Holmes", "Israel and the apartheid analogy", "Liancourt Rocks", "Schizophrenia", "Pumpkin", "SQL", "Password", "Henry Cavendish", "Pension", "Mexican drug war", "Hungarians in Romania", "Markov chain", "Mentha", "Foucault pendulum", "Indian cobra", "Harmonium", "Infrared photography", "Bohrium", "Hungarian forint", "Hendrik Lorentz", "1980s oil glut", "Deutsches Museum", "Ara (genus", "Schlenk flask"]
    for item in list:
        wiki_title = item
        year, month, day = parse_wiki()