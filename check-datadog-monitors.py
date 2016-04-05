from datadog import initialize
import json
import pickle
import os
import requests
import sys

file = 'options.json'
if os.path.isfile(file):
    with open(file) as json_data_file:
        conf = json.load(json_data_file)
else:
    print "Could not open options.json"
    sys.exit(1)

options = {
    'api_key': conf['datadog_api_key'],
    'app_key': conf['datadog_app_key']
}

prowl_api_key = conf['prowl_api_key']

def notify(apikey, app, event, description=""):
    data = {'apikey': apikey,
            'application': app,
            'event': event,
            'description': description}

    r = requests.post("https://api.prowlapp.com/publicapi/add", data=data)
    print r.text

class Config(object):
    def __init__(self):
        self.state = {}
        if os.path.isfile('state.txt'):
            self.read()
        else:
            self.write()
            
    def read(self):
        with open('state.txt', 'rb') as handle:
            self.state = pickle.loads(handle.read())
        
    def write(self):
        with open('state.txt', 'wb') as handle:
            pickle.dump(self.state, handle)

config = Config()
initialize(**options)

from datadog import api

monitors = api.Monitor.get_all()

for monitor in monitors:
    name = monitor["name"]
    state = monitor["overall_state"]

    if name in config.state:
        prev_state = config.state[name]
    else:
        prev_state = "OK"

    config.state[name] = state 

    if state != "OK" and prev_state == "OK":
        print "ALERT: {0} state is {1}".format(name, state)
        notify(prowl_api_key, name, "{0} is down.  State = {1}".format(name, state))
    elif state != "OK":
        print "{0} state is {1} - No alert because of previous state".format(name, state)
    elif state == "OK":
        print "{0} is OK".format(name)

config.write()
