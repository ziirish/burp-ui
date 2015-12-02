#!/bin/bash

PIP=$(which pip)
PYTHON=$(which python)
VERSION=$($PYTHON -V | cut -d' ' -f2)
ISROOT=0
UPDATED=0
BURP="https://git.ziirish.me/ziirish/burp.git"
BURP_VERSION="1.4.40"
BURP2_VERSION="2.0.28"

exit 0

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

#echo "install build requirements"
#update
#[ $ISROOT -eq 1 ] && apt-get install -y uthash-dev g++ make libssl-dev librsync-dev nodejs nodejs-legacy npm python$(perl -pe "s/\.\d+$//" <<<$VERSION)-dev

#echo "installing bower"
#npm install -g bower

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

#echo "downloading and compiling burp v${BURP2_VERSION}"
#BURP2_DIR=$(mktemp -d)
#cd $BURP2_DIR

#git clone $BURP
#cd burp
#git checkout tags/${BURP2_VERSION}
#./configure
#make

#cd $ROOT_PWD
#WORKING_DIR2=$(mktemp -d)

#echo "copying configuration files"
#cp -a test/burp2/config $WORKING_DIR2/
#sed -i "s|@WORKING_DIR@|${WORKING_DIR2}|" $WORKING_DIR2/config/burp.conf
#sed -i "s|@WORKING_DIR@|${WORKING_DIR2}|" $WORKING_DIR2/config/CA/CA.cnf

#echo "launching background burp-server"
#LOGFILE2=$(mktemp)
#$BURP2_DIR/burp/src/burp -F -c $WORKING_DIR2/config/burp.conf -g >$LOGFILE2 2>&1
#($BURP2_DIR/burp/src/burp -F -c $WORKING_DIR2/config/burp.conf >>$LOGFILE2 2>&1) &
#BURP2_PID=$!

echo "install virtualenv"
$PIP install virtualenv
mkdir py$VERSION
VIRTUALENV=$(which virtualenv)

echo "test python$VERSION"
$VIRTUALENV -p $PYTHON py$VERSION
source py${VERSION}/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install --upgrade -r test-requirements.txt

mkdir -p /etc/burp
cp burpui.sample.cfg /etc/burp/burpui.cfg
nosetests --with-coverage --cover-package=burpui test/test_burpui.py
ret=$?
rm /etc/burp/burpui.cfg

echo "cleanup"
deactivate
rm -rf py$VERSION

echo "Killing burp-server"
kill $BURP_PID || echo "Ooops KILL"
cat $LOGFILE

#echo "Killing burp2-server"
#kill $BURP2_PID || echo "Ooops KILL"
#cat $LOGFILE2

echo "removing temp files/dirs"
rm -rf $LOGFILE $LOGFILE2 $BURP2_DIR $BURP_DIR $WORKING_DIR $WORKING_DIR2 || echo "Ooops RM"

echo "That's it!"

echo "Return: $ret"

exit $ret
