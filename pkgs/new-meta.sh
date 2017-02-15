#!/bin/bash

TPLWORD="tpl"
TPLDIR="burp-ui-"
TPLMOD="burpui_"
TPLEXP="##TPL##"
MOD=$1
DEST="${TPLDIR}${MOD}"

usage() {
	echo "usage: $0 <name>"
	exit 0
}

[ -z "$MOD" ] && usage
[ -e "$DEST" ] && {
	echo "Module '$MOD' already exist!"
	exit 1
}

cp -r "${TPLDIR}${TPLWORD}" "$DEST"
cd $DEST
mv "${TPLMOD}${TPLWORD}" "${TPLMOD}${MOD}"
find . -type f | xargs sed -i "s/$TPLEXP/$MOD/g"

echo "New meta-package $DEST created"
echo "Don't forget to edit the $DEST/setup.py file accordingly"
