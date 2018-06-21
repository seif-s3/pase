#!/bin/sh

BIND="0.0.0.0:8080"
WORKER="gevent"
NWORKERS=1

gunicorn server:app \
    --bind $BIND \
    --worker-class $WORKER \
    --workers $NWORKERS \
    --log-level INFO
