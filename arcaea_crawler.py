import websocket
import brotli
import json
import threading
import asyncio

clear_list = ['Track Lost', 'Normal Clear', 'Full Recall', 'Pure Memory', 'Easy Clear', 'Hard Clear']
diff_list = ['PST', 'PRS', 'FTR', 'BYD']

f = open('arc_namecache.txt', 'w')
f.close()


def load_cache():
    cache = {}
    f = open('arc_namecache.txt', 'r')
    for line in f.readlines():
        ls = line.replace('\n', '').split(' ')
        cache[ls[0]] = ls[1]
    f.close()
    return cache


def put_cache(d: dict):
    f = open('arc_namecache.txt', 'w')
    for key in d:
        f.write('%s %s\n' % (key, d[key]))


def cmp(a):
    return a['rating']


def calc(ptt, song_list):
    best30_list = []
    best30_overflow = []
    brating = 0
    rall = 0
    for i in range(0, 40):
        if i <= 29:
            if i <= 9:
                rall += song_list[i]['rating']
                best30_list.append(song_list[i])
                brating += song_list[i]['rating']
            else:
                try:
                    best30_list.append(song_list[i])
                    brating += song_list[i]['rating']
                except IndexError:
                    break
        else:
            best30_overflow.append(song_list[i])
    ball = brating
    brating /= 30
    rrating = 4 * (ptt - brating * 0.75)
    maxptt = ((ball + rall) / 40)
    return brating, rrating, maxptt, best30_list, best30_overflow


def lookup(nickname: str):
    ws = websocket.create_connection("wss://arc.estertion.win:616/")
    ws.send("lookup " + nickname)
    buffer = ""
    while buffer != "bye":
        buffer = ws.recv()
        if type(buffer) == type(b''):
            obj2 = json.loads(str(brotli.decompress(buffer), encoding='utf-8'))
            id = obj2['data'][0]['code']
            cache = load_cache()
            cache[nickname] = id
            put_cache(cache)
            return id

async def query(id: str):
    s = ""
    song_title, userinfo, scores = await _query(id)
    b, r, m, n, t = calc(userinfo['rating'] / 100, scores)
    s += "玩家: %s\n潜力值: %.2f\nBest 30: %.5f\nRecent Top 10: %.5f\n不更新最高分时可达到的最高ptt: %.6f\n\n" % (userinfo['name'], userinfo['rating'] / 100, b, r, m)
    score = userinfo['recent_score'][0]
    s += "最近游玩: \n%s  %s %.1f  \n%s\nPure: %d(%d)\nFar: %d\nLost: %d\n得分: %d\n单曲评级: %.2f" % (song_title[score['song_id']]['en'], diff_list[score['difficulty']], score['constant'], clear_list[score['clear_type']],
              score["perfect_count"], score["shiny_perfect_count"], score["near_count"], score["miss_count"], score["score"], score["rating"])
    return s


def best(id: str, num: int):
    if num < 1:
        return []
    result = []
    s = ""
    song_title, userinfo, scores = _query(id)
    s += "%s's Top %d Songs:\n" % (userinfo['name'], num)
    for j in range(0, int((num - 1) / 15) + 1):
        for i in range(15 * j, 15 * (j + 1)):
            if i >= num:
                break
            try:
                score = scores[i]
            except IndexError:
                break
            s += "#%d  %s  %s %.1f  \n\t%s\n\tPure: %d(%d)\n\tFar: %d\n\tLost: %d\n\tScore: %d\n\tRating: %.2f\n" % (i+1, song_title[score['song_id']]['en'], diff_list[score['difficulty']], score['constant'], clear_list[score['clear_type']],
                  score["perfect_count"], score["shiny_perfect_count"], score["near_count"], score["miss_count"], score["score"], score["rating"])
        result.append(s[:-1])
        s = ""
    return result

