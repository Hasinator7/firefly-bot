# Firefly Bot

A Telegram bot to create transactions in Firefly III. This fork works exactly like the original, except that the first user to message the bot becomes the only authorized user. The bot will ignore the inputs of unauthorized users except that it tells those user that they are not authorized.
## Setup

First you'll have to generate a Telegram Bot token through [BotFather](https://t.me/botfather). Once you generate the token, keep it safe.

### Docker

```bash
git pull https://github.com/Hasinator7/firefly-bot
docker build -t fireflybot .
docker start -e TELEGRAM_BOT_TOKEN=<your-bot-token> fireflybot
```

## Usage

### Setup
- Once the bot is up and running, initiate a chat with the bot. Send `/start` to initiate setup 
  - `/start` can also be used to re-run the setup at a later time
- You will first be asked for your Firefly URL. Enter the full URL including the protocol. Eg - `https://firefly.host.com`
  - Make sure **not** to include a trailing slash
- Second, you will be asked for your User Token. You will have to generate one from the profile section in your Firefly instance, under OAuth. 
- Lastly, you will be asked for a default account, by default all transactions will use this account as the source account, however, you can override it per transaction

### Creating a Transaction
All you need to do is send a message to the bot with the following format

```Amount, Description, Category, Budget, Source account, Destination account```

Only the first two values are needed. The rest are optional. The description value is used for destination account as well. 
  
**Examples**

A simple one - 

```5, Starbucks```

One with all the fields being used -

```5, Mocha with an extra shot for Steve, Coffee, Food Budget, UCO Bank, Starbucks```

You can skip specfic fields by leaving them empty (except the first two) - 

```5, Starbucks, , Food Budget, UCO Bank```

You can also specify accounts by using their id instead of their name - 

```5, Mocha with an extra shot for Steve, Coffee, Food Budget, 5, 35```

---

## Development
- Clone the repository
- Install [Poetry](https://github.com/python-poetry/poetry)
- Install dependencies by running `poetry install`
- Run `poetry shell` to activate virtualenv
- Start the bot by running `python src/bot.py`

### Notes

**Why Poetry AND requirements.txt?**
I don't want to use poetry inside Docker. It's unnecessary bloat and complexity. So I just generate a requirements.txt anytime I change deps using - `poetry export -f requirements.txt > requirements.txt`. It can then be used for Docker, or just anyone who wants to use this without having to install (and figure out) poetry.
