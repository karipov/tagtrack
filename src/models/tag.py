from pathlib import Path
# import pickle
# import codecs

from peewee import SqliteDatabase, Model
from peewee import TextField, IntegerField, CompositeKey


db = SqliteDatabase(Path.cwd().joinpath('src/config/tags.db'))


# class PackedId(Field):
#     field_type = "text"

#     def db_value(self, value: list):
#         return codecs.encode(pickle.dumps(value), "base64").decode()

#     def python_value(self, value: str):
#         return pickle.loads(codecs.decode(value.encode(), "base64"))


class Tags(Model):
    chat_id = IntegerField()
    message_id = IntegerField()
    reply_message_id = IntegerField()
    card_id = TextField()
    short_url = TextField()

    class Meta:
        primary_key = CompositeKey('chat_id', 'message_id')
        database = db


db.connect()
db.create_tables([Tags])
