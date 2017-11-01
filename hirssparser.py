import subprocess
import time
import urllib
import urllib2
from bs4 import BeautifulSoup
import datetime
import os
import sys
import feedparser

# Use UTF-8
reload(sys)  
sys.setdefaultencoding('utf8')

# Check args
if len(sys.argv) != 2:
    print 'Error: incorrect number of arguments'
    sys.exit(1)
else:
    try:
        epnum = int(sys.argv[1])
    except ValueError:
        print 'Error: invalid argument'
        sys.exit(1)

# Parse the rss into feed
feed = feedparser.parse('http://www.hellointernet.fm/podcast?format=rss')
print('Downloaded rss...')

numofeps = len(feed['entries']) - 1
whichep = numofeps - epnum

# Account for the shortlist bonus episode
if epnum <= 50:
    whichep += 1


# ----------------------------------------------------------------------------------
# Go through feed
# ----------------------------------------------------------------------------------

timestamp = feed['entries'][whichep]['itunes_duration']
print('Fetched timestamp...')

html_description = feed['entries'][whichep]['summary_detail']['value']
print('Fetched description HTML...')

# Convert html description to mediawiki format
f = open('description.html', 'w')
f.write(html_description)
f.close()

subprocess.call(['pandoc', '-f', 'html', '-t', 'mediawiki', 'description.html', '-o', 'description.mw'])

# Use search and replace to tweak some formatting minutae
replacements = {'==':'=', 'By:':'By', 'Notes:':'Notes', 'Sponsors:':'Sponsors'}
lines = []
with open('description.mw') as infile:
    for line in infile:
        for src, target in replacements.iteritems():
            line = line.replace(src, target)
        lines.append(line)
        print(line)
with open('description.mw', 'w') as outfile:
    for line in lines:
        outfile.write(line)

f = open('description.mw', 'r')
description = f.read()
f.close()

os.remove('description.html')
os.remove('description.mw')
print('Created MediaWiki-format description...')

soup = BeautifulSoup(html_description, 'html.parser')  
shownotes = []
for link in soup('a'):
    shownotes.append((link.text, link['href']))

# Calculate where the first real shownote starts for later
firstshownote = 0
for i in range(len(shownotes)):
    if 'discuss' in shownotes[i][0].lower():
        firstshownote = i + 1
        break

# Get title
title = feed['entries'][whichep]['title_detail']['value']
print('Fetched title...')

def seperator(n):
    if n == 89:
        return '--'
    return ':'

title_core = title.split(seperator(epnum), 1)[1].strip()
print('Processed a stripped down version of the title...')

# Dates and date formats
date = time.strftime('%B %d, %Y', feed['entries'][whichep]['published_parsed'])
date2 = time.strftime('%Y|%B|%d', feed['entries'][whichep]['published_parsed'])
date3 = time.strftime('%d %B %Y', time.gmtime())
print('Formatted release date...')

# hellointernet.fm link
link = feed['entries'][whichep]['links'][0]['href']
print('Fetched hellointernet.fm link...')

# Get previous and possibly following episode titles and links
if whichep > 0:
    nexttitle = feed['entries'][whichep - 1]['title_detail']['value'].split(seperator(epnum + 1), 1)[1].strip()
else:
    nexttitle = ''

if epnum > 1:
    prevtitle = feed['entries'][whichep + 1]['title_detail']['value'].split(seperator(epnum - 1), 1)[1].strip()
else:
    prevtitle = ''
print('Fetched previous and next titles...')

# Get first youtube link from search
textToSearch = title
query = urllib.quote(textToSearch)
url = "https://www.youtube.com/results?search_query=" + query
response = urllib2.urlopen(url)
yt_html = response.read()
soup = BeautifulSoup(yt_html, 'html.parser')

ytlink = 'https://www.youtube.com' + soup.find(attrs={'class':'yt-uix-tile-link'})['href']
print('Fetched YouTube link...')

