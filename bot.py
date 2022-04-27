# Import libraries
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json

# Change this certs path to wherever you're storing your certificates
certs_path = "/usr/lib/ssl/client-2048.crt"

# Change these login details to your own
my_username = "mightytranks@gmail.com"
my_password = "OsGiwuevzRf4925Lfty!"
my_app_key = "X9EGwt5zbpg8o5xk"

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs=certs_path)

trading.login()