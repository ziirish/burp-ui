#!/bin/bash 
# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

USR=${1:-${USER}}
IMAGES="2.7 3.4"

echo "[+] Building docker images..."
for img in $IMAGES
do
        echo "[-] ${img}"
        docker build -t ${USR}/py${img}:${img} ${SCRIPTPATH}/docker/py${img}
done

echo "[+] Running tests..."
for img in $IMAGES
do
        echo "[-] ${img}"
        docker run -it --rm -v ${SCRIPTPATH}/..:/home/burp-ui ${USR}/py${img}:${img} bash -c "cd /home/burp-ui && /home/burp-ui/test/run_tests.sh"
done
