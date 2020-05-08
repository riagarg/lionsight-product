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
from dateutil.relativedelta import relativedelta
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import dateutil.parser
import threading
import time
import queue
import operator
import multiprocessing
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
	revscore = Col("Reversion Score")
	consolidated_score = Col("Consolidated Score")
	


class Item(object):
	def __init__(self, wiki_title, vscore, kw_score, revscore, consolidated_score):
		self.wiki_title = wiki_title
		self.vscore = vscore
		self.kw_score = kw_score
		self.revscore = revscore
		self.consolidated_score = consolidated_score

@app.route('/')
def index():
	print(request.args)

	return (render_template("index.html"))

@app.route('/index')
def index1():
	return render_template("index.html")



@app.route('/searchpage', methods = ['POST'])
def searchPage():

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
		try:
			max_time = datetime(oldest_dt.year, oldest_dt.month, oldest_dt.day+1, 0, 0)
		except:
			try:
				max_time = datetime(oldest_dt.year, oldest_dt.month+1, 1, 0, 0)
			except:
				max_time = datetime(oldest_dt.year+1, 1, 1, 0, 0)


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


	def calc_velocities_by_dates(by_date, date_type, most_recent_dt, oldest_dt):
		avg_per_period, avg_diff = get_avgs(by_date)
		velocity = 0
		pre_date = by_date[0][0]
		period_over_ave = []
		period_count = 0
		for period in by_date:
			if len(period) > avg_per_period:
				velocity += 0.01 * avg_per_period
				period_over_ave.append(period_count)
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
			period_count += 1
		velocity_summary(period_over_ave, date_type, most_recent_dt, oldest_dt)
		return math.sqrt(velocity)


	def velocity_summary(period_over_ave, date_type, most_recent_dt, oldest_dt):
		to_print = ""
		for period in period_over_ave:
			if (date_type == "year"):
				to_print += str(int(oldest_dt.year) + period) + ", "
			elif (date_type == "month"):
				plus_delta = oldest_dt + relativedelta(months=period)
				to_print += str(plus_delta.month) + "/" + str(plus_delta.year)[2:4] + ", "
			else:
				plus_delta = oldest_dt + timedelta(days=period)
				to_print += str(plus_delta.month) + "/" + str(plus_delta.day) + "/" + str(plus_delta.year)[2:4] + ", "
		#print(date_type + "s with more edits than the avg edits per " + date_type + ": " + to_print[0:len(to_print)-2])


	def calc_total_velocity(by_year, by_month, by_day, most_recent_dt, oldest_dt):
		year = calc_velocities_by_dates(by_year, "year", most_recent_dt, oldest_dt)
		month = calc_velocities_by_dates(by_month, "month", most_recent_dt, oldest_dt)
		day = calc_velocities_by_dates(by_day, "day", most_recent_dt, oldest_dt)
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

		by_year = edits_by_year(userandtime, most_recent_dt, oldest_dt)
		by_month = edits_by_month(userandtime, most_recent_dt, oldest_dt, by_year)
		by_day = edits_by_day(userandtime, most_recent_dt, oldest_dt, by_month)
		print(len(by_day))
		velocity = calc_total_velocity(by_year, by_month, by_day, most_recent_dt, oldest_dt)

		return velocity





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
		my_queue = queue.Queue()

		getEditScores_thread = threading.Thread(getEditScores(userandtime, my_queue))
		getEditScores_thread.start()

		

		# partition = int(leng/4)
		
		# manager = multiprocessing.Manager()
		# jobs = []
		# return_dict = manager.dict()

		# for i in range(4):
		# 	if partition*(i+1)<leng:
		# 		p = multiprocessing.Process(target=getchanges, args=(i,userandtime, i*partition, partition*(i+1), return_dict))
		# 	else:
		# 		p = multiprocessing.Process(target=getchanges, args=(i,userandtime, i*partition, leng-1, return_dict))
		# 	jobs.append(p)
		# 	p.start()

		# for proc in jobs:
		# 	proc.join()

		velocity = get_velocity(userandtime)

		neteditscore, velocityscore, revscore = my_queue.get()

		# changes = []
		# changes = return_dict[1]
		# changes = changes + return_dict[2]
		# changes = changes + return_dict[3]
		# changes = changes + return_dict[4]


		#similarities = getsimilarities(changes)

		#revscore = revscore/len(revisions)*1000

		#return neteditscore, velocity, similarities, revscore
		return neteditscore, velocity, revscore

	def getEditScores (userandtime, out_queue) :
		
		neteditscore = 0
		velocityscore = 0 
		delta_hours = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=6,  weeks=0)
		delta_day = timedelta( days=1, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=0)
		delta_week = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=1)
		delta_month = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=4)
		delta_halfyear = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=26)
		delta_year = timedelta( days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0,  weeks=52)

		now = datetime.now(tz=None)
		revscore = 0
		for line in userandtime:

			revscore += line[6]
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
		
		out_queue.put((neteditscore, velocityscore, revscore)) #add in revscore

	def getUsersandTime(revisions) :
		i = 0
		j = 0
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
			if ("reverted" in comment) or ("Undid" in comment) or ("undid" in comment) or ("Reverted" in comment) or ("Rollback" in comment) or ("rollback" in comment):
				revscore =1
			userandtime.append([revid,username,time,usercount[username],i, comment, revscore])
		return userandtime,j

	def getchanges(num, userandtime, beginning, end, return_dict) :
		#changes.append(getchanges(userandtime[i][0], userandtime[i+1][0]))
		changesarr = []
		i = beginning
		while i<end:
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
			i = i + 1
		return_dict[num+1] = changesarr
		return

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
	for kws in keywords:
		kws = kws.strip()
	#keywords = ["bad", "china", "good", "quality", "country", "asia", "war", "asian", "east", "power", "democracy", "republic"]
	results= []


	#this method isn't used, but might be handy...
	def most_frequent(List):
		dicts = {} 
		for item in List: 
			dicts[item] = dicts.get(item, 0) + 1

		sorted_d = dict(sorted(dicts.items(), key=operator.itemgetter(1),reverse=True))
		print('Dictionary in descending order by value : ',sorted_d)

	def getRevisions10(num, linklist, beginning, end, return_dict):
		#(i,links, i*partition, (i+1)*partition, return_dict1)
		returnlist = []

		i = beginning
		while i<end:
			pageTitle = linklist[i]
			print(pageTitle)
			pageTitle0 = pageTitle
			pageTitle = pageTitle.replace(" ", "_")
			#get up to 10 revisions
			url = "https://en.wikipedia.org/w/api.php?action=query&format=xml&prop=revisions&rvlimit=11&titles=" + pageTitle
			revisions = []                                  #list of all accumulated revisions
			next = ''                                             #information for the next request
			try :
				response = urllib2.urlopen(url + next).read()     #web request
				revisions+=(re.findall('<rev [^>]*>', response.decode("utf-8")))  #adds all revisions from the current request to the list
			except :
				i = i + 1
				continue
			userandtime,leng = getUsersandTime(revisions)


			if leng<10:
				i = i + 1
				continue
			# [revid,username,time,usercount[username],i]
			freq = userandtime[0][2]-userandtime[9][2]
			if freq < timedelta(days=10):
				returnlist.append(pageTitle0)      
			i = i + 1
		return_dict[num+1]=returnlist
		return


	def runalgo(wiki_title, depth_limit) :
		if depth_limit<= 0 :
			return 

		wiki_page = wikipedia.page(title = wiki_title, pageid = None, auto_suggest = True, redirect = True, preload = False)

		links= getLinks(wiki_page)
		#neteditscore, vscore, similarities, revscore = getRevisions(wiki_title)
		neteditscore, vscore, revscore = getRevisions(wiki_title)

		kw_score = getKeyWordScore(wiki_title,keywords)

