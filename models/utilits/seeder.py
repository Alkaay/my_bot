import random
import string
from models.bot.cats_and_products import Category, Product, Texts
from mongoengine import connect

random_bool = (True, False)

def random_string(str_len=20):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(str_len))

def ru_random_string(str_len=20):
    letters = 'йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ'
    return ''.join(random.choice(letters) for i in range(str_len))

def seed_and_get_real_cats():
    cats_list = ['сердца', 'кожи', 'имунитета', 'печени', 'желудка', 'нервов']
    real_cats_list = []
    for i in cats_list:
        cat = Category(title='Препараты для ' + i).save()
        real_cats_list.append(cat)
    return real_cats_list

def seed_and_get_sub_categories():
    cats_list = ['Дешевые', 'Средней стоимости', 'Дорогие']
    sub_cats = []
    for i in cats_list:
        cat = Category(title=i).save()
        sub_cats.append(cat)
    return sub_cats

def seed_real_products(num_of_products, list_of_cats):
    with open('products.txt', 'r') as f:
        list_of_products = []
        for i in range(30):
            list_of_products.append(f.readline().replace('\n', ''))
    for p in range(num_of_products):
        product = dict(
            title=random.choice(list_of_products),
            description=random_string(),
            price=random.randint(1000, 100*1000),
            quantity=random.randint(0,100),
            is_available=random.choice(random_bool),
            is_discount=random.choice(random_bool),
            weight=random.uniform(0, 100),
            width=random.uniform(0, 100),
            height=random.uniform(0, 100),
            category=random.choice(list_of_cats)
        )
        Product(**product).save()

def seed_cats_with_subcats():
    full_list_of_subcats = []
    real_cats = seed_and_get_real_cats()
    for c in real_cats:
        c.sub_categories = seed_and_get_sub_categories()
        c.save()
        for l in c.sub_categories:
            full_list_of_subcats.append(l)
    return full_list_of_subcats

def seed_images_to_products():
    products = Product.objects.all()
    for i in products:
        r = random.randint(1, 5)
        with open(f'D:\python_learn\python course\my_bot\images\\test_{r}.png', 'rb') as image:
            i.image.replace(image)
            i.save()

def seed_texts():
    Texts(title='ru_news', text="Препараты в категориях разделены по приблизительной стоимости.").save()
    Texts(title='ru_greetings', text="Вы зашли на телеграмм бот нашего магазина медецинских препаратов.").save()

def clear_db():
    Product.objects.all().delete()
    Category.objects.all().delete()
    Texts.objects.all().delete()

#----------------------------------------------------------------------------------------------------------------------
connect('bot_shop')
seed_texts()
seed_real_products(150, seed_cats_with_subcats())
seed_images_to_products()
# clear_db()



