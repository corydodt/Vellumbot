#!/bin/bash
## Bootstrap setup for vellumbot

umask 002

if [ "$1" == "force" ]; then
    force="force"
else
    force=""
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

