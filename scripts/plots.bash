#!/bin/bash
file=$1
min=$2
offset=$3

echo plot minute $min from $file

python main.py --plot --pbeg $(( $min * 60000 + $offset )) --pend $(( ($min + 1)*60000 + $offset ))