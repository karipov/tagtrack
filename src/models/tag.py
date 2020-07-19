from pathlib import Path
from tinydb import TinyDB, Query

__all__ = ['Storage', 'Tags']

# from peewee import SqliteDatabase, Model
# from peewee import TextField, IntegerField, CompositeKey


# db = SqliteDatabase(Path.cwd().joinpath('src/config/tags.db'))
Storage = TinyDB(Path.cwd().joinpath('src/config/tags.json'))
Tags = Query()


# class Tags(Model):
#     # primary keys
#     chat_id = IntegerField()
#     message_id = IntegerField()

#     reply_message_id = IntegerField()
#     user_id = IntegerField()
#     card_id = TextField()
#     short_url = TextField()

#     class Meta:
#         primary_key = CompositeKey('chat_id', 'message_id')
#         database = db


# db.connect()
# db.create_tables([Tags])
