#!/bin/sh

[ "`uname`" == "Darwin" ] || exec echo "Script support only Darwin (macOS)"

echo -n "Install?:"
read ANSWER
if [ "x$ANSWER" == "xy" -o "x$ANSWER" == "xY" ]
then
    launchctl load ~/Library/LaunchAgents/kondrashin.mikhail.changesrecorder.01.plist
    exit 0
fi
echo -n  "Uninstall?:"
read ANSWER
if [ "x$ANSWER" ==  "xy" -o "x$ANSWER" == "xY" ]
then
    launchctl unload ~/Library/LaunchAgents/kondrashin.mikhail.changesrecorder.01.plist
    exit 0
fi