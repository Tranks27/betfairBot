# betfairBot

## Installation
1. Download the source code
2. Create a virtual environment using virtualenv 
```
$ pip3 install virtualenv
$ virtualenv venv
```
3. Follow this link to create a self-signed certificate for Betfair: https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login 
4. Install all those modules in the requirements.txt
```
$ pip3 install -r requirements.txt
```
5. Install the chromedriver (in the same version as your current chromium/google chrome browser version)
- Download the chromedriver from the offcial website here. https://chromedriver.chromium.org/
- Move the chromedriver to file in PATH
```
  $ sudo mv ~/path/to/chromedriver /usr/local/bin/
  $ sudo chmod +x /usr/local/bin/chromedriver
```

## Start the program
```
$ source venv/bin/activate
$ python3 app.py
```
