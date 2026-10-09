#!/bin/sh
cd "$(dirname "$0")"
SKIPCLIPS=1 node snap.js frames 0 1660 > f1.log 2>&1 &
SKIPCLIPS=1 node snap.js frames 1660 3318 > f2.log 2>&1 &
wait; echo ok > frames.done
