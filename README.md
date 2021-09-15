# TwitchBanBot

TwitchBanBot is a simple app to monitor your chat on twitch and check any user that joins against a list of known bad bots (ones that are known to be follow bots or hate raid bots) and if that user is a known bot it will issue the /ban command immediately. 

## Installation

Make sure you have Python 3.8+ installed
Download a copy of this git repo and unzip it to a folder. 
in the folder run 
```bash
pip install -r requirements.txt
```
The first time you use the app (main.py) it will ask you a few questions to create the config file. 
You will want to create a bot account on twitch and then with that account .

1. Go to https://dev.twitch.tv/console/apps .
2. Click "Register your application" .
3. Give it a name.
4. In the OAuth Redirect URLs field put https://localhost:5000
6. In the Category select Application Integration.
7. Click Create.
8. On the next screen you will see your bot you just created. Click Manage.
9. Copy the Client ID to a text doc as it will be needed.
10. Click New Secret and click OK on the popup.
11. Copy the Client Secret that was created to your text doc as it will be needed.

That is all you need from there. Next you need to generate a password so your bot can log into Twitches Chat system

1. If you are logged into Twitch with any account other than your bot account, logout
2. Go to https://twitchapps.com/tmi
3. Click Connect, if you followed step 1 then either login with your bot account or you will be presented with your password starting with oauth: (if you did not logout of your personal account in step one this will be wrong and the bot will not work)
4. Copy the password to your text doc

Now we want to mod your bot account

1. If you are not already, login to twitch with your bot account
2. Go to your Twitch Channel and follow it with the bot
3. Logout of your bot account and login to your personal Twitch account
4. Go to your channel
5. Click the "→Chat" button and this will popout the chat channel for your account
6. In the chat run the mod command "/mod <bot account name>" (without the quotes or <>)

Now you are all set to start the bot. 

1. Open a command prompt
2. navigate to the directory you unzipped the files from the repository
3. Run ```python main.py```
4. This will go through a list of questions that you will use the information we have gathered to this point: Twitch Username (this is your bots username), Client ID, Client Secret, the Channel to monitor (This would be your channel name or your twitch username), the tmi password that starts with "oauth:"
5. Once you finish with the questions it will start the ban bot in the background, and you will be presented with some options. 

The first thing you will want to do is run Option 1. This will update the local database you downloaded when you grabbed a copy of the github repo from the master list. Depending how old the DB in the repo is this could take some time(in some cases hours), I will try to keep the repo updated as frequently as possible though. 

Once you have ran that you will then want to run your followers through the bot. This will check to see if you are being followed by any of these nefarious bots. When you are presented with the Menu choose Option 2 and enter your Twitch name, it will download your follower list 100 at a time and check the names against the local database, if there is a match it will let you know that you may want to ban this, This is not banning automatically as I felt it best for you to make that decision as it is an account that is already following you.

At this point the menu will just sit there in the command prompt waiting for input until you close it. If you are a mod on another channel and you want to monitor that channel make sure the broadcaster mods your bot account and then run Option 3 in the menu, This will spawn another bot in the background to monitor that channel. 

Lastly, if you keep the menu up in the background and you see a sus account in a chat you are on you can run Option 4 and enter their name to check if it is in the database. 

Have Fun!