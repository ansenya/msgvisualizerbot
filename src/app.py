from flask import Flask, send_from_directory
import os

app = Flask(__name__)


@app.route('/bg/<path:filename>')
def get_photo(filename):
    photo_folder = os.path.join(os.getcwd(), 'src', 'bg')
    return send_from_directory(photo_folder, filename)


if __name__ == '__main__':
    app.run(debug=True)
