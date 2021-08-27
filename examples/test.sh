#!/usr/bin/env bash
set -Eeuo pipefail

while :
do
  sleep 1
  if [ -f "config.json" ];
  then
    PORT=`cat config.json | jq '.schema[] | select(.key=="port").value'`
    SOMETHING_ELSE=`cat config.json | jq '.schema[] | select(.key=="something_else").value'`
  else
    continue
  fi
  if [ -n "$PORT" ]
  then
    echo "Hello, PORT: ${PORT}, SOMETHING_ELSE: ${SOMETHING_ELSE}"
  fi
done