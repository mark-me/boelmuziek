#!/usr/bin/env bash

set -euo pipefail

DIR_MUSIC=~/Music
DIR_DATA=~/Development/data/boelmuziek
DIR_MPD=$DIR_DATA/mpd
DIR_MPD_DB=$DIR_MPD/db
DIR_MPD_PLAYLISTS=$DIR_MPD/playlists
DIR_MPD_STATE=$DIR_MPD/mpdstate
SNAPFIFO=$DIR_MPD_STATE/snapfifo

if [ ! -d ${DIR_MPD_DB} ]; then
    sudo mkdir -p ${DIR_MPD_DB}
fi

if [ ! -d ${DIR_MPD_PLAYLISTS} ]; then
    sudo mkdir -p ${DIR_MPD_PLAYLISTS}
fi

if [ ! -d ${DIR_MPD_STATE} ]; then
    sudo mkdir -p ${DIR_MPD_STATE}
fi

if [ ! -p  ${SNAPFIFO} ]; then
    sudo mkfifo ${SNAPFIFO}
    sudo chmod a+rw ${SNAPFIFO}
fi

echo Set permissions for the stack\'s data directories
sudo chmod -R a+rw ${DIR_DATA}
