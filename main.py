import telebot
import time
from config import *
from mongoengine import connect
from models.bot.cats_and_products import *
from bson import ObjectId
from models.bot.user_model import User
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup)
from flask import Flask, abort, request
#-----------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
bot = telebot.TeleBot(Token)
connect('bot_shop')

API_TOKEN = Token

WEBHOOK_HOST = '34.70.37.200'
WEBHOOK_PORT = 80 # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0' # in some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem' # path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem' # path to the ssl private key

WEBHOOK_URL_BASE = 'https://%s:%s' % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = '/%s/' % (API_TOKEN)

# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if  request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

#handlers---------------------------------------------------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def start_message(message):
    User.get_or_create_user(message)
    message_keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    message_keyboard.row('\U0001F4C1Категории')
    message_keyboard.row('\U00002139Информация')
    message_keyboard.row('\U0001F6D2Корзина')
    if message.from_user.first_name:
        name = ' ' + message.from_user.first_name
    else:
        name = ''
    bot.send_message(message.chat.id, text=f'Здраствуйте{name}. ' + Texts.get_text("ru_greetings"),
                     reply_markup=message_keyboard)

@bot.message_handler(regexp='\U00002139Информация')
def info(message):
    info_kb = InlineKeyboardMarkup()
    news_button = InlineKeyboardButton(text='\U0001F4E2Последние новости', callback_data='news')
    history_button = InlineKeyboardButton(text='\U00002699История заказов', callback_data='history')
    info_kb.add(news_button, history_button)
    bot.send_message(message.chat.id, text='|\U00002139|', reply_markup=info_kb)

@bot.callback_query_handler(func=lambda call: call.data == 'news')
def news(call):
    bot.send_message(call.message.chat.id, Texts.get_text("ru_news"))

@bot.callback_query_handler(func=lambda call: call.data == 'history')
def news(call):
    curent_user = User.objects.get(user_id=call.message.chat.id)
    history_kb = InlineKeyboardMarkup(row_width=2)
    buttons_list = []
    orders_list = Cart.objects.filter(user=curent_user, is_archived=True).all()
    if orders_list:
        n = 1
        for o in orders_list:
            buttons_list.append(InlineKeyboardButton(text=f'{n}) Дата: {o.archived_date}',
                                                     callback_data='order_' + str(o.id)))
            n += 1
        history_kb.add(*buttons_list)
        bot.send_message(call.message.chat.id, text='Список выполненных заказов:', reply_markup=history_kb)
    else:
        bot.send_message(call.message.chat.id, text='Увас еще нет заказов')

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'order')
def sub_cat_kb(call):
    order = Cart.objects.filter(id=call.data.split('_')[1]).first()
    products_str_list = ''
    n = 1
    for p in order.products:
        products_str_list = products_str_list + f'{n}) {p.title.capitalize()}\n'
        n += 1
    bot.send_message(call.message.chat.id, text=f'Дата: <i>{order.archived_date}</i>\n'
                                                f'<b>Список продуктов:</b>\n{products_str_list}',
                     parse_mode='HTML')

@bot.message_handler(regexp='\U0001F4C1Категории')
def categories(message):
    inline_kb = InlineKeyboardMarkup(row_width=2)
    buttons_list = []
    categories = ['сердца', 'кожи', 'имунитета', 'печени', 'желудка', 'нервов']
    categories_list = []
    for c in categories:
        categories_list.append(Category.objects.filter(title='Препараты для ' + c).first())
    for i in categories_list:
        callback_data = 'category_'+str(i.id)
        if i.is_parent:
            callback_data = "subcategory_" + str(i.id)
        buttons_list.append(InlineKeyboardButton(text=i.title, callback_data=callback_data))
    inline_kb.add(*buttons_list)
    bot.send_message(chat_id=message.chat.id, text='\U0001F4C1Категории', reply_markup=inline_kb)

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'subcategory')
def sub_cat_kb(call):
    sub_cat_kb = InlineKeyboardMarkup(row_width=2)
    sub_cat_buttons = []
    category = Category.objects.get(id=call.data.split("_")[1])
    for i in category.sub_categories:
        callback_data = 'category_' + str(i.id)
        if i.is_parent:
            callback_data = "subcategory_" + str(i.id)
        sub_cat_buttons.append(InlineKeyboardButton(text=i.title, callback_data=callback_data))
    sub_cat_kb.add(*sub_cat_buttons)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id, text='Суб категории', reply_markup=sub_cat_kb)

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'category')
def products_buttons(call):
    cat = Category.objects.filter(id=call.data.split('_')[1]).first()
    products = cat.category_products
    if not products:
        bot.send_message(call.message.chat.id, 'В данной категории пока нет продуктов.')
    for p in products:
        title = f'<b>{p.title.capitalize()}</b>'
        description = f'<i>{p.description.capitalize()}</i>'
        products_kb = InlineKeyboardMarkup(row_width=1)
        products_kb.add(InlineKeyboardButton(
            text="Добавить в корзину",
            callback_data='add to cart_'+str(p.id)),
        InlineKeyboardButton(
            text="Подробно о продукте",
            callback_data='info_' + str(p.id))
        )
        bot.send_photo(call.message.chat.id,
                       p.image.get(),
                       caption="Название: " + title + "\nОписание: " + description,
                       reply_markup=products_kb,
                       parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'add to cart')
