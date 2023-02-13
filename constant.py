import os

import websocket
import brotli
import json
def on_message(ws,message):
    if type(message)!="str":
        data=json.loads(str(brotli.decompress(message), encoding='utf-8'))
        new = data["cmd"]
        if new == 'songtitle':
                global songTitleData
                songTitleData=data["data"]
        if new == 'songartist':
                global songArtistData
                songArtistData=data["data"]
        if new == 'constants':
                list=[["曲目","PST","PRS","FTR","BYD"]]
                
                
                songppt=data["data"]
                for k in songppt.keys():
                    list.append([songTitleData[k]['en']])
                    print(songTitleData[k])
                    for t in range(len(songppt[k])):
                        if songppt[k][t]==None:
                            list[-1].append("")
                        else:
                            list[-1].append(songppt[k][t]['constant'])
                    for j in range(4-len(songppt[k])):
                        list[-1].append("")

                FILE_PATH = os.path.dirname(__file__)
                dstable = os.path.join(FILE_PATH , "dstable.py")
                f=open(dstable, mode="w",encoding='utf-8')
                f.write('dstable = ' + str(list))
                f.close()
                    
def on_error(ws,error):
    raise error
def on_open(ws):
    ws.send("constants")

def getconstant():
    websocket.enableTrace(False)
    ws=websocket.WebSocketApp("wss://arc.estertion.win:616")
    ws.on_message=on_message
    ws.on_error=on_error
    ws.on_open=on_open
    ws.run_forever()