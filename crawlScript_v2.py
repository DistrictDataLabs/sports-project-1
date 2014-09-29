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
    if startIndex == (len(startTag) - 1) or endIndex == -1:
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
    if not statText or statText == "-":
        return 0
    else:
        return int(statText)

# parses player numbers from the table, handles the "-"s, which are registered as -1
def parseNum(numText):
    numText = numText.strip()
    if not numText or numText is "-":
        return -1
    else:
        return int(numText)
        
# parse substitution information, returns () if no sub,  
def parseSub(subText):
    if not subText:
        return ()
    minutes = getContents(subText, "<strong>Substitution</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    subfor = getContents(subText, "Off: ", "');")
    return (minutes, subfor)

# parse yellow card timing, returns "" if none 
def parseYellowCard(cardText):
    if not cardText:
        return ""
    minutes = getContents(cardText, "<strong>Yellow Card</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    return minutes
    
# parse red card timing, returns "" if none  
def parseRedCard(cardText):
    if not cardText:
        return ""
    minutes = getContents(cardText, "<strong>Red Card</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    return minutes
    
# parse own goal information, returns "" if none  
def parseOwnGoal(goalText):
    if not goalText:
        return ""
    minutes = getContents(goalText, "<strong>Own Goal</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    return minutes
    
# parse own goal information, returns "" if none  
def parseGoal(goalText):
    if not goalText:
        return ""
    minutes = getContents(goalText, "<strong>Goal</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    return minutes
    
# parse own goal information, returns "" if none  
def parseGoalHeader(goalText):
    if not goalText:
        return ""
    minutes = getContents(goalText, "<strong>Goal - Header</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    return minutes
    
def parsePenaltyScored(goalText):
    if not goalText:
        return ""
    minutes = getContents(goalText, "<strong>Penalty - Scored</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)[0]
    return minutes
    
def parseGenericIcon(iconText):
    if not iconText:
        return ""
    iconType = getContents(iconText, "<strong>", "</strong>")
    minutes = getContents(iconText, "<strong>" + iconType + "</strong> - ", "\'")
    minutes = re.findall(r"[0-9]+(?: \+ [0-9]+)*", minutes)
    if minutes and iconType:
        return [(iconType, minutes[0])]
    else:
        return []
    
def parseIcons(postLinkText):
    startIndex = 0
    iconInfo = [(), (), (), (), (), (), (), []]
    while postLinkText.find("<div class=", startIndex) > -1:
        iconType = getContents(postLinkText, "<strong>", "</strong>", start=startIndex)
        if iconType == "Substitution":
            iconInfo[0] = parseSub(postLinkText[startIndex:])
        elif iconType == "Goal":
            iconInfo[1] += (parseGoal(postLinkText[startIndex:]),)
        elif iconType == "Own Goal":
            iconInfo[2] += (parseOwnGoal(postLinkText[startIndex:]),)
        elif iconType == "Red Card":
            iconInfo[3] += (parseRedCard(postLinkText[startIndex:]),)
        elif iconType == "Yellow Card":
            iconInfo[4] += (parseYellowCard(postLinkText[startIndex:]),)
        elif iconType == "Goal - Header":
            iconInfo[5] += (parseGoalHeader(postLinkText[startIndex:]),)
        elif iconType == "Penalty - Scored":
            iconInfo[6] += (parsePenaltyScored(postLinkText[startIndex:]),)
        else:
            iconInfo[7] += parseGenericIcon(postLinkText[startIndex:])
        endTag = '</div>'
        startIndex = postLinkText.find(endTag, startIndex) + len(endTag)
        
    return iconInfo

# os.path.join
dropboxPath = "C:\Users\Matt\Documents\Dropbox\Sports Project\CrawlData"

# started from 403000 and counted down
# score glitch at 402659
for page_id in range(403000, 100000, -1):

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
    
    if not homeTeam or not awayTeam:
        print "Not a match!"
        continue
    else:
        print awayTeam + ' @ '+homeTeam + ", " + leagueName
        
    # match date
    matchDate = getContents(page_source, "= new Date(", ")")
    matchDate = datetime.utcfromtimestamp(int(matchDate) / 1000)
    matchDateStr = matchDate.strftime("%Y-%m-%d, %H:%M")
    print matchDateStr
    
    if matchDate > datetime.now(): # this isn't exact / time-zone proof
        print "Match hasn't happened yet!"
        continue
    
    # get the match score, a little tricky
    matchScore = re.findall(r"[0-9]+ - [0-9]+", getContents(getContents(page_source, '<div class="score-time">', '</div>'), '<p class="score">', '</p>'))
    if not matchScore:
        print "Match didn't have a score!"
        continue        
    matchScore = [int(score) for score in matchScore[0].split('-')]
    if page_source.find('class="team away"') > page_source.find('class="team home"'):
        matchScore = (matchScore[1], matchScore[0])
        
    # get the match time, i.e., full-time, over time, etc.
    matchDuration = getContents(getContents(page_source, '<div class="score-time">', '</div>'), '<p class="time">', '</p>')
    
    # print the match score and duration
    print str(matchScore[0]) + "-" + str(matchScore[1]) + ", " + matchDuration
       
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
    
    # some extra labels that are not in the title    
    statTitles["Sub"] = "Substitution (Min, Name)" # substitution labels
    statTitles["Started"] = "Started" # started bool
    statTitles["OG"] = "Own Goals"
    statTitles["GT"] = "Goal Times"
    statTitles["GH"] = "Header Goals"
    statTitles["GHT"] = "Header Goal Times"
    statTitles["YCT"] = "Yellow Card Times"
    statTitles["RCT"] = "Red Card Times"
    statTitles["OGT"] = "Own Goal Times"
    statTitles["PG"] = "Penalty Goals"
    statTitles["PGT"] = "Penalty Goal Times"
    statTitles["Misc"] = "Other Events"
    
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
        
        # parse icon information next to this player
        iconsText = getContents(awayLineup, '</a>', '</td>', start=startIndex)
        iconsTuple = parseIcons(iconsText)
        awayStarters[-1]["Sub"] = iconsTuple[0]
        awayStarters[-1]["GT"] = iconsTuple[1]
        awayStarters[-1]["OGT"] = iconsTuple[2]
        awayStarters[-1]["OG"] = len(iconsTuple[2])
        awayStarters[-1]["RCT"] = iconsTuple[3]
        awayStarters[-1]["YCT"] = iconsTuple[4]
        awayStarters[-1]["HG"] = len(iconsTuple[5])
        awayStarters[-1]["HGT"] = iconsTuple[5]
        awayStarters[-1]["PG"] = len(iconsTuple[6])
        awayStarters[-1]["PGT"] = iconsTuple[6]
        awayStarters[-1]["Misc"] = iconsTuple[7]
        
        # advance the startIndex
        startIndex = awayLineup.find(endTag, awayLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
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

        # parse icon information next to this player
        iconsText = getContents(homeLineup, '</a>', '</td>', start=startIndex)
        iconsTuple = parseIcons(iconsText)
        homeStarters[-1]["Sub"] = iconsTuple[0]
        homeStarters[-1]["GT"] = iconsTuple[1]
        homeStarters[-1]["OGT"] = iconsTuple[2]
        homeStarters[-1]["OG"] = len(iconsTuple[2])
        homeStarters[-1]["RCT"] = iconsTuple[3]
        homeStarters[-1]["YCT"] = iconsTuple[4]
        homeStarters[-1]["HG"] = len(iconsTuple[5])
        homeStarters[-1]["HGT"] = iconsTuple[5]
        homeStarters[-1]["PG"] = len(iconsTuple[6])
        homeStarters[-1]["PGT"] = iconsTuple[6]
        homeStarters[-1]["Misc"] = iconsTuple[7]
        
        # advance the startIndex
        startIndex = homeLineup.find(endTag, homeLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
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
        
        # parse icon information next to this player
        iconsText = getContents(awaySubLineup, '</a>', '</td>', start=startIndex)
        iconsTuple = parseIcons(iconsText)
        awaySubs[-1]["Sub"] = iconsTuple[0]
        awaySubs[-1]["GT"] = iconsTuple[1]
        awaySubs[-1]["OGT"] = iconsTuple[2]
        awaySubs[-1]["OG"] = len(iconsTuple[2])
        awaySubs[-1]["RCT"] = iconsTuple[3]
        awaySubs[-1]["YCT"] = iconsTuple[4]
        awaySubs[-1]["HG"] = len(iconsTuple[5])
        awaySubs[-1]["HGT"] = iconsTuple[5]
        awaySubs[-1]["PG"] = len(iconsTuple[6])
        awaySubs[-1]["PGT"] = iconsTuple[6]
        awaySubs[-1]["Misc"] = iconsTuple[7]
        
        # advance the startIndex
        startIndex = awaySubLineup.find(endTag, awaySubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
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
            
        # parse icon information next to this player
        iconsText = getContents(homeSubLineup, '</a>', '</td>', start=startIndex)
        iconsTuple = parseIcons(iconsText)
        homeSubs[-1]["Sub"] = iconsTuple[0]
        homeSubs[-1]["GT"] = iconsTuple[1]
        homeSubs[-1]["OGT"] = iconsTuple[2]
        homeSubs[-1]["OG"] = len(iconsTuple[2])
        homeSubs[-1]["RCT"] = iconsTuple[3]
        homeSubs[-1]["YCT"] = iconsTuple[4]
        homeSubs[-1]["HG"] = len(iconsTuple[5])
        homeSubs[-1]["HGT"] = iconsTuple[5]
        homeSubs[-1]["PG"] = len(iconsTuple[6])
        homeSubs[-1]["PGT"] = iconsTuple[6]
        homeSubs[-1]["Misc"] = iconsTuple[7]
        
        # advance the startIndex
        startIndex = homeSubLineup.find(endTag, homeSubLineup.find(startTag, startIndex) + len(startTag)) + len(endTag)
        
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
    jsonData["Match Score (A-H)"] = matchScore
    jsonData["Match Duration"] = matchDuration
    jsonData["Home Offensive Goals"] = sum([player["G"] for player in jsonData["Home Players"]])
    jsonData["Away Offensive Goals"] = sum([player["G"] for player in jsonData["Away Players"]])
    
    # write everything to a json
    filename = matchDate.strftime("%Y-%m-%d_%H%M") + "_" + (awayTeam + " at " + homeTeam).replace(" ", "-").replace("/", "_") + ".json"
    
    # make sure the file structure exists
    if not os.path.exists(os.path.join(dropboxPath, leagueName, str(matchDate.year))):
        if not os.path.exists(os.path.join(dropboxPath, leagueName)):
            os.mkdir(os.path.join(dropboxPath, leagueName))
        os.mkdir(os.path.join(dropboxPath, leagueName, str(matchDate.year)))
        
    # write the json
    with open(os.path.join(dropboxPath, leagueName, str(matchDate.year), filename), 'w') as outfile:
        json.dump(jsonData, outfile)
        print "Wrote JSON " + filename
        
    csvEntry = page_id_string + "," + leagueName + "," + awayTeam + " @ " + homeTeam + "," + matchDate.strftime("'%Y-%m-%d %H:%M'") + ",'" + str(matchScore[0]) + "-" + str(matchScore[1]) + "'," + os.path.join(leagueName, str(matchDate.year), filename) + "," + str(len(jsonData["Home Players"]) + len(jsonData["Away Players"])) + " Players' Info\n"
    with open(os.path.join(dropboxPath, "MatchesExtracted.csv"), 'a') as csvwriter:
        csvwriter.write(csvEntry)
        print "Wrote entry into MatchesExtracted.csv"    
    