def add_to_cart(call):
    Cart.create_cart_or_add_to_cart(
        product_id=call.data.split('_')[1],
        user_id=call.message.chat.id)
    bot.send_message(call.message.chat.id, text='Товар добавлен в корзину.')

@bot.message_handler(regexp="\U0001F6D2Корзина")
def show_cart(message):
    curent_user = User.objects.get(user_id=message.chat.id)
    cart = Cart.objects.filter(user=curent_user, is_archived=False).first()
    if cart:
        if not cart.products:
            bot.send_message(message.chat.id, text='Корзина пустая')
        else:
            for product in cart.products:
                remove_kb = InlineKeyboardMarkup()
                remove_button = InlineKeyboardButton(
                    text='Удалить из корзины', callback_data='rm product_' + str(product.id))
                remove_kb.add(remove_button)
                bot.send_message(message.chat.id, product.title.capitalize(),
                                 reply_markup=remove_kb)
            cart_kb = InlineKeyboardMarkup()
            clear_button = InlineKeyboardButton(text='Очистить корзину', callback_data='clear cart_' + str(cart.id))
            archiv_button = InlineKeyboardButton(text='Выполнить заказ', callback_data='archiv cart_' + str(cart.id))
            cart_kb.add(archiv_button, clear_button)
            bot.send_message(message.chat.id, text=f'Общая сумма: {cart.get_sum}грн', reply_markup=cart_kb)
    else:
        bot.send_message(message.chat.id, text='Вы еще ничего не добавили в корзину')

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'clear cart')
def clear_cart(call):
    curent_user = User.objects.get(user_id=call.message.chat.id)
    cart = Cart.objects.filter(user=curent_user, is_archived=False).first()
    cart.clean_cart()
    bot.send_message(call.message.chat.id, text='Корзина очищена')

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'archiv cart')
def archiv_cart(call):
    curent_user = User.objects.get(user_id=call.message.chat.id)
    cart = Cart.objects.filter(user=curent_user, is_archived=False).first()
    cart.is_archived = True
    cart.archived_date = time.strftime("%d.%m.%y (%H:%M:%S)")
    cart.save()
    bot.send_message(call.message.chat.id, text='Заказ выполнен')

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'rm product')
def rm_product_from_cart(call):
    curent_user = User.objects.get(user_id=call.message.chat.id)
    cart = Cart.objects.filter(user=curent_user).first()
    cart.update(pull__products=ObjectId(call.data.split('_')[1]))
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.split('_')[0] == 'info')
def product_info(call):
    product = Product.objects.filter(id=call.data.split('_')[1]).first()
    bot.send_message(call.message.chat.id,
                     text=f"<b>Название: '{product.title.capitalize()}</b>'\n"
                     f"Цена: {product.price}грн\n"
                     f"Наличиена складе: {product.is_available}\n"
                     f"Действует ли скидка: {product.is_discount}\n\n"
                     f"<b>Габариты упаковки:</b>\n"
                     f"Вес: {round(product.weight)}грамм\n"
                     f"Ширина: {round(product.width, 2)}мм\n"
                     f"Высота: {round(product.height, 2)}мм".replace('True','Да').replace('False', 'Нет'),
                     parse_mode='HTML')
#-----------------------------------------------------------------------------------------------------------------------

print("Bot started")
# bot.polling(none_stop=True)

bot.remove_webhook()
time.sleep(0.1)
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))
app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        debug=True)