async def _query(id: str):
    cache = load_cache()
    # print(cache)
    try:
        id = cache[id]
    except KeyError:
        pass
    ws = websocket.create_connection("wss://arc.estertion.win:616/")
    ws.send(id)
    buffer = ""
    scores = []
    userinfo = {}
    song_title = {}
    while buffer != "bye":
        try:
            buffer =  ws.recv()
        except websocket._exceptions.WebSocketConnectionClosedException:
            ws = websocket.create_connection("wss://arc.estertion.win:616/")
            ws.send(lookup(id))
        if type(buffer) == type(b''):
            # print("recv")
            obj = json.loads(str(brotli.decompress(buffer), encoding='utf-8'))
            # al.append(obj)
            if obj['cmd'] == 'songtitle':
                song_title = obj['data']
            elif obj['cmd'] == 'scores':
                scores += obj['data']
            elif obj['cmd'] == 'userinfo':
                userinfo = obj['data']
    scores.sort(key=cmp, reverse=True)
    return song_title, userinfo, scores

def get_b30_dict(id, songtitle: dict, userinfo: dict, scores: list):
    b30_dict = {}
    ptt = userinfo['rating'] / 100
    brating, rrating, maxptt, best30_list, best30_overflow = calc(ptt, scores)
    best30_songinfo,best30_overflow_songinfo = get_b30_song_info(songtitle,scores)
    userinfo["code"] = id
    b30_dict["best30_avg"] = brating
    b30_dict["recent10_avg"] = rrating
    b30_dict["theory_ptt"] = maxptt
    b30_dict["account_info"] = userinfo
    b30_dict["best30_list"] = best30_list
    b30_dict["best30_overflow"] = best30_overflow
    b30_dict["best30_songinfo"] = best30_songinfo
    b30_dict["best30_overflow_songinfo"] = best30_overflow_songinfo
    return b30_dict

def get_b30_song_info(songtitle: dict, scores: list):
    best30_songinfo = []
    best30_overflow_songinfo = []
    for i in range(0,40):
        if i <=29:
            songinfo={}
            sid = scores[i]["song_id"]
            name_en = songtitle[sid]["en"]
            note = scores[i]["perfect_count"] + scores[i]["near_count"] + scores[i]["miss_count"]
            songinfo["name_en"] = name_en
            songinfo["note"] = note
            songinfo["side"] = 0
            best30_songinfo.append(songinfo)
        else:
            songinfo = {}
            sid = scores[i]["song_id"]
            name_en = songtitle[sid]["en"]
            note = scores[i]["perfect_count"] + scores[i]["near_count"] + scores[i]["miss_count"]
            songinfo["name_en"] = name_en
            songinfo["note"] = note
            songinfo["side"] = 0
            best30_overflow_songinfo.append(songinfo)
    return best30_songinfo,best30_overflow_songinfo

async def b30(id: str):
    song_title, userinfo, scores = await _query(id)
    b30_dict = get_b30_dict(id, song_title,userinfo,scores)
    return b30_dict

def get_recent_songinfo(songtitle: dict, scores: list):
    songinfo = []
    song_info = {}
    sid = scores[0]["song_id"]
    name_en = songtitle[sid]["en"]
    note = scores[0]["perfect_count"] + scores[0]["near_count"] + scores[0]["miss_count"]
    song_info["name_en"] = name_en
    song_info["note"] = note
    song_info["side"] = 0
    songinfo.append(song_info)
    return  songinfo

def get_recent_dict(id, song_title: dict, userinfo: dict):
    recent_dict = {}
    songinfo = get_recent_songinfo(song_title, userinfo["recent_score"])
    userinfo["code"] = id
    recent_dict["account_info"] = userinfo
    recent_dict["recent_score"] = userinfo["recent_score"]
    recent_dict["songinfo"] = songinfo
    return  recent_dict

async def recent(id: str):
    send = id
    send += " -1 -1"
    song_title, userinfo, scores = await _query(send)
    recent_dict = get_recent_dict(id, song_title, userinfo)

    return recent_dict

class Arcaea:

    @staticmethod
    async def run(operation, aid, num=0):
        result = []
        if operation == 'arcaea':
            try:
                message = await query(aid)
            except Exception as e:
                message = "An exception occurred: %s" % repr(e)
            result.append(message)
        elif operation == 'recent':
            try:
                s = await recent(aid)
            except Exception as e:
                s = ["An exception occurred: %s" % repr(e)]
            result.append(s)
        elif operation == 'best':
            try:
                s = await b30(aid)
            except Exception as e:
                s = ["An exception occurred: %s" % repr(e)]
            result.append(s)
        return result
