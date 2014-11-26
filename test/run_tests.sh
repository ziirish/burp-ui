#!/bin/bash

echo "install lib devel..."
apt-get update
apt-get -y install python-pip python
#apt-get -y install python2.7-dev python2.6-dev libsasl2-dev

echo "check files"
pwd
ls -la
file burp-ui.py
file burpui.cfg
file test/test_burpui.py

echo "install virtualenv"
pip install virtualenv
mkdir py2.7

echo "test python2.7"
virtualenv -p /usr/bin/python2.7 py2.7
source py2.7/bin/activate
pip install -r requirements.txt
pip install -r test-requirements.txt
LOG=$(mktemp)
(
nosetests --with-coverage --cover-package=burpui test/test_burpui.py 2>&1 >$LOG
ret=$?
cat $LOG
grep TOTAL $LOG | awk '{ print "TOTAL: "$4; }'
exit $ret
)
ret2=$?
rm $LOG
deactivate

echo "That's it!"

echo "Return: $ret2"

exit $ret2
