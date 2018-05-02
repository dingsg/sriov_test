#!/bin/bash
modprobe amdgpu
nohup xinit > nohup.out 2>&1 &
