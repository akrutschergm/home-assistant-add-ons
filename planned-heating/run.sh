#!/usr/bin/with-contenv bashio

bashio::log.info "Starting..."

CONFIG_PATH=/data/options.json
LOG_LEVEL="$(bashio::config 'log_level')"

python3 /code/main.py -c /data/options.json -d /data --log-level "$LOG_LEVEL"
