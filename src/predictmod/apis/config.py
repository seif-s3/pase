import os
import sys
import flask_restful as rest
from flask_restful import reqparse
from flask import jsonify
from predictmod.app import api, app


def makeConfigParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('influx_host', required=True, nullable=False)
    parser.add_argument('influx_db', required=True, nullable=False)
    parser.add_argument('influx_user', required=True, nullable=False)
    parser.add_argument('influx_pass', required=True, nullable=False)
    parser.add_argument('test', nullable=False)
    return parser


class InfluxConfig(rest.Resource):
    def post(self):
        args = makeConfigParser().parse_args()
        try:
            app.config['INFLUX_HOST'] = args.get('influx_host')
            app.config['INFLUX_DB'] = args.get('influx_db')
            app.config['INFLUX_USER'] = args.get('influx_user')
            app.config['INFLUX_PASS'] = args.get('influx_pass')
            # Restart gunicorn gracefully to apply changes
            # http://docs.gunicorn.org/en/stable/faq.html
            os.system('kill -HUP masterpid')
        except Exception as e:
            print >> sys.stderr, 'Error reloading server to update config!\n', e

    def get(self):
        return jsonify(
            {
                'influx_host': app.config['INFLUX_HOST'],
                'influx_db': app.config['INFLUX_DB'],
                'influx_user': app.config['INFLUX_USER'],
                'influx_pass': app.config['INFLUX_PASS']
            }
        )

api.add_resource(InfluxConfig, '/config/influx')
