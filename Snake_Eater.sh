#!/bin/bash
xdotool mousemove 1280 1024
cd projet/Snake_Eater
touch highscore
java -cp .:..:../.. Snake_Eater
