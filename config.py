import os
from os import environ


class Environment:
    token = environ.get('TOKEN')
    flask_path = os.environ.get('FLASK_PATH') or 'localhost:5000'
    dbpath = os.path.abspath('db/database.db')
    root_path = os.path.abspath('.')
    bg_path = os.path.abspath('bg')
    index_path = os.path.abspath('res/index.html')
    temp_path = os.path.abspath('temp')

    def check(self):
        if self.token is None:
            raise ValueError('No token')
