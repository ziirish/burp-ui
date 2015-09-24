#!/bin/bash

PIP=$(which pip)
PYTHON=$(which python)
VERSION=$($PYTHON -V | cut -d' ' -f2)
ISROOT=0
UPDATED=0
BURP="https://git.ziirish.me/ziirish/burp.git"
BURP_VERSION="1.4.40"

function update() {
    [ $UPDATED -eq 0 ] && [ $ISROOT -eq 1 ] && {
        apt-get update
        UPDATED=1
    }
    return 0
}

echo "test requirements"
[ $UID -eq 0 ] && ISROOT=1

#[ $ISROOT -eq 1 ] && apt-get update

[ -x "$PIP" ] && {
    echo "python-pip seems to be installed"
} || {
    echo "python-pip is missing..."
    exit 1
}

[ -x "$PYTHON" ] && {
    echo "python seems to be installed"
} || {
    echo "python is missing..."
    exit 1
}

echo "install build requirements"
update
[ $ISROOT -eq 1 ] && apt-get install -y uthash-dev g++ make libssl-dev librsync-dev python$(perl -pe "s/\.\d+$//" <<<$VERSION)-dev

echo "downloading and compiling burp v${BURP_VERSION}"
ROOT_PWD=`pwd`
BURP_DIR=$(mktemp -d)
cd $BURP_DIR

git clone $BURP
cd burp
git checkout tags/${BURP_VERSION}
./configure --disable-ipv6
make

cd $ROOT_PWD
WORKING_DIR=$(mktemp -d)

echo "copying configuration files"
cp -a test/burp/config $WORKING_DIR/
sed -i "s|@WORKING_DIR@|${WORKING_DIR}|" $WORKING_DIR/config/burp.conf
sed -i "s|@WORKING_DIR@|${WORKING_DIR}|" $WORKING_DIR/config/CA/CA.cnf

echo "launching background burp-server"
LOGFILE=$(mktemp)
$BURP_DIR/burp/src/burp -F -c $WORKING_DIR/config/burp.conf -g >$LOGFILE 2>&1
($BURP_DIR/burp/src/burp -F -c $WORKING_DIR/config/burp.conf >>$LOGFILE 2>&1) &
BURP_PID=$!

##echo "install lib devel..."
##apt-get update
##apt-get -y install python-pip python
##apt-get -y install python2.7-dev python2.6-dev libsasl2-dev

echo "check files"
pwd
ls -la
file burp-ui.py
file burpui.cfg
file test/test_burpui.py

echo "install virtualenv"
$PIP install virtualenv
mkdir py$VERSION
VIRTUALENV=$(which virtualenv)

echo "test python$VERSION"
$VIRTUALENV -p $PYTHON py$VERSION
source py${VERSION}/bin/activate
pip install -r requirements.txt
pip install -r test-requirements.txt


nosetests --with-coverage --cover-package=burpui test/test_burpui.py
ret=$?

echo "cleanup"
deactivate
rm -rf py$VERSION

echo "Killing burp-server"
kill $BURP_PID || echo "Ooops KILL"
cat $LOGFILE

echo "removing temp files/dirs"
rm -rf $LOGFILE $BURP_DIR $WORKING_DIR || echo "Ooops RM"

echo "That's it!"

echo "Return: $ret"

exit $ret
