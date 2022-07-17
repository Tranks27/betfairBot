# betfairBot

## Installation
1. Download the source code
2. Create a virtual environment using virtualenv 
```
$ sudo apt install python3-virtualenv
$ virtualenv venv
```
3. Follow this link to create a self-signed certificate for Betfair: https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login 
- Include the generated certificate in a folder /betfairBot/certs/ .
4. Install all those modules in the requirements.txt
```
$ pip3 install -r requirements.txt
```
5. Install the chromedriver (the same version as your current chromium/google chrome browser version)
- Download the chromedriver from the offcial website here. https://chromedriver.chromium.org/
- Move the chromedriver to file in PATH
```
  $ sudo mv ~/path/to/chromedriver /usr/local/bin/
  $ sudo chmod +x /usr/local/bin/chromedriver
```

## Pre-requisites
- A betfair account with non-interactive login enabled. More info here: https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login
- Your own betfair live API token. Create a file /betfairBot/certs/passwords.py and add the following sensitive data in it.
```
## login details
USERNAME = "xxx" # betfair username
PASSWORD = "xxx" # betfair password 
API_KEY_DEMO = "xxx" # (optional) betfair demo API token
API_KEY_LIVE = "xxx" # betfair LIVE API token
```

## Start the program
```
$ source venv/bin/activate
$ python3 app.py
```
