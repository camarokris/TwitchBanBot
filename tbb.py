import configparser
import irc.bot
import irc.client
import requests
import json
import sqlite3
import sys
import logging
import os
from time import sleep

import tempora.schedule
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
import irc.schedule

if not os.path.exists('logs'):
    os.makedirs('logs')

config = configparser.ConfigParser()
config.read('config.ini')
cid = config['TWITCH']['ClientID']
csec = config['TWITCH']['ClientSecret']
chans = config['TWITCH']['Channels'].replace(' ', '').split(',')
usern = config['TWITCH']['Username']
ctoken = config['TWITCH']['TMIPass']
conn = sqlite3.connect('bannedusers.db')

twitch = Twitch(cid, csec, target_app_auth_scope=[AuthScope.BITS_READ, AuthScope.MODERATION_READ,
                                                  AuthScope.USER_READ_BLOCKED_USERS, AuthScope.CHAT_EDIT,
                                                  AuthScope.CHAT_READ])
url = "https://id.twitch.tv/oauth2/token?client_id=7ne11ngtwmae816wl6nazhfkxctsbd&client_secret=1t5nsbxmzmt4ps1708txe322qe4kva&grant_type=client_credentials&scope=chat:edit chat:read channel:moderate moderation:read user:read:follows bits:read user:read:blocked_users"
rj = requests.post(url).json()
token = rj['access_token']
twitchHeaders = {'Authorization': 'Bearer ' + token, 'Client-Id': cid, 'Accept': 'application/json'}

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
    sql = """SELECT rowid FROM BANNED WHERE LOGIN = ?"""
    if isinstance(ida, tuple):
        cur.execute(sql, ida)
    else:
        cur.execute(sql, (ida,))
    data = cur.fetchone()
    if data is None:
        return False
    else:
        return True

def addtoblocklist(id):
    cur = conn.cursor()
    sql = 'INSERT OR REPLACE INTO ' + chan + ' (uid) VALUES (?)'
    cur.execute(sql, (id,))
    conn.commit()
    return 0

def checkfollowersforbots(self, c, e):
    userinformation = twitch.get_users(logins=chan)
    pag = ""
    ctr = 0
    logging.warning('Checking followers for bots and banning')
    while True:
        if len(pag) > 0:
            foll = twitch.get_users_follows(first=100, to_id=userinformation['data'][0]['id'], after=pag)
        else:
            foll = twitch.get_users_follows(first=100, to_id=userinformation['data'][0]['id'])
        for a in range(len(foll['data'])):
            ctr += 1
            badactor = foll['data'][a]['from_login']
            if isuserloginindb(badactor):
                c.privmsg(self.channel, '/ban ' + badactor + 'This Username has been identified in the CommanderRoot Blocklist. If you feel this is in error please contact CommanderRoot on Twitter to have your ID removed from the list. Once we update our copy of the list your account will be unbanned if it has been removed.')
                addtoblocklist(badactor)
                logging.warning(badactor + ' is Following ' + chan + ' AND has been banned')
        if len(foll['pagination']) > 0:
            pag = foll['pagination']['cursor']
        else:
            break
    print('Processed ' + str(ctr) + ' followers for ' + chan)
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

    def checkfollowersforbotso(self, c, e):
        userinformation = twitch.get_users(logins=chan)
        pag = ""
        ctr = 0
        logging.warning('Checking followers for bots and banning')
        while True:
            if len(pag) > 0:
                foll = twitch.get_users_follows(first=100, to_id=userinformation['data'][0]['id'], after=pag)
            else:
                foll = twitch.get_users_follows(first=100, to_id=userinformation['data'][0]['id'])
            for a in range(len(foll['data'])):
                ctr += 1
                badactor = foll['data'][a]['from_login']
                if isuserloginindb(badactor):
                    c.privmsg(self.channel, '/ban ' + badactor + 'This Username has been identified in the CommanderRoot Blocklist. If you feel this is in error please contact CommanderRoot on Twitter to have your ID removed from the list. Once we update our copy of the list your account will be unbanned if it has been removed.')
                    addtoblocklist(badactor)
                    logging.warning(badactor + ' is Following ' + chan + ' AND has been banned')
            if len(foll['pagination']) > 0:
                pag = foll['pagination']['cursor']
            else:
                break
        print('Processed ' + str(ctr) + ' followers for ' + chan)
        return 0

    def isusrremoved(self, c, e):
        blist = []
        cur = conn.cursor()
        cur.execute('SELECT uid FROM ' + chan)
        resulta = cur.fetchall()
        for i in resulta:
            if isinstance(i, tuple):
                blist.append(str(i[0]))
            else:
                blist.append(str(i))

        if len(resulta) > 0:
            for id in resulta:
                if isuserloginindb(id):
                    junk = None
                else:
                    sql = """DELETE FROM """ + chan + """ WHERE uid = ?"""
                    cur.execute(sql, (id,))
                    conn.commit()
                    c.privmsg(self.channel, '/unban ' + id)
                    logging.warning(id + ' is no longer in the CommanderRoot Blocklist. Ban removed')
        return 0

    def on_welcome(self, c, e):
        logging.info('Joining ' + self.channel)

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        sleep(10)
        #self.reactor.scheduler.execute_every(60, func=checkfollowersforbots(self, c, e))
        #irc.schedule.IScheduler.execute_every(self, 60, checkfollowersforbots(self, c, e))
        checkfollowersforbots(self, c, e)

    def on_join(self, c, e):
        usrid = e.source.split('!')[0]
        self.isusrremoved(c, e)
        if isuserloginindb(usrid):
            logging.warning(usrid + ' In CommanderRoot BlockList, banning.')
            c.privmsg(self.channel, '/ban ' + usrid + 'This Username has been identified in the CommanderRoot Blocklist. If you feel this is in error please contact CommanderRoot on Twitter to have your ID removed from the list. Once we update our copy of the list your account will be unbanned if it has been removed.')
            addtoblocklist(usrid)
        else:
            logging.info(usrid + ' is safe.')

createtable()
bot = TwitchBot(usern, cid, ctoken, chan)
bot.start()
