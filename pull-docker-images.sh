#!/bin/bash

source .env
echo ${TAG_MPD}
COMPONENTS=("mpd" "icecast" "snapserver" "controller" "ui" "ympd")
TAGS=("${TAG_MPD}" "${TAG_ICECAST}" "${TAG_SNAPSERVER}" "${TAG_CONTROLLER}" "${TAG_UI}" "${TAG_YMPD}")

set -- "${COMPONENTS[@]}"

for TAG in "${TAGS[@]}"; do
    COMPONENT=$1; shift
    PULL='docker pull ghcr.io/mark-me/boelmuziek-'"$COMPONENT":"$TAG"
    eval $PULL
done
