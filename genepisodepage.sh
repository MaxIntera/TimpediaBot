#!/usr/bin/env bash

python hirssparser.py $1
cat formatted.txt | python editpage.py $2
rm formatted.txt
