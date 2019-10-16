from mongoengine import *
from models.bot.user_model import User
import time

class Category(Document):
    title = StringField(max_length=64)
    sub_categories = ListField(ReferenceField('self'))

    @property
    def category_products(self):
        return Product.objects.filter(category=self, is_available=True)

    @property
    def is_parent(self):
        if self.sub_categories:
            return True

class Product(Document):
    title = StringField(max_length=64)
    image = FileField()
    description = StringField(max_length=4096)
    price = IntField(min_value=0)
    quantity = IntField(min_value=0)
    is_available = BooleanField()
    is_discount = BooleanField(default=False)
    category = ReferenceField(Category)
    weight = FloatField(min_value=0, null=True)
    width = FloatField(min_value=0, null=True)
    height = FloatField(min_value=0, null=True)

class Texts(Document):
    title = StringField()
    text = StringField(max_length=4096)

    @classmethod
    def get_text(cls, title):
        return cls.objects.filter(title=title).first().text

class Cart(Document):
    archived_date = StringField(max_length=64)
    user = ReferenceField(User, required=True)
    products = ListField(ReferenceField(Product))
    is_archived = BooleanField(default=False)

    @property
    def get_sum(self):
        cart_sum = 0
        for p in self.products:
            cart_sum += p.price
        return round(cart_sum)

    @classmethod
    def create_cart_or_add_to_cart(cls, product_id, user_id):
        user = User.objects.filter(user_id=user_id).first()
        user_cart = cls.objects.filter(user=user, is_archived=False).first()
        product = Product.objects.filter(id=product_id).first()
        if user_cart:
            user_cart.products.append(product)
            user_cart.save()
        else:
            cls(user=user, products=[product]).save()

    def clean_cart(self):
        self.products = []
        self.save()
