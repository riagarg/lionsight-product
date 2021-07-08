# Lionsight

## Description

Our project let's you find contentious spaces on Wikipedia and the language and context of hostility.

It uses different indicators as variables in a regression to determine whether a page is hostile:
1. Reversions of edits: This is found through comments in the edits.
2. Velocity of edits: Speed at which edits are occuring
3. Keywords: presence of words that would indicate hostility 

## Running through web app

Go to: https://lionsight.herokuapp.com/

Enter in a wikipedia article that you want to search (Ex. 'Coronavirus'). *Tip: Copy and paste the article title from Wikipedia to ensure you have the syntax correct*

Type in keywords that you think may indicate the article is contentious. Separate the keywords by commas and no spaces. This step is optional. 

Depth search will look at related links to the original link and determines contention on them. It is recommended to keep this number small as it runs recursively and too many levels will make the program run for a long time or crash.

## How to use

To run the web app locally, clone the repo and use wikiparser_2.py.

Pip install all necessary packages including Wikipedia, pandas, BeautifulSoup, re, numpy, seaborn, matplotlib, datetime

run `<python wikiparser_2.py>`

Open the URL that pops up in the console and enter the title of the Wikipedia page.

If you want to run the algorithm on just the given wikipedia page enter 1 for the depth search. If you want to look at this page and similar pages enter 2-4 for the depth (2 will give fewer but more similar pages while 4 will give more pages which may be less similar to the original page).


