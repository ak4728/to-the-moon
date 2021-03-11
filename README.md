<p align="center">
  <img alt="to-the-moon.py" src="https://dl3.pushbulletusercontent.com/25CJDZ1FmLHTYh6e1AHLtaCLLzzWO70S/Untitled-1.png" width="750px">
</p>

## Requirements
- Python 3.6 and up - https://www.python.org/downloads/
- git - https://git-scm.com/download/

## Command List
!ticker
!interval
!watchlist
!sentiment
!reddit

## How to setup
1. Make a bot [here](https://discordapp.com/developers/applications/me) and grab the token
![Image_Example1](https://i.alexflipnote.dev/f9668b.png)

2. Rename the file **config.json.example** to **config.json**, then fill in the required spots, such as token, prefix and game

3. To install what you need, do **pip install -r requirements.txt**<br>
(If that doesn't work, do **python -m pip install -r requirements.txt**)<br>
`NOTE: Use pip install with Administrator/sudo`

4. Start the bot by having the cmd/terminal inside the bot folder and type **python main.py**

5. You're done, enjoy your bot!


### Docker
Well, we need to find a way to write a docker file with auto-reboot functions.
```
# Build and run the Dockerfile
docker-compose up -d --build

# Tips on common commands
docker-compose <command>
  ps      Check if bot is online or not (list)
  down    Shut down the bot
  reboot  Reboot the bot without shutting it down or rebuilding
  logs    Check the logs made by the bot.
```
