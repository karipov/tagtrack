from pathlib import Path

from peewee import SqliteDatabase, Model
from peewee import TextField, IntegerField, CompositeKey


db = SqliteDatabase(Path.cwd().joinpath('src/config/tags.db'))


class Tags(Model):
    chat_id = IntegerField()
    message_id = IntegerField()
    user_id = IntegerField()
    card_id = TextField()
    short_url = TextField()

    class Meta:
        primary_key = CompositeKey('chat_id', 'message_id')
        database = db


db.connect()
db.create_tables([Tags])
