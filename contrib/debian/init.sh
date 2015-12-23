#!/bin/sh
### BEGIN INIT INFO
# Provides:          burp-ui
# Required-Start:    $network $local_fs $remote_fs
# Required-Stop:     $network $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: User interface for burp backup
# Description:       Burp UI work with burp backup and restore.
### END INIT INFO


DAEMON=/usr/local/bin/burp-ui
DESC=burp-ui
NAME=burp-ui
PIDFILE=/var/run/burp-ui.server.pid

# Exit if the package is not installed
[ -x $DAEMON ] || exit 0

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Function that starts the daemon/service

do_start()
{
        # Return
        #   0 if daemon has been started
        #   1 if daemon was already running
        #   2 if daemon could not be started
        start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON --test > /dev/null \
                || return 1
        start-stop-daemon --start --quiet --pidfile $PIDFILE --make-pidfile --background --exec $DAEMON -- \
                || return 2
}

# Function that stops the daemon/service

do_stop()
{
        # Return
        #   0 if daemon has been stopped
        #   1 if daemon was already stopped
        #   2 if daemon could not be stopped
        #   other if a failure occurred
        start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --pidfile $PIDFILE --name $NAME
        RETVAL="$?"
        [ "$RETVAL" = 2 ] && return 2
        #
        start-stop-daemon --stop --quiet --oknodo --retry=0/30/KILL/5 --exec $DAEMON
        [ "$?" = 2 ] && return 2
        # Many daemons don't delete their pidfiles when they exit.
        rm -f $PIDFILE
        return "$RETVAL"
}

case "$1" in
  start)
    [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC "
    do_start
    case "$?" in
                0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
                2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
        esac
  ;;
  stop)
        [ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC"
        do_stop
        case "$?" in
                0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
                2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
        esac
        ;;
  restart)
        do_stop
        do_start
        ;;
  *)
        echo "Usage: $SCRIPTNAME {start|stop|restart}" >&2
        exit 3
        ;;
esac

:
