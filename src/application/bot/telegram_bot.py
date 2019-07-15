import json
import os
from functools import wraps
from logging import getLogger

from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Updater,
    Filters,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from jinja2 import Environment, FileSystemLoader

from application.models import User
from application.ecommerce_api.moltin_api.exceptions import MoltinApiError, MoltinError
from application.ecommerce_api.moltin_api.moltin import MoltinApi
from application.bot.utils import chunks

logger = getLogger(__name__)


class TelegramBot:
    def __init__(self, token: str, moltin_api: MoltinApi):
        self.updater = Updater(token=token)
        templates_directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'templates'
        )
        file_loader = FileSystemLoader(templates_directory)
        env = Environment(loader=file_loader)
        bot_processor = BotProcessor(moltin_api, env)
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(CallbackQueryHandler(bot_processor.handle_use_reply))
        dispatcher.add_handler(CommandHandler('start', bot_processor.handle_use_reply))
        dispatcher.add_handler(
            MessageHandler(Filters.text, bot_processor.handle_use_reply)
        )

    def start(self):
        logger.debug('Bot polling started')
        self.updater.start_polling()


def check_callback_query_exists(func):
    """
    User ignored keyboard options and sent random string.
    Let's return him back to the current state
    """

    @wraps(func)
    def wrapped(self, bot, update):
        query = update.callback_query
        if query is None:
            user_id = update.message.chat_id
            bot.delete_message(chat_id=user_id, message_id=update.message.message_id)
            user = User(user_id)
            user_state = user.get_state_from_db()
            return user_state
        return func(self, bot, update)

    return wrapped