#rev, vscore, reversions, year, month, day
#net_edit_score, velocity_score, reversion_score, year, month ,day

		consolidated_score= 32.31521 * vscore + 1.123432 * revscore - 285.7542

		#results.append([wiki_title, vscore, kw_score, similarities])
		#results.append(dict(wiki_title=wiki_title, vscore = vscore, kw_score = kw_score, similarities = similarities, revscore = revscore, consolidated_score = consolidated_score))
		results.append(dict(wiki_title=wiki_title, vscore = vscore, kw_score = kw_score, revscore = revscore, consolidated_score = consolidated_score))
		
		if depth_limit>1:
			manager = multiprocessing.Manager()
			jobs = []
			return_dict1 = manager.dict()
			totallinks = len(links)
			print(totallinks)

			partitions = 5
			
			partition = int(totallinks/partitions)

			# print(len(userandtime))
			# print(leng)
			# print(partition)

			for i in range(partitions):
				if partition*(i+1)<totallinks:
					p = multiprocessing.Process(target = getRevisions10, args = (i,links, i*partition, (i+1)*partition, return_dict1))
				else:
					p = multiprocessing.Process(target = getRevisions10, args = (i,links, i*partition, totallinks, return_dict1))
				jobs.append(p)
				p.start()
				
			for proc in jobs:
				proc.join()
			#i = 0 

			links2 = []

			for i in range(partitions):
				links2 = links2+return_dict1[i+1]

			for link in links2:
				try:
					runalgo(link, depth_limit-1)
				except Exception as inst:
					print(inst)

		return results#, year, month, day


	start = time.time()
	results = runalgo(wiki_title, depth_limit)
	elapsed = time.time()-start
	hours = elapsed/3600

	timemsg = "This program took " + str(int(elapsed)) + " seconds, or "+ str(round(hours,3))+" hours to run."

	table = ItemTable(results)


	context = dict(table = table, page = wiki_title, depth = depth_limit, keywordstring = keywords, timemsg = timemsg)
	return render_template("index2.html", **context)


if __name__ == "__main__":
	import click
	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
	run()



 