# Get first reddit link from search
textToSearch = title
query = urllib.quote(textToSearch)
url = "https://www.reddit.com/r/CGPGrey/search?q=" + query + "&restrict_sr=on&sort=relevance&t=all"
def searchReddit():
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPException:
        print('Error searching reddit, retrying...')
        searchReddit()
red_html = response.read()
soup = BeautifulSoup(red_html, 'html.parser')

try:
    redlink = 'https://reddit.com' + soup.find_all('header', {"class" : "search-result-header"})[0].find_all('a')[0].get('href')
except IndexError:
    print "Reddit link not found. Please try again later or enter link manually."
    redlink = 'https://reddit.com/r/CGPGrey'
print('Fetched Reddit link...')

ituneslink = 'http://www.hellointernet.fm/itunes'

# Create a list of sponsors
sponsors = []
for note in shownotes[:firstshownote]:
    if 'listeners' not in note[0].lower() and 'patreon' not in note[0].lower() and 'rss' not in note[0].lower() and 'itunes' not in note[0].lower() and 'discuss' not in note[0].lower():
        name = ''
        for char in note[0]:
            if char.isalnum() or char == '\'':
                name += char
            else:
                break
        sponsors.append(name)
print('Created list of sponsors...')



f = open('formatted.txt', 'w')

# Write to file

f.write('{{Infobox television episode\n')
f.write('| title = ' + title_core + '\n')
f.write('| series = [[Hello Internet]]\n')
f.write('| image = {{right|{{#widget:YouTube|id=' + ytlink.split('v=', 1)[1] + '|height=188|width=336}}}}\n')
f.write('| caption = Episode ' + str(epnum) + ' on the [[Hello Internet (YouTube channel)|podcast YouTube channel]]\n')
f.write('| episode = ' + str(epnum) + '\n')
f.write('| presenter = {{hlist|[[CGP Grey]]|[[Brady Haran]]}}\n')
f.write('| airdate = {{Start date|' + date2 + '}}\n')
f.write('| length = ' + timestamp + '\n')
f.write('| reddit = [' + redlink + ' Link]\n')
f.write('| website = [' + link + ' Link]\n')
f.write('| sponsors     = {{hlist|' + '|'.join(sponsors) + '}}\n')
f.write('| prev = [[H.I. No. ' + str(epnum - 1) + ': ' + prevtitle + '|' + prevtitle + ']]\n')
if nexttitle == '':
    f.write('| next = \n')
else:
    f.write('| next = [[H.I. No. ' + str(epnum + 1) + ': ' + nexttitle + '|' + nexttitle + ']]\n')
f.write('| episode_list = [[List of Hello Internet episodes]]\n')
f.write('}}\n')
print('Created info box...')


# https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

intro = ''
intro += '\"\'\'\'' + title + '\'\'\'\" is the ' + ordinal(epnum)
if whichep == 0:
    intro += ' and most recent'
intro += ' episode of \'\'[[Hello Internet]]\'\', released on ' + date + '.<ref name="HI page">{{cite web|title= ' + title
intro += '|url=' + link + '|website=Hello Internet|publisher=\'\'Hello Internet\'\'|accessdate='
intro += date3 + '}}</ref>\n\n'

f.write(intro)
print('Created initial paragraph')

f.write('= Official Description =\n')
f.write(description)
print('Added official description and shownotes...') 

curmonth = time.strftime('%B %Y', time.gmtime())

footer = '= Other =\n'
footer += '{{collapse top|title=Fan Art}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{collapse top|title=Flowchart}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{collapse top|title=Summary}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{collapse top|title=Transcript}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '= References =\n{{reflist}}\n\n[[Category:HelloInternetEpisode]]\n\n'
footer += '{{Hello Internet episodes}}\n\n__NOTOC__\n'
f.write(footer)
print('Created footer elements...')

f.close()
print('Article generation complete.\n')

