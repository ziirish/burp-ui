#!/bin/bash

PYTHON=$(which python)
ISROOT=0
UPDATED=0
VERSION=$($PYTHON -V 2>&1 | cut -d' ' -f2)

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

#echo "install build requirements"
#update
#[ $ISROOT -eq 1 ] && apt-get install -y nodejs nodejs-legacy npm

#echo "installing bower"
#npm install -g bower

echo "downloading libs"
bower install

echo "building dist"
[ "$(sed 's/\([[:digit:]]*\)\..*$/\1/' <<<$VERSION)" -eq 2 ] && $PYTHON setup.py sdist
$PYTHON setup.py bdist_egg

echo "publishing build"
cp -vf dist/burp-ui*.tar.gz /pub/burp-ui.dev.tar.gz 2>/dev/null
cp -vf dist/burp_ui*.egg /pub/burp_ui-dev-py${VERSION}.egg 2>/dev/null

exit 0
