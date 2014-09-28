import urllib2
import os
from bs4 import BeautifulSoup # donwload here: http://www.crummy.com/software/BeautifulSoup/#Download
from datetime import datetime
import re
import json

# this is a good utility function for getting text between two tags
def getContents(htmlText, startTag, endTag, start=0, end=-1, brkTag=[]):
    if end == -1:
        end = len(htmlText)
    startIndex = htmlText.find(startTag, start, end) + len(startTag)
    endIndex = htmlText.find(endTag, startIndex)
    if startIndex == -1 or endIndex == -1:
        return ""
    else:
        if not brkTag or (brkTag and htmlText.find(brkTag, startIndex, endIndex) == -1):
            return htmlText[startIndex:endIndex]
        else:
            return ""

# parses a string containing a player (a little complicated) into a (ID, name) tuple 
def parsePlayer(linkText): # link text of the form <a href = ...>Player Name</a>
    playerName = getContents(linkText, ">", "</a")
    playerID = int(getContents(linkText, '<a href="/player/', "/"))
    return (playerID, playerName)
    
# parses stats from the table, handles the "-"s, which are registered as zeros
def parseStat(statText):
    statText = statText.strip()
    if statText is "-":
        return 0
    else:
        return int(statText)

# parses player numbers from the table, handles the "-"s, which are registered as -1
def parseNum(numText):
    numText = numText.strip()
    if numText is "-":
        return -1
    else:
        return int(numText)

# parse substitution information, returns () if no sub,  
def parseSub(subText):
    if not subText:
        return ()
    minutes = int(re.findall(r"[0-9]+", getContents(subText, "<strong>Substitution</strong> - ", "\'"))[0])
    subfor = getContents(subText, "Off: ", "');")
    return (minutes, subfor)

# os.path.join
dropboxPath = "C:\Users\Matt\Documents\Dropbox\Sports Project\CrawlData"

