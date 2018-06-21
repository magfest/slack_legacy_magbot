#! /bin/bash

if [ "$1" != "" ]; then
    BOT_USERNAME=$1
fi

if [ "$2" != "" ]; then
    BOT_TOKEN=$2
fi

if [ -z "$BOT_USERNAME" ] || [ -z "$BOT_TOKEN" ]; then
    echo "Usage: $0 BOT_USERNAME BOT_TOKEN"
    echo ""
    echo "BOT_USERNAME and BOT_TOKEN may also be specified as environment variables."
    exit 1
fi

docker run -it --rm \
    --name magbot \
    -v $PWD:/srv/plugins/magbot \
    --mount type=bind,source=$PWD/config-dev.py,target=/srv/config.py \
    -e BOT_USERNAME=$BOT_USERNAME \
    -e BOT_TOKEN=$BOT_TOKEN \
    magfest/docker-errbot:latest
