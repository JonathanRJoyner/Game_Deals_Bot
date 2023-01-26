<p align="center"><img src="https://user-images.githubusercontent.com/89750679/214477390-951d28bd-cc65-44bd-b669-6c7d77f746bd.png" alt="Game Deals Logo" width="200"/></p>

<p align="center">
<a href="https://top.gg/bot/1028073862597967932">
  <img src="https://top.gg/api/widget/servers/1028073862597967932.svg?noavatar=true">
</a>
<a href="https://top.gg/bot/1028073862597967932">
  <img src="https://top.gg/api/widget/upvotes/1028073862597967932.svg?noavatar=true">
</a>
</p>

# Game Deals Bot

A discord bot for game deals, giveaways, and free game releases. 

## Table of Contents

- [Usage](#usage)
- [Built With](#built-with)
- [Support](#support)
- [Contributing](#contributing)

## Usage

[Invite the bot](https://discord.com/oauth2/authorize?client_id=1028073862597967932&permissions=2147485696&scope=bot) to your Discord server.

Application commands ([aka slash commands](https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ)) are the main entrypoint for all bot functions. Bot functions include:

 - Checking game prices
 - Creating alerts
 - Deleting alerts

### Alert Creation and Deletion

![Alert Commands](https://user-images.githubusercontent.com/89750679/214490137-190567a5-1eda-4963-915e-5a51633849d6.png)

Alert creation is simple and requires no input. Simply using the command will create an alert in the channel.
Deleting alerts is equally as simple. Just pick a type of alert to delete and the alerts will be removed on your server.


### Game Price Check and Alerts

![Game Price Gif](https://user-images.githubusercontent.com/89750679/214491752-56ebdc80-0f88-46cb-a3e4-afe079908224.gif)


Game prices can be checked using the price_lookup or price_alert commands. It requires a game name input and will autocomplete suggestions based on the input. Once the current game price is shown, there is an option to set an alert using the button below.

## Built With

This bot relies on several other libraries:

 - [Py-cord](https://github.com/Pycord-Development/pycord) - Discord API wrapper
 - [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) - SQL toolkit and ORM
 - [Psycopg2](https://github.com/psycopg/psycopg2) - PostgreSQL database adapter
 - [Topggpy](https://github.com/top-gg/python-sdk) - Top.gg API wrapper

## Support

Join the [support server](https://discord.gg/BtGjwBShYk)!
