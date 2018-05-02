#!/bin/bash
export DISPLAY=:0.0
nohup glxgears > nohup.out 2>&1 &
nohup x11vnc --forever > nohup.out 2>&1 &
