# Python ecommerce bot.

This is a bot application which is integrated with [Motlin ecommerce API](https://www.moltin.com/).
Main purpose of the bot is to provide opportunity to user to make an order and buy goods with telegram.
Bot logic based on implementation of state machine. 
Currently the following functionality is supported:
* Listing of available products
* Operations with cart:
    * Add item to cart
    * Remove item from cart
    * View cart content
* Checkout procedure represents the saving of contact details of customer


### Usage

#### Telegram configuration
* Obtain a token for your bot from [botfather](https://core.telegram.org/bots).
* Update TELEGRAM_BOT_TOKEN at .env file.
#### Moltin configuration
* Register at [Motlin ecommerce API](https://www.moltin.com/).
* Create new store.
* Update MOLTIN_STORE_ID, MOLTIN_CLIENT_ID and MOLTIN_CLIENT_SECRET at .env file with your API keys.
* MOLTIN_API_URL is a https://api.moltin.com
### Development with docker-compose

Build with docker-compose:
```bash
docker-compose -f docker-compose-dev.yml build
```
Run:
```bash
docker-compose -f docker-compose-dev.yml up
```

Run tests:
```bash
python -m pytest
```


### Deployment with Heroku
This application requires Heroku-redis add-on.
* To deploy this app on Heroku you need to setup environment variable APP_SETTINGS=config.ProductionConfig
* Activate Heroku-redis add-on on your account.

* Login with [Heroku cli](https://devcenter.heroku.com/articles/heroku-cli):
    ```bash
    heroku login
    ```
* To reveal configuration variables:
    ```bash
    heroku config --app <your_application_name_here>
    ```
* Run application and track logs:
    ```bash
    heroku ps:scale bot-telegram=1 --app <your_application_name_here>
    heroku logs --tail --app <your_application_name_here>
    ```
    
### Further improvement:
* Full test coverage
* Implement FSM with a [transitions](https://github.com/pytransitions/transitions) library