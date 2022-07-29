#!/bin/bash
echo /home/ubuntu/betfairBot/cronjob.sh called: `date`
HOME=/home/ubuntu/
PYTHONPATH=/home/ubuntu/betfairBot/venv/bin/python3
cd /home/ubuntu/betfairBot
python3 app.py 2>&1


## Syntax = $ path/to/venv/python3 path/to/script
##cd /home/ubuntu/betfairBot/
##/home/ubuntu/betfairBot/venv/bin/python3 /home/ubuntu/betfairBot/app.py
##/home/ubuntu/betfairBot/venv/bin/python3 /home/ubuntu/betfairBot/tests/neds_test_raw.py
