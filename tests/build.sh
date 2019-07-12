#!/bin/sh

pip install wheel

echo "building dist"
python setup.py sdist bdist_wheel bdist_egg
mkdir meta
cd pkgs
for pkg in *
do
    [ "$pkg" = "burp-ui-tpl" -o -f "$pkg" ] && continue
    cd $pkg
    python setup.py sdist bdist_wheel bdist_egg
    find dist -type f -exec cp "{}" ../../meta/ \;
    cd ..
done
cd ..

exit 0
