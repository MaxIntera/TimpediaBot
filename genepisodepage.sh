#!/usr/bin/env bash

echo "Generating article..."
python hirssparser.py $1
echo "Editing wiki..."
cat formatted.txt | python editpage.py $2
rm formatted.txt
echo "Process Complete.\n"
