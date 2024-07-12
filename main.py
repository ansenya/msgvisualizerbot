import sys

from flask import Flask, send_from_directory
import os
import config

app = Flask(__name__)


@app.route('/bg/<path:filename>')
def get_photo(filename):
    photo_folder = config.Environment.bg_path
    return send_from_directory(photo_folder, filename)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', )
