import re,json,sqlite3,requests,time, os, logging, urllib.parse
from datetime import datetime
from functools import reduce

now = datetime.now()
timestamp=now.strftime("%Y-%m-%d-%H-%M-%S")

conn = sqlite3.connect('cards.db')
c = conn.cursor()

#setup logging. Info+higher goes to the console. Debug+higher goes to file. not working right now? debug not going to file
logger = logging.getLogger('collection')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('output.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

blackList = {"Plains", "Island", "Mountain", "Swamp", "Forest", "BADCARD", "Shadowspear", "Shorecomber Crab"}



def readDeckList(filePath):
  file = open(filePath, "r")
  returnSet=set()
  cardName=""
  for line in file:
    strippedLine=line.split(" (")[0].strip("\n")
    if strippedLine == "Deck":
      pass
    elif strippedLine.split(" ")[0].isdigit(): # first characters are digits
      returnSet.add(strippedLine.split(" ", 1)[1].strip('\n'))
    else:
      returnSet.add(strippedLine.strip('\n'))
  return returnSet

def writeList(passedList, filePrefix):
  fileName="files/"+filePrefix+"-"+timestamp+".txt"
  f = open(fileName, "w")
  for line in passedList:
    f.write(line + '\n') 
  logger.info("writing cube " + fileName)

def writeDeckList(passedList, filePrefix):
  fileName="files/"+filePrefix+"-"+timestamp+".txt"
  f = open(fileName, "w")
  for line in passedList:
    f.write("1 " + line + '\n') 
  logger.info("writing cube " + fileName)

def writeCubeCobra(passedList, filePrefix):
  fileName="files/"+filePrefix+"-"+timestamp+".txt"
  f = open(fileName, "w")
  for line in passedList:
    f.write(line.split(' //')[0] + '\n') # cube cobra doesn't like split cards. so writing with just the first part. 
  logger.info("writing cube " + fileName)

def getScryfallInfo(cardId):
  scryfalltxt=requests.get('https://api.scryfall.com/cards/arena/' + str(cardId))
  cardname="BADCARD"
  rarity="NONE"
  if scryfalltxt.json()["object"] == "card":
    cardname=scryfalltxt.json()["name"]
    rarity=scryfalltxt.json()["rarity"]
    if scryfalltxt.json()["layout"] == "modal_dfc":
      cardname=cardname.split(' //')[0]
  return [cardname, rarity]

def getInfoFromPlayerLog():
  path=os.environ['USERPROFILE'] + "\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log"
  file = open(path, "r")
  inventoryKeyword="PlayerInventory.GetPlayerCardsV3"
  playerNameKeyword="Updated account. DisplayName"
  for line in file:
    if re.search(r"%s\b" % re.escape(inventoryKeyword), line):
      lastCatalogLine=line
    if re.search(r"%s\b" % re.escape(playerNameKeyword), line):
      lastLoginLine=line
  user=lastLoginLine.split("DisplayName:")[1].split('#')[0]
  catalog=json.loads('{' + lastCatalogLine.split('{')[2].split('}')[0] + '}')
  return [user,catalog]

def updateCollection(playerInfo):
  for idval in playerInfo[1].keys():
    if c.execute('''SELECT COUNT(*) FROM cardInfo WHERE cardId = "%s"''' %idval).fetchone()[0] == 0: # card is not in db. can't use an insert unique constraint since we need to look up scryfall if it's not present.
      scryfallInfo=getScryfallInfo(idval)
      if scryfallInfo[0] == "BADCARD":
        logger.warning("ERROR: grabbing data for " + idval)
      c.execute('''INSERT INTO cardInfo VALUES (?,?,?)''', (idval,scryfallInfo[0],scryfallInfo[1]))
        
    cardValues=c.execute('''SELECT cardName FROM cardInfo WHERE cardId = "%s"''' %idval).fetchall()
    cardname=cardValues[0][0]
    try:
      c.execute('''INSERT INTO cardOwners VALUES (?,?)''', (playerInfo[0],cardname))
    except:
      pass #catches unique error. card already existed in table. no further action required
    else:
      logger.info("Adding " + cardname + " to owner " + playerInfo[0])
      conn.commit()

def getUsersCards(passedUser): # passedUser is a string
  return {x[0] for x in c.execute('''SELECT cardName FROM cardOwners WHERE userName = "%s"''' %passedUser).fetchall()} - blackList


def getCardsByRarity(cardRarity):
  return {x[0] for x in c.execute('''SELECT cardName FROM cardInfo WHERE cardRarity = "%s"''' %cardRarity).fetchall()} - blackList

updateCollection(getInfoFromPlayerLog())

