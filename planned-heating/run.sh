#!/usr/bin/with-contenv bashio

bashio::log.info "Starting..."

python3 /code/main.py -c /data/options.json
