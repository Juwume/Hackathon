from xml.dom.minidom import Document
from mongoengine import *


class ArticleVC(Document):
    title = StringField(required=True)
    text = StringField(required=True)
    tags = ListField(StringField())
    category = StringField(required=False)
    repost_amt = IntField(required=False)
    comment_amt = IntField(required=False)
    published = StringField(required=False)
