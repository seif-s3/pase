import os
import sys
import flask_restful as rest
import csv
from flask import jsonify, request, make_response
from werkzeug.utils import secure_filename
from predictmod.app import app, api
from predictmod import utils


ALLOWED_EXTENSIONS = ['csv']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_csv(file):
    try:
        if not allowed_file(file.filename):
            return False, "Invalid file type. Only CSVs are allowed."

        reader = csv.DictReader(file)
        if len(reader.fieldnames) != 2:
            print >> sys.stderr, "Invalid fieldnames: {}".format(reader.fieldnames)
            return False, "Invalid fieldnames: {}".format(reader.fieldnames)

        if "timestamp" not in reader.fieldnames and "value" not in reader.fieldnames:
            print >> sys.stderr, "Missing header. CSV should have 2 columns: timestamp, value"
            return False, "Missing header. CSV should have 2 columns: timestamp, value"
        ln = 1
        for l in reader:
            ln += 1
            if len(l) != 2:
                print >> sys.stderr, "Encountered Bad line {}".format(ln)
                return False, "Encountered Bad line {}".format(ln)
        return True, None
    except Exception as e:
        print >> sys.stderr, e.message
        return False, e.message


class Upload(rest.Resource):
    def post(self):
        if 'file' not in request.files:
            return jsonify(
                {
                    'error': 'Request is missing file'
                }
            )
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify(
                {
                    'error': 'Invalid file'
                }
            )

        valid_csv, error_msg = validate_csv(file)
        if file and valid_csv:
            # Check if file already exists, in which case we'll overwrite it.
            overwritten = False
            filename = secure_filename(file.filename)
            datasets = utils.get_datasets()
            if filename in datasets:
                overwritten = True

            try:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Get datasets after saving file
                datasets = utils.get_datasets()
                return jsonify(
                    {
                        'uploaded': True,
                        'overwritten': overwritten,
                        'datasets': datasets
                    }
                )
            except:
                return jsonify(
                    {
                        'error': 'Failed to save file'
                    }
                )
        else:
            return jsonify(
                {
                    'error': error_msg
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