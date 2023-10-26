# Lionsight

## Description

Use our app to find contentious spaces on Wikipedia.

We use the following indicators of hositility to determine whether a page is hostile:
1. Reversions of edits: This is found through comments in the edits.
2. Velocity of edits: Speed at which edits are occuring
3. Keywords: Presence of words that would indicate hostility.


We take these inputs and create metrics that we then apply to a regression to get a consolidated contention score. 


## How to use

To run the web app locally, clone the repo and use wikiparser_2.py.

Pip install all necessary packages by running `pip3 install -r requirements.txt`

run `python wikiparser_2.py`

You should then see this webpage on whichever development server spins up:
![Alt](/landingpage.png "Landing Page")
For the Inputs
- Wikipedia Entry: Enter in a title of a Wikipedia Page exactly as Wikipedia has it. Any deviation could lead to error.
- Depth: Number of related pages you want to see contention for. If you want to run the algorithm on just the given wikipedia page enter 1 for the depth search. If you want to look at this page and similar pages enter 2-4 for the depth (2 will give fewer but more similar pages while 4 will give more pages which may be less similar to the original page).
- Keywords: This field is optional. If you know certain keywords, that if appear in the Wikipedia page, likely indicates the page is contentious, record them here. It can help the accuracy of the score.

![Alt](/resultpage.png "Wikiparser result")

The contention score and a True/False contention result will appear on the following page. If the score is >500 then we consider it to be contentious. 
