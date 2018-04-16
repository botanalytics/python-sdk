# [Botanalytics](https://botanalytics.co) - Conversational analytics & engagement tool for chatbots

Python SDK currently supports


* [Google Assistant](http://docs.botanalytics.apiary.io/)
* [Amazon Alexa](http://docs.botanalytics.apiary.io/)
* [Facebook](http://docs.botanalytics.apiary.io/)
* [Slack](http://docs.botanalytics.apiary.io/)
* [Generic](http://docs.botanalytics.apiary.io/)

If you want to use nodejs instead, checkout [Botanalytics NodeJs SDK](https://github.com/Botanalyticsco/botanalytics)

## Setup

Create a free account at [https://www.botanalytics.co](https://www.botanalytics.co) and get a Token.

Botanalytics is available via pip.

```bash
pip install botanalytics
```

##### Google Assistant
```python
from botanalytics.google import GoogleAssistant, GoogleAssistantCloudFunctions
import os

# Optional callback function, if you specify it, you can handle failed
#  attemps the way you want
def err_callback(err, reason, payload):
    pass

# Debug(optional)->bool, token(required)->str, callback(optional)->function
botanalytics = GoogleAssistant(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], callback=err_callback)
# request_payload -> dict, response_payload -> dict
botanalytics.log(request_payload, response_payload)

# For Google Cloud Functions
# Debug(optional)->bool, token(required)->str, async_logging(optional)->bool
botanalytics_gc = GoogleAssistantCloudFunctions(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], async_logging=True)
# request_payload->dict, response_payload->dict
botanalytics_gc.log(request_payload, response_payload)

```

##### Amazon Alexa
```python
from botanalytics.amazon import AmazonAlexa, AmazonAlexaLambda
import os

# Optional callback function, if you specify it, you can handle failed
#  attemps the way you want
def err_callback(err, reason, payload):
    pass

# Debug(optional)->bool, token(required)->str, callback(optional)->function
botanalytics = AmazonAlexa(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], callback=err_callback)
# request_payload -> dict, response_payload -> dict
botanalytics.log(request_payload, response_payload)

# For lambda
# Debug(optional)->bool, token(required)->str, async_logging(optional)->bool
botanalytics_aal = AmazonAlexaLambda(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], async_logging=True)
# request_payload->dict, response_payload->dict
botanalytics_aal.log(request_payload, response_payload)

```

##### Facebook
```python
from botanalytics.facebook import FacebookMessenger
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import requests
import os

# Optional callback function, if you specify it, you can handle failed
#  attemps the way you want
def err_callback(err, reason, payload):
    pass

botanalytics_token = os.environ['BOTANALYTICS_API_TOKEN']
fb_page_token = os.environ["FACEBOOK_PAGE_TOKEN"]
# Debug(optional)->bool, token(required)->str, fb_token(optional)-> str,
# callback(optional)->function
botanalytics = FacebookMessenger(
                        debug=True,
                        token=botanalytics_token,
                        fb_token=fb_page_token,
                        callback=err_callback)

class BasicRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super(ServerHandler, self).__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == '/webhook/facebook':
            print('Incoming facebook message')
            self.handle_facebook_message()
        else:
            # Handle your paths

    def handle_facebook_message(self):
        request_body = str(self.rfile.read(int(self.headers['content-length'])), 'utf-8')
        message_payload = json.loads(request_body)
        #log incoming message
        botanalytics.log_incoming(message_payload)

        for entry in message_payload['entry']:
            page_id = entry['id']
            message_time = entry['time']
            for event in entry['messaging']:
                sender_id = event['sender']['id']
                message_to_build= {}

                #
                # Handle your event and build your message
                #

                # log outgoing message
                botanalytics.log_outgoing(message_to_build, sender_id)

                # send your message
                response_message = {
                    "recipient": {"id":sender_id},
                    "message": message_to_build,
                }
                requests.post('https://graph.facebook.com/v2.6/me/messages?access_token='+fb_page_token,
                             json = response message)

        self.send_response(200)

def run(server_class=HTTPServer, handler_class=BasicRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    try:
        httpd.serve_forever()
    except BaseException as ki:
        print(str(ki))


if __name__ == "__main__":
    run()

```


##### Generic
```python
from botanalytics.generic import Generic
import os

# Optional callback function, if you specify it, you can handle failed
#  attemps the way you want
def err_callback(err, reason, payload):
    pass

# Debug(optional)->bool, token(required)->str, callback(optional)->function
botanalytics = Generic(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], callback=err_callback)
# message -> dict
botanalytics.log(message)

```

##### SlackRTMApi
```python
from botanalytics.slack import SlackRTMApi
from slackclient import SlackClient
import os

sc = SlackClient(os.environ["SLACK_API_TOKEN"])

# Optional callback function, if you specify it, you can handle failed
#  attemps the way you want
def err_callback(err, reason, payload):
    pass

# Debug(optional)->bool, token(required)->str, slack_client_instance(required)-> SlackClient, callback(optional)->function
botanalytics = SlackRTMApi(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], slack_client_instance=sc, callback=err_callback)
if sc.rtm_connect():
  while sc.server.connected is True:
        for message in sc.rtm_read():
            # message -> dict
            botanalytics.log_incoming(message)
            # Handle incoming message
            #       .
            #       .
            sc.rtm_send_message("welcome-test", "test")
            botanalytics.log_outgoing("welcome-test", "test")
            time.sleep(1)
else:
    print "Connection Failed"


```

##### SlackEventApi
```python
from botanalytics.slack import SlackEventApi
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import json

# Optional callback function, if you specify it, you can handle failed
#  attemps the way you want
def err_callback(err, reason, payload):
    pass

# Debug(optional)->bool, token(required)->str, slack_token(required)-> str, callback(optional)->function
botanalytics = SlackEventApi(debug=True, token=os.environ['BOTANALYTICS_API_TOKEN'], slack_token=os.environ["SLACK_API_TOKEN"], callback=err_callback)

class BasicRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super(ServerHandler, self).__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == '/slack/events':
            print('Incoming event')
            self.handle_slack_event()

        elif self.path == '/slack/interactive':
            print('Incoming interactive event')
            self.handle_slack_interactive()
        else:
            # Handle your paths

    def handle_slack_interactive(self):
        byte_dictionary = parse_qs(self.rfile.read(int(self.headers['content-length'])), keep_blank_values=1)
        interactive_payload = json.loads(byte_dictionary[b'payload'][0].decode())
        botanalytics.log(interactive_payload)
        #
        # Handle interactive payload
        #
        self.send_response(200)

    def handle_slack_event(self):
        request_body = str(self.rfile.read(int(self.headers['content-length'])), 'utf-8')
        event_payload = json.loads(request_body)
        botanalytics.log(event_payload)
        #
        #Handle event message
        #
        self.send_response(200)

def run(server_class=HTTPServer, handler_class=BasicRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    try:
        httpd.serve_forever()
    except BaseException as ki:
        print(str(ki))


if __name__ == "__main__":
    run()

```
Follow the instructions at [http://docs.botanalytics.apiary.io/](http://docs.botanalytics.apiary.io/)
