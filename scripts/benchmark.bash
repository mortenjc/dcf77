#!/bin/bash

files=$(ls -1 samples)

for f in $files
do
    echo "--------------"
    fname="samples/"$f
    size=$(wc -c $fname | awk '{print $1}')
    minutes=$(($size/120000))
    #echo $minutes
    echo "File $f"
    echo "size (bytes):    $size"
    echo "minutes sampled: $minutes"
    dmin=$(python main.py "samples/"$f | grep 'decode: (good )' | wc -l | awk '{print $1}')
    echo "minutes decoded: $dmin"
done
