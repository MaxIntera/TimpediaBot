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

if len(sys.argv) > 2:
    print 'Error: too many arguments'
    sys.exit(1)

if len(sys.argv) == 2:
    try:
        epnum = int(sys.argv[1])
    except ValueError:
        print 'Error: invalid argument'
        sys.exit(1)
else:
    whichep = 0

# Parse the rss into feed
feed = feedparser.parse('http://www.hellointernet.fm/podcast?format=rss')


numofeps = len(feed['entries']) - 1
whichep = numofeps - epnum

if epnum <= 50:
    whichep += 1


# ----------------------------------------------------------------------------------
# Go through feed
# ----------------------------------------------------------------------------------

timestamp = feed['entries'][whichep]['itunes_duration']
html_description = feed['entries'][whichep]['summary_detail']['value']

# Convert html description to mediawiki format
f = open('description.html', 'w')
f.write(html_description)
f.close()

subprocess.call(['pandoc', '-f', 'html', '-t', 'mediawiki', 'description.html', '-o', 'description.mw'])
f = open('description.mw', 'r')
description = f.read()
f.close()
os.remove('description.html')
os.remove('description.mw')


# Parse the shownotes from the html
soup = BeautifulSoup(html_description, 'html.parser')  
shownotes = []
for link in soup('a'):
    shownotes.append((link.text, link['href']))

firstshownote = 0
for i in range(len(shownotes)):
    if 'discuss' in shownotes[i][0].lower():
        firstshownote = i + 1
        break

title = feed['entries'][whichep]['title_detail']['value']

def seperator(n):
    if n == 89:
        return '--'
    return ':'

title_core = title.split(seperator(epnum), 1)[1].strip()

date = time.strftime('%B %d, %Y', feed['entries'][whichep]['published_parsed'])
date2 = time.strftime('%Y|%B|%d', feed['entries'][whichep]['published_parsed'])
date3 = time.strftime('%d %B %Y', feed['entries'][whichep]['published_parsed'])

link = feed['entries'][whichep]['links'][0]['href']

# Get previous and possibly following episode titles and links
if whichep > 0:
    nexttitle = feed['entries'][whichep - 1]['title_detail']['value'].split(seperator(epnum + 1), 1)[1].strip()
else:
    nexttitle = ''

if epnum > 1:
    prevtitle = feed['entries'][whichep + 1]['title_detail']['value'].split(seperator(epnum - 1), 1)[1].strip()
else:
    prevtitle = ''

# Get first youtube link from search
textToSearch = title
query = urllib.quote(textToSearch)
url = "https://www.youtube.com/results?search_query=" + query
response = urllib2.urlopen(url)
yt_html = response.read()
soup = BeautifulSoup(yt_html, 'html.parser')

ytlink = 'https://www.youtube.com' + soup.find(attrs={'class':'yt-uix-tile-link'})['href']

# Get first reddit link from search
textToSearch = title
query = urllib.quote(textToSearch)
print query
url = "https://www.reddit.com/r/CGPGrey/search?q=" + query + "&restrict_sr=on&sort=relevance&t=all"
response = urllib2.urlopen(url)
red_html = response.read()
soup = BeautifulSoup(red_html, 'html.parser')

try:
    redlink = 'https://reddit.com' + soup.find_all('header', {"class" : "search-result-header"})[0].find_all('a')[0].get('href')
except IndexError:
    print "Reddit link not found. Please try again later or enter link manually."
    redlink = 'https://reddit.com/r/CGPGrey'

ituneslink = 'http://www.hellointernet.fm/itunes'

# Create a list of sponsors
sponsors = []
for note in shownotes[:firstshownote]:
    if 'listeners' not in note[0].lower() and 'patreon' not in note[0].lower() and 'rss' not in note[0].lower() and 'itunes' not in note[0].lower() and 'discuss' not in note[0].lower():
        name = ''
        for char in note[0]:
            if char.isalnum():
                name += char
            else:
                break
        sponsors.append(name)

f = open('formatted.txt', 'w')

# Write to file

f.write('{{Infobox television episode\n')
f.write('| title = ' + title_core + '\n')
f.write('| series = [[Hello Internet]]\n')
f.write('| image = {{right|{{#widget:YouTube|id=' + ytlink.split('v=', 1)[1] + '|height=188|width=336}}}}\n')
f.write('| caption = Episode 90 on the [[Hello Internet (YouTube channel)|podcast YouTube channel]]\n')
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

# https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

intro = ''
intro += '\"\'\'\'' + title + '\'\'\'\" is the ' + ordinal(epnum)
if whichep == 0:
    intro += ' and most recent episode of'
intro += ' \'\'[[Hello Internet]]\'\', released on ' + date + '.<ref name="HI page">{{cite web|title= ' + title
intro += '|url=' + link + '|website=Hello Internet|publisher=\'\'Hello Internet\'\'|accessdate='
intro += date3 + '}}</ref>\n\n'

f.write(intro)


f.write('==Official Description==\n')
f.write(description.split('==', 1)[0].strip())

f.write('\n\n==Show Notes==\n')
for snlink in shownotes[firstshownote:]:
    f.write('*[' + snlink[1] + ' ' + snlink[0] + ']\n')

curmonth = time.strftime('%B %Y', time.gmtime())

footer = ''
footer += '{{collapse top|title=Fan Art}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{collapse top|title=Flowchart}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{collapse top|title=Summary}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{collapse top|title=Transcript}}\n{{Empty section|date=' + curmonth +'}}\n{{collapse bottom}}\n\n'
footer += '{{Hello Internet episodes}}\n\n'
footer += '==References==\n{{reflist}}\n\n[[Category:HelloInternetEpisode]]\n\n__NOTOC__\n'
f.write(footer)

f.close()

