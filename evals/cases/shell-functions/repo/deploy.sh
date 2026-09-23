#!/bin/bash

# shellcheck source=lib/log.sh
source "$(dirname "$0")/lib/log.sh"

APP_DIR=/opt/myapp
RELEASE=$1

mkdir $APP_DIR/releases/$RELEASE
cp -r ./build/* $APP_DIR/releases/$RELEASE
rm $APP_DIR/current
ln -s $APP_DIR/releases/$RELEASE $APP_DIR/current
log Deployed release $RELEASE
