#!/bin/bash
## Bootstrap setup for vellumbot

umask 002

if [ "$1" == "force" ]; then
    force="force"
else
    force=""
fi

cat <<EOF
:: This script will check your environment to make sure Goonmill is
:: ready to run, and do any one-time setup steps necessary.
::
:: Please check for any errors below, and fix them.
EOF

export errorStatus=""

function testPython()
# Use: testPython "Software name" "python code"
#  If "python code" has no output, we pass.
# 
#  If there is any output, the last line is considered an error message, and
#  we print it.  Then we set the global errorStatus.
# 
#  "python code" should not write to stderr if possible, so use 2>&1 to
#  redirect to stdout.
{
    software="$1"
    line=$(python -c "$2" 2>&1 | tail -1)

    if [ -n "$line" ]; then
        echo "** Install $software ($line)"
        errorStatus="error"
    else
        echo "OK $software"
    fi
}

testPython "PySQLite2" 'import pysqlite2.dbapi2'
testPython "Playtools" 'import playtools'
testPython "Goonmill" 'import goonmill'
testPython "Storm" 'import storm.locals'
testPython "zope.interface" 'import zope.interface'
t="from twisted import __version__ as v; assert v>='2.5.0', 'Have %s' % (v,)"
testPython "Twisted 2.5" "$t"
testPython "simpleparse" 'import simpleparse'
testPython "Python 2.5" 'import xml.etree'

if [ "$errorStatus" == "error" ]; then
    echo "** Errors occurred.  Please fix the above errors, then re-run this script."
    exit 1
fi

if [ -n "$force" ]; then
    echo ::
    echo ':: force is in effect: removing database files!'
    set -x
    rm -f vellumbot/user.db*
    set +x
fi

userdb=vellumbot/user.db
if [ ! -r "$userdb" ]; then
    echo ::
    echo :: $userdb
    # run python to produce the sql script that sqlite3 will import
    sqlite3 -init <(python vellumbot/usersql.py) $userdb '.exit' || exit 1
    sqlite3 -init vellumbot/sql/dummy.sql $userdb '.exit' || exit 1
    chmod 664 $userdb
else
    echo "** ${userdb} already exists, not willing to overwrite it!"
    echo ::
    echo :: If you have already run bootstrap.sh once, this is not an error.
    echo ::
fi

echo ::
echo :: Done.

