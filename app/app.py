import flask
from flask_restful import Api


app = flask.Flask('pase-fuoracle')
api = Api(app, catch_all_404s=True)


@app.route('/')
def hello_world():
    return 'Hello docker!'

import apis.predict

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
