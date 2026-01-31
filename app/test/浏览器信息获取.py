import requests
import websocket
import json

id_counter = 0

def send_cdp(ws,method,params=None):
    global id_counter
    ws.send(json.dumps({
        'id': id_counter,
        'method': method,
        'params': params
    }))
    id_counter+=1
    print(ws.recv())

url='http://127.0.0.1:9222/json'
html=requests.get(url).json()
ws_url=None
for i in html:
    if i.get('webSocketDebuggerUrl'):
        ws_url=i.get('webSocketDebuggerUrl')

if ws_url:
    ws = websocket.create_connection(ws_url)
    send_cdp(ws,'Page.navigate',
             {'url': 'https://www.baidu.com'})