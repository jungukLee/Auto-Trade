#!/bin/zsh

# 백그라운드에서 Python 스크립트 실행
nohup python3 -u auto.py &

# nohup.out 로그 파일 실시간 모니터링
tail -f ./nohup.out