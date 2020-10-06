import sqlite3
conn = sqlite3.connect('cards.db')
c = conn.cursor()

print(c.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall())
c.execute("drop table cardInfo")
c.execute('CREATE TABLE "cardInfo" ("cardId" int,"cardName" text,"cardRarity" text,UNIQUE("cardId","cardName","cardRarity"))')
c.execute("drop table cardOwners")
c.execute('CREATE TABLE "cardOwners" ("userName" text,"cardName" text,UNIQUE("userName","cardName"))')
