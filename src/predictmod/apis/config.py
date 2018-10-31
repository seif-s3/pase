import os
import sys
import flask_restful as rest
from flask_restful import reqparse
from flask import jsonify
from predictmod.app import api, app
from predictmod.app import update_model_job


def makeInfluxConfigParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('influx_host', required=True, nullable=False)
    parser.add_argument('influx_db', required=True, nullable=False)
    parser.add_argument('influx_user', required=True, nullable=False)
    parser.add_argument('influx_pass', required=True, nullable=False)
    return parser


def makeTestConfigParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('test', required=True, nullable=False)
    return parser


def makeCronConfigParser(for_update=False):
    parser = reqparse.RequestParser(trim=True)
    parser.add_argument('interval', required=True, type=int, nullable=False)
    return parser


class InfluxConfig(rest.Resource):
    def post(self):
        args = makeInfluxConfigParser().parse_args()
        try:
            app.config['INFLUX_HOST'] = args.get('influx_host')
            app.config['INFLUX_DB'] = args.get('influx_db')
            app.config['INFLUX_USER'] = args.get('influx_user')
            app.config['INFLUX_PASS'] = args.get('influx_pass')
            return jsonify(
                {
                    'influx_host': app.config['INFLUX_HOST'],
                    'influx_db': app.config['INFLUX_DB'],
                    'influx_user': app.config['INFLUX_USER'],
                    'influx_pass': app.config['INFLUX_PASS']
                }
            )
        except Exception as e:
            print >> sys.stderr, 'Error updating Influx Config!\n', e

    def get(self):
        return jsonify(
            {
                'influx_host': app.config['INFLUX_HOST'],
                'influx_db': app.config['INFLUX_DB'],
                'influx_user': app.config['INFLUX_USER'],
                'influx_pass': app.config['INFLUX_PASS']
            }
        )


class CronConfig(rest.Resource):
    def post(self):
        args = makeCronConfigParser().parse_args()
        try:
            print >> sys.stderr, 'Rescheduling Cron Job to {} minutes'.format(args['interval'])
            app.config['RETRAIN_INTERVAL'] = args['interval']
            update_model_job.reschedule('interval', minutes=args['interval'])
            return jsonify(
                {
                    'interval': app.config['RETRAIN_INTERVAL']
                }
            )
        except Exception as e:
            print >> sys.stderr, 'Error rescheduling Cron Job!\n', e

    def get(self):
        return jsonify(
            {
                'interval': app.config['RETRAIN_INTERVAL']
            }
        )


class TestConfig(rest.Resource):
    def post(self):
        args = makeTestConfigParser().parse_args()
        try:
            app.config['TEST_CONFIG'] = args.get('test')
            return jsonify(
                {
                    'test_config': app.config.get('TEST_CONFIG'),
                }
            )
        except Exception as e:
            print >> sys.stderr, 'Error updating config!\n', e

    def get(self):
        return jsonify(
            {
                'test_config': app.config.get('TEST_CONFIG'),
            }
        )

api.add_resource(InfluxConfig, '/config/influx')
api.add_resource(CronConfig, '/config/cron')
api.add_resource(TestConfig, '/config/test')
