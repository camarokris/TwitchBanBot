#!/usr/bin/env python3
import subprocess
import requests
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
import sqlite3
import configparser
import logging
import os
import time
import psutil
import sys

updatebl = 0
if len(sys.argv) > 1:
    if sys.argv[1] == 'ubl':
        updatebl = 1


def checkproc(user):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        if user.lower() in proc.info['cmdline']:
            return True


def createconfig(username, clientid, clientsec, monchans, tmioauth):
    conf = configparser.RawConfigParser()
    conf.add_section('TWITCH')
    conf.set('TWITCH', 'ClientID', clientid)
    conf.set('TWITCH', 'ClientSecret', clientsec)
    conf.set('TWITCH', 'TMIPass', tmioauth)
    conf.set('TWITCH', 'Channels', monchans)
    conf.set('TWITCH', 'Username', username)
    cfgfile = open('config.ini', 'w')
    conf.write(cfgfile, space_around_delimiters=False)
    cfgfile.close()


if not os.path.exists('logs'):
    os.makedirs('logs')

if not os.path.exists('config.ini'):
    myuser = input('Enter your Twitch usernamne: ')
    myapiid = input('Enter your Twitch API Client ID:')
    myapisec = input('Enter your Twitch API Client Secret: ')
    mymonchans = input('Enter the channels you wish to monitor [Comma separated no spaces]: ')
    print('GoTo https://twitchapps.com/tmi and get your chat oauth password')
    mytmipass = input('Copy the generated password and paste it here: ')
    if mytmipass.startswith('oauth:'):
        mytmipass = mytmipass[6:]
    createconfig(myuser, myapiid, myapisec, mymonchans, mytmipass)

