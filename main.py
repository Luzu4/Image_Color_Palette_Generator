import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
from colormap import rgb2hex
UPLOAD_FOLDER = 'static/uploads/'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.jinja_env.filters['zip'] = zip
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def palette(img):
    arr = np.asarray(img)
    palette, index = np.unique(asvoid(arr).ravel(), return_inverse=True)
    palette = palette.view(arr.dtype).reshape(-1, arr.shape[-1])
    count = np.bincount(index)
    order = np.argsort(count)
    percents = count[order[::-1]]/count.sum()
    percents = [percent*100 for percent in percents]
    return palette[order[::-1]], percents


def asvoid(arr):
    arr = np.ascontiguousarray(arr)
    return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        try:
            number_of_colors = int(request.form['number_of_colors'])
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img = Image.open('static/uploads/' + filename, 'r').convert('RGB')
            if number_of_colors <= len(palette(img)[0]):
                top_colors = palette(img)[0][:number_of_colors]
                percent_of_colors = palette(img)[1][:number_of_colors]
                top_colors = [rgb2hex(color[0], color[1], color[2]) for color in top_colors]
                return render_template('upload.html', filename=filename, top_colors=top_colors, top_percents=percent_of_colors)
            else:
                flash('Wrong number of colors.')
                return redirect(request.url)
        except ValueError:
            flash('You have to type number')
            return redirect(request.url)
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename, code=301))


if __name__ == "__main__":
    app.run(debug=True)