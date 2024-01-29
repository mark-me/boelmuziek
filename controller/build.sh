#!/bin/bash
VERSION_ID='v0.0.4'
COMPONENT=controller
PUSH_IMAGES=false  # Default value for pushing images

# Check for the optional parameter
while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        -p|--push)
        PUSH_IMAGES=true
        shift
        ;;
        *)  # Unknown option
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# Pull docker images
docker pull ghcr.io/mark-me/boelmuziek-$COMPONENT:$VERSION_ID
docker pull ghcr.io/mark-me/boelmuziek-$COMPONENT:latest

# App
docker build -t ghcr.io/mark-me/boelmuziek-$COMPONENT:$VERSION_ID -t ghcr.io/mark-me/boelmuziek-$COMPONENT:latest .

# Optionally push Docker images
if [ "$PUSH_IMAGES" = true ]; then
    docker push ghcr.io/mark-me/boelmuziek-$COMPONENT:$VERSION_ID
    docker push ghcr.io/mark-me/boelmuziek-$COMPONENT:latest
fi
