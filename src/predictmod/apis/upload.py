import os
import flask_restful as rest
from os import listdir
from os.path import isfile, join
from flask import flash, jsonify, request, redirect, make_response
from werkzeug.utils import secure_filename
from predictmod.app import app, api

ALLOWED_EXTENSIONS = ['csv']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Upload(rest.Resource):
    def post(self):
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            datasets = [
                f for f in listdir(
                    app.config['UPLOAD_FOLDER']) if isfile(join(app.config['UPLOAD_FOLDER'], f))
            ]
            return jsonify(
                {
                    'uploaded': True,
                    'datasets': datasets
                }
            )

    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response('''<h1>Upload new Dataset</h1>\
        <form method=post enctype=multipart/form-data>\
        <input type=file name=file>\
        <input type=submit value=Upload>\
        </form>''', 200, headers)


api.add_resource(Upload, '/upload')
