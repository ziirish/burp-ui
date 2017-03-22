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

pip install --upgrade pip
pip install -r requirements.txt
pip install wheel

echo "building dist"
[ "$(sed 's/\([[:digit:]]*\)\..*$/\1/' <<<$VERSION)" -eq 2 ] && {
    $PYTHON setup.py sdist bdist_wheel bdist_egg
    mkdir meta
    cd pkgs
    for pkg in *
    do
        cd $pkg
        $PYTHON setup.py sdist bdist_wheel bdist_egg
        find dist -exec cp "{}" ../../meta/ \;
        cd ..
    done
    cd ..
} || {
    $PYTHON setup.py bdist_egg
    mkdir meta
    cd pkgs
    for pkg in *
    do
        [ -f "$pkg" ] && continue
        cd $pkg
        $PYTHON setup.py bdist_egg
        find dist -exec cp "{}" ../../meta/ \;
        cd ..
    done
    cd ..
}

# Not useful anymore since we are using artifacts
#echo "publishing build"
#cd dist
#tgz=$(ls -1rt burp-ui*.tar.gz | tail -1)
#egg=$(ls -1rt burp_ui*.egg | tail -1)
#whl=$(ls -1rt burp_ui*.whl | tail -1)
#cd ..
#cp -vf dist/burp-ui*.tar.gz /pub/ 2>/dev/null
#cp -vf dist/burp_ui*.egg /pub/ 2>/dev/null
#cp -vf dist/burp_ui*.whl /pub/ 2>/dev/null
#
#cd /pub
##rm burp-ui.dev.tar.gz burp_ui-dev-py${VERSION}.egg burp_ui-dev-py2.py3-none-any.whl 2>/dev/null
#[ -n "$tgz" ] && ln -sf $tgz burp-ui.dev.tar.gz
#[ -n "$egg" ] && ln -sf $egg burp_ui-dev-py${VERSION}.egg
#[ -n "$whl" ] && ln -sf $whl burp_ui-dev-py2.py3-none-any.whl

exit 0
