#!/bin/bash

PYTHON=$(which python)
ISROOT=0
UPDATED=0

function update() {
    [ $UPDATED -eq 0 ] && [ $ISROOT -eq 1 ] && {
        apt-get update
        UPDATED=1
    }
    return 0
}

echo "test requirements"
[ $UID -eq 0 ] && ISROOT=1

[ -x "$PYTHON" ] && {
    echo "python seems to be installed"
} || {
    echo "python is missing..."
    exit 1
}

echo "install build requirements"
update
[ $ISROOT -eq 1 ] && apt-get install -y nodejs nodejs-legacy npm

echo "installing bower"
npm install -g bower

echo "downloading libs"
bower install

echo "building dist"
$PYTHON setup.py sdist

echo "publishing build"
cp -vf dist/burp-ui*.tar.gz /pub/burp-ui.dev.tar.gz

exit 0
