#!/bin/bash
xdotool mousemove 1280 1024
cd projet/Kowasu_Renga
touch highscore
java -cp .:..:../.. Kowasu_Renga