class BotProcessor:
    CALLBACK_MENU = 'menu'
    CALLBACK_CART = 'cart'
    available_quantity_options = ['1 pc', '2 pcs', '5 pcs']

    @staticmethod
    def get_button_cart():
        return InlineKeyboardButton(
            'Go to cart', callback_data=BotProcessor.CALLBACK_CART
        )

    @staticmethod
    def get_button_menu():
        return InlineKeyboardButton(
            'Go to menu', callback_data=BotProcessor.CALLBACK_MENU
        )

    def __init__(self, moltin_api: MoltinApi, jinja_env: Environment):
        self.moltin_api = moltin_api
        self.jinja_env = jinja_env

    def handle_use_reply(self, bot, update):
        if update.message:
            user_reply = update.message.text
            chat_id = update.message.chat_id
        elif update.callback_query:
            user_reply = update.callback_query.data
            chat_id = update.callback_query.message.chat_id
        else:
            return

        user = User(chat_id)

        if user_reply == '/start':
            user_state = 'HANDLE_START'
        else:
            user_state = user.get_state_from_db()

        states_functions = {
            'HANDLE_START': self.handle_start,
            'HANDLE_MENU': self.handle_menu,
            'HANDLE_PRODUCT': self.handle_product,
            'HANDLE_CART': self.handle_cart,
        }
        state_handler = states_functions[user_state]

        try:
            next_state = state_handler(bot, update)
            user.save_state_to_db(next_state)
        except Exception as e:
            logger.error('A general exception occurred: {}'.format(str(e)))

    def handle_start(self, bot, update):

        if update.message:
            chat_id = update.message.chat_id
        else:
            chat_id = update.callback_query.message.chat_id

        self.view_menu(bot, chat_id)

        return 'HANDLE_MENU'

    @check_callback_query_exists
    def handle_menu(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id

        bot.delete_message(
            chat_id=query.message.chat_id, message_id=query.message.message_id
        )

        if query.data == BotProcessor.CALLBACK_CART:
            self.view_cart(bot, chat_id)
            return 'HANDLE_CART'

        product_id = query.data
        self.view_product(bot, chat_id, product_id)

        return 'HANDLE_PRODUCT'

    @check_callback_query_exists
    def handle_product(self, bot, update):

        query = update.callback_query
        chat_id = query.message.chat_id
        message_id = query.message.message_id

        bot.delete_message(chat_id=chat_id, message_id=message_id)

        if query.data == BotProcessor.CALLBACK_MENU:
            self.view_menu(bot, chat_id)
            return 'HANDLE_MENU'
        elif query.data == BotProcessor.CALLBACK_CART:
            self.view_cart(bot, chat_id)
            return 'HANDLE_CART'

        product_id = query.data

        product_presentation = deserialize_product_presentation(product_id)

        try:
            self.moltin_api.add_product_to_cart(
                chat_id,
                product_presentation['id'],
                quantity=int(product_presentation['qty']),
            )
        except MoltinApiError as e:
            error_text = 'Cannot add item to card. An error occurred: {}. {}'.format(
                str(e.title), str(e.detail)
            )
            logger.error(str(e))
            self.view_menu(bot, chat_id, error_text)
            return 'HANDLE_MENU'
        except MoltinError as e:
            error_text = 'An error occurred, please try again later.'
            logger.error(str(e))
            self.view_menu(bot, chat_id, error_text)
            return 'HANDLE_MENU'

        text = 'Item has been successfully added to cart. Please, continue:'
        self.view_menu(bot, chat_id, text)

        return 'HANDLE_MENU'

    @check_callback_query_exists
    def handle_cart(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id
        message_id = query.message.message_id

        bot.delete_message(chat_id=chat_id, message_id=message_id)

        if query.data == BotProcessor.CALLBACK_MENU:
            self.view_menu(bot, chat_id)
            return 'HANDLE_MENU'

        item_id = query.data
        self.moltin_api.remove_item_from_cart(chat_id, item_id)
        self.view_cart(bot, chat_id)
        return 'HANDLE_CART'

    def view_menu(self, bot, chat_id, text=None):

        keyboard_row_buttons_width = 2
        products = self.moltin_api.get_products()
        products_chunks = chunks(products, keyboard_row_buttons_width)

        products_options = [
            [
                InlineKeyboardButton(product.name, callback_data=product.id)
                for product in product_chunk
            ]
            for product_chunk in products_chunks
        ]

        keyboard = [*products_options, [BotProcessor.get_button_cart()]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        if text is None:
            text = 'Make your choice.'
        bot.send_message(chat_id, text, reply_markup=reply_markup)

    def view_product(self, bot, chat_id, product_id):

        product = self.moltin_api.get_product_by_id(product_id)

        text = '{}\n{}\n{}'.format(
            product.name, product.formatted_price_with_tax, product.description
        )

        products_quantity_options = [
            InlineKeyboardButton(
                quantity_option,
                callback_data=serialize_product_presentation(product, quantity_option),
            )
            for quantity_option in BotProcessor.available_quantity_options
        ]

        keyboard = [
            products_quantity_options,
            [BotProcessor.get_button_cart(), BotProcessor.get_button_menu()],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if product.main_image_id is None:
            bot.send_message(chat_id, text, reply_markup=reply_markup)
        else:
            file = self.moltin_api.get_file_by_id(product.main_image_id)
            bot.send_photo(
                chat_id, photo=file.link, caption=text, reply_markup=reply_markup
            )

    def view_cart(self, bot, chat_id):
        template = self.jinja_env.get_template('cart_content.jinja2')
        cart_header = self.moltin_api.get_cart(chat_id)
        cart_content = self.moltin_api.get_cart_products(chat_id)
        output = template.render(
            cart_content=cart_content, total=cart_header.formatted_price_with_tax
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    'Remove {} from cart'.format(product_in_cart.name),
                    callback_data=product_in_cart.id,
                )
                for product_in_cart in cart_content
            ],
            [BotProcessor.get_button_menu()],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id, output, reply_markup=reply_markup)


def serialize_product_presentation(product, quantity_option):
    quantity, unit_of_measure = quantity_option.split()
    data = json.dumps({'id': product.id, 'qty': quantity})
    return data


def deserialize_product_presentation(encoded_string):
    data = json.loads(encoded_string)
    return data
