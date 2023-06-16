#!/bin/python
import pandas as pd
import abc, json, re
import uuid
import time
import socketio

# setup websocket connection
#WEBSOCKET_URL = "wss://dev.msg.botcentralapi.com"
WEBSOCKET_URL = "wss://va.bc-msg.liveperson.net"
BOT_ID = "bbd30aa121330e52f99548b8f4082c8a06710bbc"

def getMessageId():
    messageId = str(uuid.uuid4())
    return '{}-{}'.format(messageId, 0)

def createMessage(uid, cid, text):
    mid_counter = 0
    mid = getMessageId()
    return {
      "object": "page",
      "entry": [
        {
          "id": mid,
          "time": int(round(time.time() * 1000)),
          "messaging": [
            {
              "conversationId": cid,
              "sender": {
                "id": uid
              },
              "recipient": {
                "id": BOT_ID
              },
              "source": "lp_inapp",
              "timestamp": int(round(time.time() * 1000)),
              "message": {
                "mid": mid,
                "text": text
              }
            }
          ]
        }
      ]
    }



sio = socketio.Client()
df_billing = pd.read_csv('./Billing.csv')
results = {}
time_tracker = {}
started_running = False

def formatResults():
    global results
    if len(results.keys()) ==  0:
        return
    df = pd.DataFrame([(k,v[0],v[1] if len(v) > 1 else None, v[2] if len(v) > 2 else None, v[3] if len(v) > 3 else None ) for k,v in results.items()])
    df.to_csv('./results_2A.csv')

@sio.on('connect')
def on_connect():
    print('connection established')
    global results
    global started_running
    time.sleep(5)
    if started_running == False:
        started_running = True
        for idx, row in df_billing.iterrows():
            # print(idx, row['conversationId'], row['usertext1'])
            uid = str(uuid.uuid4())
            if not row['usertext1'] or len(str(row['usertext1'])) == 0:
                continue
            key = row['conversationId']
            msg = createMessage(key, key, row['usertext1'])
            results[key] = [key]
            time_tracker[key] = time.time()
            sio.emit("usermessage", msg)
            time.sleep(0.2)
@sio.on('botresponse')
def on_message(data):
    global results
    if not "sender_action" in data.keys():
        try:
            key = data['recipient']['id']
            results[key].append(data)
            if "Which category below best describes your issue?" in data['message']['attachment']['payload']['text']:
                print(time_tracker[key] - time.time())
                msg = createMessage(key, key, "Billing or invoice")
                sio.emit("usermessage", msg)
            if 'Ok. You have a concern with "Billing". Is that right?' in data['message']['attachment']['payload']['text']:
                print(time_tracker[key] - time.time())
                msg = createMessage(key, key, "Yes")
                sio.emit("usermessage", msg)
            time.sleep(0.2)
        except Exception as e:
            print(e)

@sio.on('disconnect')
def on_disconnect():
    print('disconnected from server')
    print('-'*25)
    formatResults()

time.sleep(3)
sio.connect(WEBSOCKET_URL)
sio.wait()