# started from 395707 and counted down
for page_id in range(394910, 394909, -1):

    print "********************"
    
    page_id_string = str(page_id).zfill(6)
    print page_id_string
    
    urlString = "http://www.espnfc.co.uk/gamecast/statistics/id/" + page_id_string + "/statistics.html"
    response = urllib2.urlopen(urlString)
    page_source = response.read()
    soup = BeautifulSoup(page_source)
    
    # get team names
    awayTeam = getContents(page_source, '<h1 id="away-team" class="heading alt">', '</h1>')
    homeTeam = getContents(page_source, '<h1 id="home-team" class="heading alt">', '</h1>')
    leagueName = getContents(page_source, '<p class="floatleft">', "<span>").strip() # no clue why this is the only match
    
    if not soup.title.string.find(awayTeam + " v " + homeTeam) > -1 and not soup.title.string.find(homeTeam + " v " + awayTeam) > -1:
        print "Not a match!"
        continue
    else:
        print awayTeam + ' @ '+homeTeam + ", " + leagueName
        
    # match date
    matchDate = getContents(page_source, "= new Date(", ")")
    matchDate = datetime.utcfromtimestamp(int(matchDate) / 1000)
    matchDateStr = matchDate.strftime("%Y-%m-%d, %H:%M")
    print matchDateStr
        
    # get stat column titles, this is the only place that I use the BeautifulSoup object
    statAbbrevs = []
    statTitles = dict()
    for tag in soup.find_all("tr"):
        if tag.th and tag.prettify().find("pstat") > -1:
            statList = tag.find_all('th')
            for stat in statList:
                statAbbrevs.append(stat.text.strip())
                if stat.has_attr("title"):
                    statTitles[statAbbrevs[-1]] = stat.attrs["title"]
                else:
                    statTitles[statAbbrevs[-1]] = statAbbrevs[-1]
            break
    statTitles["Sub"] = "Substitution (Min, Name)" # substitution labels
    statTitles["Started"] = "Started" # started bool
    
    # get the indices to search from
    awayIndex = page_source.find('<h1 id="away-team" class="heading alt">')
    homeIndex = page_source.find('<h1 id="home-team" class="heading alt">')
    
    # get the away lineup and subs
    awayLineup = getContents(page_source, '<td class="first">', 'Substitutes', start=awayIndex)
    awaySubLineup = getContents(page_source, 'Substitutes', '</table>', start=awayIndex)
    
    # get the home lineup and subs
    homeLineup = getContents(page_source, '<td class="first">', 'Substitutes', start=homeIndex)
    homeSubLineup = getContents(page_source, 'Substitutes', '</table>', start=homeIndex)
    
    # get away team starters!
    awayStarters = []
    startIndex=0
    while awayLineup.find('<p>', startIndex) > -1:
        awayStarters.append(dict())
        awayStarters[-1]["Started"] = True
        
        # parse position
        startTag = "<p>"    
        endTag = "</p>"
        awayStarters[-1][statAbbrevs[0]] = getContents(awayLineup, startTag, endTag, start=startIndex)
        startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse number
        startTag = "<td>"
        endTag = "</td>"
        awayStarters[-1][statAbbrevs[1]] = parseNum(getContents(awayLineup, startTag, endTag, start=startIndex))
        startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse player name + id (espn.fc.co.uk ID)
        startTag = "<td>"    
        endTag = "</td>"
        awayStarters[-1][statAbbrevs[2]] = parsePlayer(getContents(awayLineup, startTag, endTag, start=startIndex))
        startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # this player did not sub in        
        awayStarters[-1]["Sub"] = ()
        
        # parse the scoring stats
        for statLoop in range(3, len(statAbbrevs)):
            startTag = "<td>"        
            endTag = "</td>"
            awayStarters[-1][statAbbrevs[statLoop]] = parseStat(getContents(awayLineup, startTag, endTag, start=startIndex))
            startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
    # get home team starters!
    homeStarters = []
    startIndex=0
    while homeLineup.find('<p>', startIndex) > -1:
        homeStarters.append(dict())
        homeStarters[-1]["Started"] = True
        
        # parse position        
        startTag = "<p>"    
        endTag = "</p>"
        homeStarters[-1][statAbbrevs[0]] = getContents(homeLineup, startTag, endTag, start=startIndex)
        startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse number
        startTag = "<td>"
        endTag = "</td>"
        homeStarters[-1][statAbbrevs[1]] = parseNum(getContents(homeLineup, startTag, endTag, start=startIndex))
        startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse player info
        startTag = "<td>"    
        endTag = "</td>"
        homeStarters[-1][statAbbrevs[2]] = parsePlayer(getContents(homeLineup, startTag, endTag, start=startIndex))
        startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # this player did not sub in
        homeStarters[-1]["Sub"] = ()
        
        # parse individual scoring stats
        for statLoop in range(3, len(statAbbrevs)):
            startTag = "<td>"        
            endTag = "</td>"
            homeStarters[-1][statAbbrevs[statLoop]] = parseStat(getContents(homeLineup, startTag, endTag, start=startIndex))
            startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    # get away team subs!
    awaySubs = []
    startIndex=0
    while awaySubLineup.find('<p>', startIndex) > -1:
        awaySubs.append(dict())
        awaySubs[-1]["Started"] = False
        
        # parse position        
        startTag = "<p>"    
        endTag = "</p>"
        awaySubs[-1][statAbbrevs[0]] = getContents(awaySubLineup, startTag, endTag, start=startIndex)
        startIndex = awaySubLineup.find(endTag, awaySubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse number
        startTag = "<td>"
        endTag = "</td>"
        awaySubs[-1][statAbbrevs[1]] = parseNum(getContents(awaySubLineup, startTag, endTag, start=startIndex))
        startIndex = awaySubLineup.find(endTag, awaySubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse player name and ID
        startTag = "<td>"    
        endTag = "</td>"
        awaySubs[-1][statAbbrevs[2]] = parsePlayer(getContents(awaySubLineup, startTag, endTag, start=startIndex))
        
        # parse sub information if it exists    
        startTag = '<div '
        endTag = "</div>"
        breakTag = "</td>"# this can be used to say "there is no content here
        awaySubs[-1]["Sub"] = parseSub(getContents(awaySubLineup, startTag, endTag, start=startIndex, brkTag=breakTag))
        startIndex = awaySubLineup.find(breakTag, startIndex) + len(breakTag)
        
        # parse individual scoring stats
        for statLoop in range(3, len(statAbbrevs)):
            startTag = "<td>"        
            endTag = "</td>"
            awaySubs[-1][statAbbrevs[statLoop]] = parseStat(getContents(awaySubLineup, startTag, endTag, start=startIndex))
            startIndex = awaySubLineup.find(endTag, awaySubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
    # get home team subs!
    homeSubs = []
    startIndex=0
    while homeSubLineup.find('<p>', startIndex) > -1:
        homeSubs.append(dict())
        homeSubs[-1]["Started"] = False
        
        # parse position        
        startTag = "<p>"    
        endTag = "</p>"
        homeSubs[-1][statAbbrevs[0]] = getContents(homeSubLineup, startTag, endTag, start=startIndex)
        startIndex = homeSubLineup.find(endTag, homeSubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse number
        startTag = "<td>"
        endTag = "</td>"
        homeSubs[-1][statAbbrevs[1]] = parseNum(getContents(homeSubLineup, startTag, endTag, start=startIndex))
        startIndex = homeSubLineup.find(endTag, homeSubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
        # parse player information
        startTag = "<td>"    
        endTag = "</td>"
        homeSubs[-1][statAbbrevs[2]] = parsePlayer(getContents(homeSubLineup, startTag, endTag, start=startIndex))
            
        # parse sub information if it exists    
        startTag = '<div '
        endTag = "</div>"
        breakTag = "</td>"# this can be used to say "there is no content here
        homeSubs[-1]["Sub"] = parseSub(getContents(homeSubLineup, startTag, endTag, start=startIndex, brkTag=breakTag))
        startIndex = homeSubLineup.find(breakTag, startIndex) + len(breakTag)
        
        # parse individual scoring stats        
        for statLoop in range(3, len(statAbbrevs)):
            startTag = "<td>"        
            endTag = "</td>"
            homeSubs[-1][statAbbrevs[statLoop]] = parseStat(getContents(homeSubLineup, startTag, endTag, start=startIndex))
            startIndex = homeSubLineup.find(endTag, homeSubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
    
    # create the json object for writing
    jsonData = dict()
    jsonData["League"] = leagueName
    jsonData["Home Team"] = homeTeam
    jsonData["Away Team"] = awayTeam
    jsonData["Game Date, Time"] = matchDateStr
    jsonData["Stat Abbreviations"] = statTitles
    jsonData["Home Players"] = homeStarters
    jsonData["Home Players"].extend(homeSubs)
    jsonData["Away Players"] = awayStarters
    jsonData["Away Players"].extend(awaySubs)
    jsonData["Away Score"] = sum([player["G"] for player in jsonData["Away Players"]])
    jsonData["Home Score"] = sum([player["G"] for player in jsonData["Home Players"]])
    
    # write everything to a json
    filename = matchDate.strftime("%Y-%m-%d_%H%M") + "_" + (awayTeam + " at " + homeTeam).replace(" ", "-") + ".json"
    
    # make sure the file structure exists
    if not os.path.exists(os.path.join(dropboxPath, leagueName, str(matchDate.year))):
        if not os.path.exists(os.path.join(dropboxPath, leagueName)):
            os.mkdir(os.path.join(dropboxPath, leagueName))
        os.mkdir(os.path.join(dropboxPath, leagueName, str(matchDate.year)))
        
    # write the json
    with open(os.path.join(dropboxPath, leagueName, str(matchDate.year), filename), 'w') as outfile:
        json.dump(jsonData, outfile)
        print "Wrote JSON " + filename + " successfully!"
        
    csvEntry = page_id_string + "," + leagueName + "," + awayTeam + "," + homeTeam + "," + matchDate.strftime("'%Y-%m-%d %H:%M'") + ",'" + str(jsonData["Away Score"]) + "-" + str(jsonData["Home Score"]) + "'," + os.path.join(leagueName, str(matchDate.year), filename) + "\n"
    with open(os.path.join(dropboxPath, "MatchesExtracted.csv"), 'a') as csvwriter:
        csvwriter.write(csvEntry)
        print "Wrote entry into MatchesExtracted.csv successfully!"    
    