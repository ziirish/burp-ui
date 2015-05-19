#!/bin/bash

PIP=$(which pip)
PYTHON=$(which python2.7)
ISROOT=0

[ $UID -eq 0 ] && ISROOT=1


echo "test requirements"
[ $ISROOT -eq 1 ] && apt-get update

[ -x "$PIP" ] && {
    echo "python-pip seems to be installed"
} || {
    echo "python-pip is missing... Installing it"
    [ $ISROOT -eq 1 ] && apt-get -y install python-pip
}

[ -x "$PYTHON" ] && {
    echo "python2.7 seems to be installed"
} || {
    echo "python2.7 is missing... Installing it"
    [ $ISROOT -eq 1 ] && apt-get -y install python2.7 python
}

echo "install lib devel..."
apt-get update
apt-get -y install python-pip python
##apt-get -y install python2.7-dev python2.6-dev libsasl2-dev

echo "check files"
pwd
ls -la
file burp-ui.py
file burpui.cfg
file test/test_burpui.py

echo "install virtualenv"
$PIP install virtualenv
mkdir py2.7

echo "test python2.7"
virtualenv -p $PYTHON py2.7
source py2.7/bin/activate
pip install -r requirements.txt
pip install -r test-requirements.txt
LOG=$(mktemp)
(
    nosetests --with-coverage --cover-package=burpui test/test_burpui.py
    exit $?
) &>$LOG
ret=$?
cat $LOG
grep TOTAL $LOG | awk '{ print "TOTAL: "$4; }'
rm $LOG
deactivate

echo "That's it!"

echo "Return: $ret"

exit $ret
