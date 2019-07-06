# Python ecommerce bot.

This is a bot application which is integrated with [Motlin ecommerce API](https://www.moltin.com/).
Main purpose of the bot is to provide opportunity to user to make an order with telegram.
Bot logic based on implementation of state machine. 
Currently the following functionality is supported:
* Show available products

### Usage
#### Telegram configuration
* Obtain a token for your bot from [botfather](https://core.telegram.org/bots).
* Update TELEGRAM_BOT_TOKEN at .env file.
#### Motlin configuration
* Register at [Motlin ecommerce API](https://www.moltin.com/).
* Create new store.
* Update MOLTIN_STORE_ID, MOLTIN_CLIENT_ID and MOLTIN_CLIENT_SECRET at .env file with your API keys.
### Development with docker-compose

Build with docker-compose:
```bash
docker-compose -f docker-compose-dev.yml build
```
Run:
```bash
docker-compose -f docker-compose-dev.yml up
```