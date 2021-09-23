import irc.bot
import requests
import json
import sqlite3
import sys
import logging
import os

if not os.path.exists('logs'):
    os.makedirs('logs')

cid = sys.argv[1]
tokena = sys.argv[2]
usern = sys.argv[3]
chan = sys.argv[4]
ctoken = sys.argv[5]

logging.basicConfig(filename='logs/' + chan + '.log', format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('Username: ' + usern)
logging.info('Channel: ' + chan)

conn = sqlite3.connect('bannedusers.db')
twitchHeaders = {'Authorization': 'Bearer ' + tokena, 'Client-Id': cid, 'Accept': 'application/json'}

def createtable():
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS ' + chan + ' (uid TEXT NOT NULL UNIQUE)')
    conn.commit()
    return 0

def isuserloginindb(ida):
    cur = conn.cursor()
    sql = """SELECT rowid FROM BANNED WHERE LOGIN = ?;"""
    cur.execute(sql, (ida,))
    data = cur.fetchone()
    if data is None:
        return False
    else:
        return True

def isusrremoved():
    blist = []
    cur = conn.cursor()
    cur.execute('SELECT uid FROM ' + chan)
    resulta = cur.fetchall()
    for i in resulta:
        blist.append(str(i))

    if len(resulta) > 0:
        for id in resulta:
            if isuserloginindb(id):
                junk = None
            else:
                cur.execute("DELETE FROM " + chan + " WHERE uid = '" + id + "'")
                conn.commit()
                c.privmsg(self.channel, '/unban ' + id)
                logging.warning(id + ' is no longer in the CommanderRoot Blocklist. Ban removed')
    return 0

def addtoblocklist(id):
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO ' + chan + ' (uid) VALUES (' + id + ')')
    conn.commit()
    return 0

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/helix/users?login=' + channel
        r = requests.get(url, headers=twitchHeaders)
        self.channel_id = json.loads(r.text)['data'][0]['id']

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        logging.info('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:' + token)], username, username)

    def on_welcome(self, c, e):
        logging.info('Joining ' + self.channel)

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_join(self, c, e):
        usrid = e.source.split('!')[0]
        isusrremoved()
        if isuserloginindb(usrid):
            logging.warning(usrid + ' In CommanderRoot BlockList, banning.')
            c.privmsg(self.channel, '/ban ' + usrid + 'This Username has been identified in the CommanderRoot Blocklist. If you feel this is in error please contact CommanderRoot on Twitter to have your ID removed from the list. Once we update our copy of the list your account will be unbanned if it has been removed.')
            addtoblocklist(usrid)
        else:
            logging.info(usrid + ' is safe.')

createtable()
bot = TwitchBot(usern, cid, ctoken, chan)
bot.start()
