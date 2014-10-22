import json, os, operator, glob

## scores seem to be reversed!
#def calcPlusMinusDumbV0(gameData):
#    plusMinuses = dict()
#    for player in gameData['Home Players']:
#        plusMinuses[player['Name'][1]] = gameData["Match Score (A-H)"][1] - gameData["Match Score (A-H)"][0]
#    for player in gameData['Away Players']:
#        plusMinuses[player['Name'][1]] = gameData["Match Score (A-H)"][0] - gameData["Match Score (A-H)"][1]
#    return plusMinuses

# this gives the starters equal contribution, can fix eventually
def calcPlusMinusDumb(gameData):
    plusMinuses = dict()
    for player in gameData['Home Players']:
        plusMinuses[player['Name'][1]] = (gameData["Home Offensive Goals"] - gameData["Away Offensive Goals"], 1)
    for player in gameData['Away Players']:
        plusMinuses[player['Name'][1]] = (gameData["Away Offensive Goals"] - gameData["Home Offensive Goals"], 1)
    return plusMinuses
    
# future directions:
# 1. fix this to actually be a game score
# 2. calculate using all but one game for prediction
# 3. create distribution for each player to sum / average for prediction
# 4. only use times that people are in the game + add subs
    
# sum the (+/-, # of games tuples)
def mergePlusMinus(x,y):
    return (x[0] + y[0], x[1] + y[1])
    
# get every file in the BARCLAYS
filepath = "C:\Users\Matt\Documents\Dropbox\Sports Project\CrawlData\BARCLAYS PREMIER LEAGUE"
filenames = glob.glob(os.path.join(filepath, "2014\*.json"))+glob.glob(os.path.join(filepath, "2013\*.json"))
totalPlusMinus = dict()
for filename in filenames:
    gameData = []
    with open(filename, 'r') as f:
        gameData = json.loads(f.read())
        
    plusMinusTemp = calcPlusMinusDumb(gameData)
    totalPlusMinus = { key: mergePlusMinus(plusMinusTemp.get(key, (0, 0)), totalPlusMinus.get(key, (0, 0))) for key in set( plusMinusTemp.keys() + totalPlusMinus.keys())}

totalPlusMinus = {key: totalPlusMinus[key][0] / float(totalPlusMinus[key][1]) for key in totalPlusMinus.keys()}
sortedPlusMinus = sorted(totalPlusMinus.items(), key=operator.itemgetter(1),reverse=True)
print sortedPlusMinus
