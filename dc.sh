#!/bin/bash

docker compose version 2>&1 > /dev/null
if [ $? -eq 0 ]; then
    compose="docker compose"
else
    compose="docker-compose"
fi

_dc() {
    local args=$@
    $compose $args
}

_dc_up() {
    local service=$1
    _dc up --detach $service
}

supervisorctl() {
    local service=$1
    shift 1
    _dc exec $service supervisorctl $@
}

$*

