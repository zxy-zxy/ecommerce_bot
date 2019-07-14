import json
from functools import wraps

from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Updater,
    Filters,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from application.models import User
from application.ecommerce_api.moltin_api.exceptions import MoltinApiError, MoltinError
from application.ecommerce_api.moltin_api.moltin import MoltinApi
from application.bot.utils import chunks


class TelegramBot:
    def __init__(self, token: str, moltin_api: MoltinApi):
        self.updater = Updater(token=token)
        handlers = TelegramBotHandlers(moltin_api)
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(
            CallbackQueryHandler(handlers.handle_use_reply))
        dispatcher.add_handler(
            CommandHandler('start', handlers.handle_use_reply))
        dispatcher.add_handler(
            MessageHandler(Filters.text, handlers.handle_use_reply))

    def start(self):
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
            bot.delete_message(
                chat_id=user_id,
                message_id=update.message.message_id
            )
            user = User(user_id)
            user_state = user.get_state_from_db()
            return user_state
        return func(self, bot, update)

    return wrapped


class TelegramBotHandlers:
    CALLBACK_RETURN = 'return'
    CALLBACK_CART = 'cart'
    available_quantity_options = ['1 pc', '2 pcs', '5 pcs']

    @staticmethod
    def get_button_cart():
        return InlineKeyboardButton('Cart', callback_data=TelegramBotHandlers.CALLBACK_CART)

    @staticmethod
    def get_button_return():
        return InlineKeyboardButton('Return', callback_data=TelegramBotHandlers.CALLBACK_RETURN)

    def __init__(self, moltin_api: MoltinApi):
        self.moltin_api = moltin_api

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
            'HANDLE_CART': self.handle_cart
        }
        state_handler = states_functions[user_state]

        try:
            next_state = state_handler(bot, update)
            user.save_state_to_db(next_state)
        except Exception as err:
            print(err)

    def handle_start(self, bot, update):

        chat_id = update.message.chat_id if update.message \
            else update.callback_query.message.chat_id

        self.show_menu(bot, chat_id)

        return 'HANDLE_MENU'

    @check_callback_query_exists
    def handle_menu(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id

        if query.data == TelegramBotHandlers.CALLBACK_CART:
            self.show_cart(bot, chat_id)
            return 'HANDLE_CART'

        product_id = query.data

        bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )

        self.show_product(bot, chat_id, product_id)

        return 'HANDLE_PRODUCT'

    @check_callback_query_exists
    def handle_product(self, bot, update):

        query = update.callback_query
        chat_id = query.message.chat_id
        message_id = query.message.message_id

        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )

        if query.data == TelegramBotHandlers.CALLBACK_RETURN:
            return 'HANDLE_START'
        elif query.data == TelegramBotHandlers.CALLBACK_CART:
            self.show_cart(bot, chat_id)
            return 'HANDLE_CART'

        product_id = query.data

        product_presentation = deserialize_product_presentation_from_callback(
            product_id)

        try:
            self.moltin_api.add_product_to_cart(
                chat_id,
                product_presentation['id'],
                quantity=int(product_presentation['qty'])
            )
        except MoltinApiError as e:
            text = 'Cannot add item to card. Error occured: {}'.format(str(e))
            self.show_menu(bot, chat_id, text)
            return 'HANDLE_MENU'

        text = 'Item has been successfully added to cart. Please, continue:'
        self.show_menu(bot, chat_id, text)

        return 'HANDLE_MENU'

    def handle_cart(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id

    def show_menu(self, bot, chat_id, text=None):

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

        keyboard = [
            *products_options,
            [TelegramBotHandlers.get_button_cart()]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        if text is None:
            text = 'Please choose:'
        bot.send_message(
            chat_id,
            text,
            reply_markup=reply_markup
        )

    def show_product(self, bot, chat_id, product_id):

        product = self.moltin_api.get_product_by_id(product_id)

        text = '{}\n{}\n{}'.format(
            product.name,
            product.formatted_price_with_tax,
            product.description
        )

        products_quantity_options = [
            InlineKeyboardButton(
                quantity_option,
                callback_data=serialize_product_presentation_for_callback(
                    product, quantity_option)
            )
            for quantity_option in TelegramBotHandlers.available_quantity_options
        ]

        keyboard = [
            products_quantity_options,
            [
                TelegramBotHandlers.get_button_cart(),
                TelegramBotHandlers.get_button_return()
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if product.main_image_id is None:
            bot.send_message(
                chat_id,
                text,
                reply_markup=reply_markup
            )
        else:
            file = self.moltin_api.get_file_by_id(product.main_image_id)
            bot.send_photo(
                chat_id,
                photo=file.link,
                caption=text,
                reply_markup=reply_markup
            )

    def show_cart(self, bot, chat_id):

        cart_current_condition = self.moltin_api.get_cart(chat_id)
        cart_products = self.moltin_api.get_cart_products(chat_id)

        bot.send_message(
            chat_id,
            'This is cart content',
        )


def serialize_product_presentation_for_callback(product, quantity_option):
    quantity, unit_of_measure = quantity_option.split()
    data = json.dumps({'id': product.id, 'qty': quantity})
    return data


def deserialize_product_presentation_from_callback(encoded_string):
    data = json.loads(encoded_string)
    return data
