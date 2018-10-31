#!/bin/bash

PYTHON=$(which python)

echo "test requirements"

[ -x "$PYTHON" ] && {
    echo "python seems to be installed"
} || {
    echo "python is missing..."
    exit 1
}

pip install -r requirements.txt
pip install wheel


echo "building dist"
$PYTHON setup.py sdist bdist_wheel bdist_egg
mkdir meta
cd pkgs
for pkg in *
do
    [ "$pkg" = "burp-ui-tpl" -o -f "$pkg" ] && continue
    cd $pkg
    $PYTHON setup.py sdist bdist_wheel bdist_egg
    find dist -exec cp "{}" ../../meta/ \;
    cd ..
done
cd ..

exit 0
