#!/bin/bash 
# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")
me=$(basename $0)

# prints error in all cases
function myerror() {
        echo "[e] $*" >&2
}

# prints the help menu and exit
function usage() {
        cat <<EOF
$me [options...]
usage:
        -u, --user      User prefix for images
        -t, --test      List of tests to run separated by a coma
        -h, --help      Print this menu and exit
EOF
        ret=${1:-0}
        exit $ret
}

# options may be followed by one colon to indicate they have a required argument
options=$(getopt -n "$me" -o "hu:t::" -l "help,user:,test::" -- "$@") || {
        # something went wrong, getopt will put out an error message for us
        usage 1
}

set -- $options

if [ "$(getopt --version)" = " --" ]; then
        # bsd getopt - skip configuration declarations
        nb_delims_to_remove=2
        while [ $# -gt 0 ]; do
                if [ $1 = "--" ]; then
                        shift
                        nb_delims_to_remove=$(expr $nb_delims_to_remove - 1)
                        if [ $nb_delims_to_remove -lt 1 ]; then
                                break
                        fi
                fi

                shift
        done
fi

while [ $# -gt 0 ]
do
        case $1 in
                -h|--help) usage ;;
                # for options with required arguments, an additional shift is required
                -u|--user) user=$(sed "s/^.//;s/.$//" <<<$2) ; shift ;;
                -t|--test) [ -z "$tests" ] && tests=$(sed "s/,/ /g;s/^.//;s/.$//" <<<$2) || tests="$tests $(sed 's/,/ /g;s/^.//;s/.$//' <<<$2)" ; shift ;;
                (--) shift; break ;;
                (-*) myerror "$me: error - unrecognized option $1"; usage 1 ;;
                (*) break ;;
        esac
        shift
done

for arg; do [ -z "${tests}" ] && tests=$(sed "s/,/ /g;s/^.//;s/.$//" <<<$arg) || tests="$tests $(sed 's/,/ /g;s/^.//;s/.$//' <<<$arg)"; done

USR=${user:-${USER}}
IMAGES="${tests:-2.7 3.4}"

echo "[+] Building docker images..."
for img in $IMAGES
do
        [ -d ${SCRIPTPATH}/docker/py${img} ] || continue
        echo "[-] ${img}"
        docker build -t ${USR}/py${img}:${img} ${SCRIPTPATH}/docker/py${img}
done

echo "[+] Running tests..."
for img in $IMAGES
do
        [ -d ${SCRIPTPATH}/docker/py${img} ] || continue
        echo "[-] ${img}"
        docker run -it --rm -v ${SCRIPTPATH}/..:/home/burp-ui ${USR}/py${img}:${img} /bin/bash -c "cd /home/burp-ui && /home/burp-ui/test/run_tests.sh"
done
