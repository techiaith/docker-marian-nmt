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


_dc_build() {
    local service=$1
    local user=$2
    local supervisord_conf=$3
    local supervisord_conf_dest=$4
    shift 4
    local volume_dirs=$@
    local uid=$(id -u)
    local gid=$(getent group docker | cut -d: -f3)
    mkdir -p -m 770 $volume_dirs
    chown -R ${uid}:${gid} $volume_dirs
    cp $supervisord_conf $supervisord_conf_dest/.
    _dc build $service --build-arg uid=$UID \
               --build-arg gid=$gid \
	       --build-arg app_user=$user \
	       --build-arg gitlab_oauth_token=$GITLAB_OAUTH_TOKEN \
	       --force-rm
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

