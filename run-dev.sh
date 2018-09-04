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

if [ -f config.py ]; then
    CONFIG_FILE="config.py"
else
    CONFIG_FILE="config-example.py"
fi

mkdir -p srv

docker run -it --rm \
    --name magbot \
    --mount type=bind,source=$PWD,target=/srv/plugins/magbot \
    --mount type=bind,source=$PWD/$CONFIG_FILE,target=/srv/config.py \
    --mount type=bind,source=$PWD/srv,target=/srv \
    -e BOT_USERNAME=$BOT_USERNAME \
    -e BOT_TOKEN=$BOT_TOKEN \
    magfest/docker-errbot:latest