logging.basicConfig(filename='logs/mainmessages.log', format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

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


def clear():
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')


def updateconfigchannels(chlist):
    conf = configparser.RawConfigParser()
    conf.read('config.ini')
    conf.set('TWITCH', 'Channels', chlist)
    cfgfile = open('config.ini', 'w')
    conf.write(cfgfile, space_around_delimiters=False)
    cfgfile.close()


def addbanneduser(ida, login, created):
    cur = conn.cursor()
    sql = """INSERT INTO BANNED (ID, LOGIN, CREATED) VALUES (?, ?, ?);"""
    data = (ida, login, created)
    cur.execute(sql, data)
    conn.commit()
    return 0


def adddeaduser(idb):
    cur = conn.cursor()
    sql = """INSERT OR REPLACE INTO DEAD (ID) VALUES (?);"""
    cur.execute(sql, (str(idb),))
    conn.commit()
    return 0


def isuseridindb(idc):
    cur = conn.cursor()
    sql = """SELECT rowid FROM BANNED WHERE ID = ?;"""
    cur.execute(sql, (str(idc),))
    data = cur.fetchone()
    curb = conn.cursor()
    sql = """SELECT rowid FROM DEAD WHERE ID = ?;"""
    curb.execute(sql, (str(idc),))
    datab = curb.fetchone()
    if data is None and datab is None:
        return False
    else:
        return True


def isuserloginindb(login):
    cur = conn.cursor()
    sql = """SELECT rowid FROM BANNED WHERE LOGIN = ?;"""
    cur.execute(sql, (login,))
    data = cur.fetchone()
    if data is None:
        return False
    else:
        return True


def totalbadassholes():
    cur = conn.cursor()
    sql = """SELECT COUNT(*) FROM BANNED;"""
    cur.execute(sql)
    cur_res = cur.fetchone()
    total = cur_res[0]
    sql = """SELECT COUNT(*) FROM DEAD;"""
    cur.execute(sql)
    cur_res = cur.fetchone()
    total = total + cur_res[0]
    return total


def updatebanlist():
    ctr = 0
    dctr = 0
    btotal = totalbadassholes()
    a = requests.get('https://twitch-tools.rootonline.de/blocklist_manager.php?preset=known_bot_users').json()
    for i in a:
        if isuseridindb(i):
            continue
        else:
            usr = twitch.get_users(user_ids=str(i))
            if len(usr['data']) == 0:
                dctr += 1
                print(str(i) + ' is no longer a valid user on Twitch, Skipping. Dead User Added = ' + str(dctr))
                logging.info(str(i) + ' is no longer a valid user on Twitch, Skipping. Dead User Added = ' + str(dctr))
                adddeaduser(i)
                continue
            idd = str(usr['data'][0]['id'])
            login = str(usr['data'][0]['login'])
            created = str(usr['data'][0]['created_at'])
            ctr += 1
            print('Count: ' + str(ctr) + ' | Adding ID: ' + idd + ' | Created On: ' + created + ' | LOGIN: ' + login)
            logging.info(
                'Count: ' + str(ctr) + ' | Adding ID: ' + idd + ' | Created On: ' + created + ' | LOGIN: ' + login)
            addbanneduser(idd, login, created)

    atotal = totalbadassholes()
    print('Total assholes before update in DB: ' + str(btotal))
    print('Total users added to BANNED table: ' + str(ctr))
    print('Total users added to DEAD table: ' + str(dctr))
    logging.info('Total users added to BANNED table: ' + str(ctr))
    logging.info('Total users added to DEAD table: ' + str(dctr))
    print('Total assholes after update in DB: ' + str(atotal))


def checkfollowersforbots(usr):
    usrnfo = twitch.get_users(logins=usr)
    pag = ""
    ctr = 0
    while True:
        if len(pag) > 0:
            foll = twitch.get_users_follows(first=100, to_id=usrnfo['data'][0]['id'], after=pag)
        else:
            foll = twitch.get_users_follows(first=100, to_id=usrnfo['data'][0]['id'])
        for a in range(len(foll['data'])):
            ctr += 1
            if isuserloginindb(foll['data'][a]['from_login']):
                print(foll['data'][a][
                          'from_login'] + ' is Following ' + usr + 'AND is in the local database as a bad account, '
                                                                   'consider banning this account')
        if len(foll['pagination']) > 0:
            pag = foll['pagination']['cursor']
        else:
            break
    print('Processed ' + str(ctr) + ' followers for ' + usr)


def startbanbot(cida, tokena, userna, cha, ctokena):
    if os.name == 'nt':
        totesmagoats = "python.exe tbb.py " + cida + " " + tokena + " " + userna + " " + cha + " " + ctokena
    else:
        totesmagoats = "python tbb.py " + cida + " " + tokena + " " + userna + " " + cha + " " + ctokena
    return totesmagoats


if updatebl == 1:
    updatebanlist()
    sys.exit()

for ch in chans:
    if checkproc(ch):
        continue
    else:
        cmd = startbanbot(cid, token, usern, ch, ctoken)
        p = subprocess.Popen(cmd, shell=True)

while True:
    clear()
    print('Choose an operation from the following list:')
    print('    1. Update local database from online master list')
    print('    2. Check followers of a user for accounts in DB')
    print('    3. Add another user to monitor their chat for bad accounts')
    print('    4. Check if user is in the DB')
    print('    5. Exit all processes')
    chosen = int(input('Choice: '))
    if chosen == 1:
        updatebanlist()
    elif chosen == 2:
        clear()
        chusr = input('Enter the user you wish to check the follower list of: ')
        print('Checking Follower List. This could take some time depending on amount of followers')
        checkfollowersforbots(chusr)
        input('Press Any key to return to menu. This will clear the screen')
    elif chosen == 3:
        clear()
        nusr = input('Enter the username you wish to add to the list of users we monitor: ').lower()
        chans.append(nusr)
        updateconfigchannels(",".join(chans))
        cmd = startbanbot(cid, token, usern, nusr, ctoken)
        p = subprocess.Popen(cmd, shell=True)
        print('Added ' + nusr + ' to the config file and started monitoring.')
        logging.info('Added ' + nusr + ' to the config file and started monitoring.')
        print('Check the logs directory for any logging. if you do not')
        print('see a new log with the new username in the filename, it is possible the username was incorrect')
        print('Returning to the main menu in 5 seconds')
        time.sleep(5)
    elif chosen == 4:
        clear()
        isbad = input('Enter the username you wish to check: ').lower()
        if isuserloginindb(isbad):
            print(isbad + ' Is a bad user, BAN Them')
            logging.info(isbad + ' Is a bad user, BAN Them')
            time.sleep(5)
        else:
            print(
                isbad + ' is not in the Bad list. If the DB has not been updated in the last hour, update and try again'
            )
            logging.info(
                isbad + ' is not in the Bad list. If the DB has not been updated in the last hour, update and try again'
            )
            time.sleep(5)
    elif chosen == 5:
        break
    else:
        print('Invalid Entry, Try again')
        time.sleep(5)

sys.exit()
