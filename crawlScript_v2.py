import urllib2
import os
from bs4 import BeautifulSoup # donwload here: http://www.crummy.com/software/BeautifulSoup/#Download
from datetime import datetime

# this is a good utility function for getting text between two tags
def getContents(htmlText, startTag, endTag, start=0, end=-1):
    if end == -1:
        end = len(htmlText)
    startIndex = htmlText.find(startTag, start, end) + len(startTag)
    endIndex = htmlText.find(endTag, startIndex)
    if startIndex == -1 or endIndex == -1:
        return ""
    else:
        return htmlText[startIndex:endIndex]

def parsePlayer(linkText): # link text of the form <a href = ...>Player Name</a>
    playerName = getContents(linkText, ">", "</a")
    playerID = int(getContents(linkText, '<a href="/player/', "/"))
    return (playerID, playerName)
    
def parseStat(statText):
    statText = statText.strip()
    if statText is "-":
        return 0
    else:
        return int(statText)

# os.path.join
dropboxPath = "C:\Users\Matt\Documents\Dropbox\Sports Project\CrawlData"

page_id = 200007;
page_id_string = str(page_id).zfill(6)

urlString = "http://www.espnfc.co.uk/gamecast/statistics/id/" + page_id_string + "/statistics.html"
response = urllib2.urlopen(urlString)
page_source = response.read()
soup = BeautifulSoup(page_source)

# get team names
awayTeam = getContents(page_source, '<h1 id="away-team" class="heading alt">', '</h1>')
homeTeam = getContents(page_source, '<h1 id="home-team" class="heading alt">', '</h1>')

if not homeTeam or not awayTeam:
    print page_id_string + ": Not a match!"
else:
    print awayTeam+' @ '+homeTeam
    
# match date
matchDate = getContents(page_source, "= new Date(", ")")
matchDate = datetime.utcfromtimestamp(int(matchDate) / 1000)
matchDateStr = matchDate.strftime("%Y-%m-%d, %H:%M")
print matchDateStr
    
# get stat column titles
statAbbrevs = []
statTitles = []
for tag in soup.find_all("tr"):
    if tag.th and tag.prettify().find("pstat") > -1:
        statList = tag.find_all('th')
        for stat in statList:
            statAbbrevs.append(stat.text.strip())
            if stat.has_attr("title"):
                statTitles.append(stat.attrs["title"])
            else:
                statTitles.append(statAbbrevs[-1])
        break

# get the indices to search from
awayIndex = page_source.find('<h1 id="away-team" class="heading alt">')
homeIndex = page_source.find('<h1 id="home-team" class="heading alt">')

# get the away lineup and subs
awayLineup = getContents(page_source, '<td class="first">', 'Substitutes', start=awayIndex)
awaySubs = getContents(page_source, 'Substitutes', '</table>', start=awayIndex)

# get the home lineup and subs
homeLineup = getContents(page_source, '<td class="first">', 'Substitutes', start=homeIndex)
homeSubs = getContents(page_source, 'Substitutes', '</table>', start=homeIndex)

# get away team starters!
awayStarters = []
startIndex=0
while awayLineup.find('<p>', startIndex) > -1:
    awayStarters.append(dict())
    
    startTag = "<p>"    
    endTag = "</p>"
    awayStarters[-1][statAbbrevs[0]] = getContents(awayLineup, startTag, endTag, start=startIndex)
    startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"
    endTag = "</td>"
    awayStarters[-1][statAbbrevs[1]] = int(getContents(awayLineup, startTag, endTag, start=startIndex))
    startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"    
    endTag = "</td>"
    awayStarters[-1][statAbbrevs[2]] = parsePlayer(getContents(awayLineup, startTag, endTag, start=startIndex))
    startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    for statLoop in range(3, len(statAbbrevs)):
        startTag = "<td>"        
        endTag = "</td>"
        awayStarters[-1][statAbbrevs[statLoop]] = parseStat(getContents(awayLineup, startTag, endTag, start=startIndex))
        startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
    print awayStarters[-1]
    
# get home team starters!
homeStarters = []
startIndex=0
while homeLineup.find('<p>', startIndex) > -1:
    homeStarters.append(dict())
    
    startTag = "<p>"    
    endTag = "</p>"
    homeStarters[-1][statAbbrevs[0]] = getContents(homeLineup, startTag, endTag, start=startIndex)
    startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"
    endTag = "</td>"
    homeStarters[-1][statAbbrevs[1]] = int(getContents(homeLineup, startTag, endTag, start=startIndex))
    startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"    
    endTag = "</td>"
    homeStarters[-1][statAbbrevs[2]] = parsePlayer(getContents(homeLineup, startTag, endTag, start=startIndex))
    startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    for statLoop in range(3, len(statAbbrevs)):
        startTag = "<td>"        
        endTag = "</td>"
        homeStarters[-1][statAbbrevs[statLoop]] = parseStat(getContents(homeLineup, startTag, endTag, start=startIndex))
        startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
    print homeStarters[-1]

# get away team subs!
awaySubs = []
startIndex=0
while awayLineup.find('<p>', startIndex) > -1:
    awaySubs.append(dict())
    
    startTag = "<p>"    
    endTag = "</p>"
    awaySubs[-1][statAbbrevs[0]] = getContents(awayLineup, startTag, endTag, start=startIndex)
    startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"
    endTag = "</td>"
    awaySubs[-1][statAbbrevs[1]] = int(getContents(awayLineup, startTag, endTag, start=startIndex))
    startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"    
    endTag = "</td>"
    awaySubs[-1][statAbbrevs[2]] = parsePlayer(getContents(awayLineup, startTag, endTag, start=startIndex))
    startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    for statLoop in range(3, len(statAbbrevs)):
        startTag = "<td>"        
        endTag = "</td>"
        awaySubs[-1][statAbbrevs[statLoop]] = parseStat(getContents(awayLineup, startTag, endTag, start=startIndex))
        startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
    print awaySubs[-1]
    
# get home team subs!
homeSubs = []
startIndex=0
while homeLineup.find('<p>', startIndex) > -1:
    homeSubs.append(dict())
    
    startTag = "<p>"    
    endTag = "</p>"
    homeSubs[-1][statAbbrevs[0]] = getContents(homeLineup, startTag, endTag, start=startIndex)
    startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"
    endTag = "</td>"
    homeSubs[-1][statAbbrevs[1]] = int(getContents(homeLineup, startTag, endTag, start=startIndex))
    startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    startTag = "<td>"    
    endTag = "</td>"
    homeSubs[-1][statAbbrevs[2]] = parsePlayer(getContents(homeLineup, startTag, endTag, start=startIndex))
    startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    for statLoop in range(3, len(statAbbrevs)):
        startTag = "<td>"        
        endTag = "</td>"
        homeSubs[-1][statAbbrevs[statLoop]] = parseStat(getContents(homeLineup, startTag, endTag, start=startIndex))
        startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
    print homeSubs[-1]

        