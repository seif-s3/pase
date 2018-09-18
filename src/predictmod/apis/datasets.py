import os
import sys
import flask_restful as rest
import csv
import urllib
from flask import jsonify, request, render_template, make_response, flash, redirect, send_file
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
            return False, "Error: Invalid fieldnames: {}".format(reader.fieldnames)

        if "timestamp" not in reader.fieldnames and "value" not in reader.fieldnames:
            print >> sys.stderr, "Missing header. CSV should have 2 columns: timestamp, value"
            return False, "Error: Missing header. CSV should have 2 columns: timestamp, value"
        ln = 1
        for l in reader:
            ln += 1
            if len(l) != 2:
                print >> sys.stderr, "Encountered Bad line {}".format(ln)
                return False, "Error: Encountered Bad line {}".format(ln)
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
                # We need to seek to the beginning of the file to save since reading it moved
                # the pointer ot the last byte and thus saving would save an empty file
                file.stream.seek(0)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                flash_msg = "Your file was uploaded! "
                if overwritten:
                    flash_msg += "Note that an older dataset was overwritten by this operation."

                flash(flash_msg)
                return redirect('/datasets')

            except:
                flash('Error: Failed to save file!')
                return redirect('/datasets')

        else:
            flash(error_msg)
            return redirect('/datasets')

    def get(self):
        template = render_template('index.html', files=utils.get_datasets(), headers='')
        headers = {'Content-Type': 'text/html'}
        return make_response(template, 200, headers)


class Download(rest.Resource):

    def get(self, filename):
        filename = urllib.unquote(filename)
        base_directory = app.config['UPLOAD_FOLDER']
        if os.path.isfile(filename):
            if os.path.dirname(filename) == base_directory.rstrip("/"):
                return send_file(filename, as_attachment=True)
        else:
            return {'error': "File not found!"}
        return None

api.add_resource(Upload, '/datasets')
api.add_resource(Download, '/download/<filename>')
