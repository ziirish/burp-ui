#!/bin/bash

PYTHON=$(which python)
VERSION=$($PYTHON -V 2>&1 | cut -d' ' -f2)

echo "test requirements"

[ -x "$PYTHON" ] && {
    echo "python seems to be installed"
} || {
    echo "python is missing..."
    exit 1
}

echo "building dist"
[ "$(sed 's/\([[:digit:]]*\)\..*$/\1/' <<<$VERSION)" -eq 2 ] && $PYTHON setup.py sdist bdist_wheel
$PYTHON setup.py bdist_egg

echo "publishing build"
cp -vf dist/burp-ui*.tar.gz /pub/burp-ui.dev.tar.gz 2>/dev/null
cp -vf dist/burp_ui*.egg /pub/burp_ui-dev-py${VERSION}.egg 2>/dev/null
cp -vf dist/burp_ui*.whl /pub/burp_ui-dev-py2.py3-none-any.whl 2>/dev/null

exit 0
