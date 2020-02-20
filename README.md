H4D Guerilla Warfare

Helpful links to get started:

wiki quickstart guide: https://wikipedia.readthedocs.io/en/latest/quickstart.html#quickstart
wiki full API: https://wikipedia.readthedocs.io/en/latest/code.html#api
pywikibot: https://github.com/wikimedia/pywikibot
pypi wikipedia project docs: https://pypi.org/project/wikipedia/
mediaWiki: I have no idea how to use this but i think it's supposed to be helpful so if someone understands how to use pls lmk: https://www.mediawiki.org/wiki/API:Revisions#Example_2:_Get_last_five_revisions_of_a_page_filtered_by_date_and_user
To Do:

Edit score
Currently it counts the number of edits but it doesn't do velocity of edits or it doesn't compare the content of the edits with previous edits
calculate velocity of edits: edits/time (3)
see if 90% of the content is the same as previous edit (5)
Links - (for the recusive stuff)
Currently we pick two random links that are linked by the original page
we should probably be picking the top links that appear in the page (4)
we can see how many times the words of a specific link appear on the page and rank them that way
Keyword score
Create a weighted dictionary instead of a word list and account for weights (2)
we need to decide (and implement) whether we use the summary or the full article for the keywords (1)
Unified score
right now there is a keyword score and a edit score so we will need to find a clever way to make one unified score (5)
Less technical- but we need a way to make the score actually mean something--it should be more than just a number (3)
This could be finding some sort of baseline scores based on non-volitaile pages?? I don't really know rn but it's going to require quite a bit of thought
Computing !!
find a way to like parallize/thread some of this stuff so it doesn't take forever-- look at library "scrapy"/"multiprocessing" (4)
maybe find a way to run on cloud ? (2)
