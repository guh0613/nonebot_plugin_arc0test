import json
import os

from nonebot import on_command
from nonebot.permission import SUPERUSER


from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.message import Message
from configs.path_config import DATA_PATH


from .arcaea_crawler import *
from .schema.v5.user_info import UserInfo
from .schema.v5.user_best30 import UserBest30
from .draw import UserArcaeaInfo
from .constant import getconstant

DATA = DATA_PATH / "arcaea" / "player.json"
player_data = {}
if not os.path.exists(DATA):
    with open(DATA, 'x', encoding='utf-8') as f:
        json.dump(player_data, f, ensure_ascii=False, indent=4)
with open(DATA, 'r', encoding='utf-8') as f:
    player_data = json.load(f)

help_text = '''arcaea查分器：
arcbind <好友码> 查询好友码
arcbest <好友码> 查询b30
arcre <好友码> 查询最近游玩
查询定数 <曲名/定数> 查询某首曲目的定数，或查询某个定数的所有曲目'''


help = on_command("arc帮助")
best = on_command("arcbest")
ds = on_command("查询定数")
recent = on_command("arcre")
bind = on_command("arcbind")
updateds = on_command("更新定数表",permission=SUPERUSER)




@help.handle()
async def help():
    await help.send(help_text)

@bind.handle()
async def arcbind(ev:MessageEvent, arg: Message = CommandArg()):
    uid = ev.user_id
    uid = str(uid)
    aid = arg.extract_plain_text().strip()
    if uid in player_data.keys():
        await bind.finish("该qq号已经绑定过了")
    else:
        player_data[uid] = aid
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)
        await bind.finish(f"成功绑定: {aid}")

@best.handle()
async def arcbetter(ev: MessageEvent,arg: Message = CommandArg()):
    uid = str(ev.user_id)
    aid = arg.extract_plain_text().strip()
    if len(aid) < 1:
        if not uid in player_data.keys():
            await best.finish("参数错误")
        else:
            aid = player_data[uid]
    await best.send("正在查询")
    result = await Arcaea.run('best', aid)
    data = UserBest30(**result[0])
    b = await UserArcaeaInfo.draw_user_b30(data)
    await best.finish(b)

@updateds.handle()
async def dstable():
    try:
        getconstant()
    except Exception:
        await updateds.finish("发生错误")
    await  updateds.send("更新定数表成功")

@ds.handle()
async def arcds(arg = CommandArg()):
    msg = arg.extract_plain_text().strip()
    result_str = ""
    num = 0
    from .dstable import dstable
    for line in dstable:
        if msg.lower() in ','.join(line).lower():
            num += 1
            result_str += f'\n{line[0]}  {line[1]}  {line[2]}  {line[3]}  {line[4]}'
    await ds.send("共找到%d条结果：" % num + result_str)

@recent.handle()
async def arcre(ev: MessageEvent, arg: Message = CommandArg()):
    uid = str(ev.user_id)
    aid = arg.extract_plain_text().strip()
    if len(aid) < 1:
        if not uid in player_data.keys():
            await recent.finish("你还没有绑定账号，或者参数错误")
        else:
            aid = player_data[uid]
    await recent.send("正在查询")
    result = await Arcaea.run('recent', aid)
    data = UserInfo(**result[0])
    r = await UserArcaeaInfo.draw_user_recent(data)
    await recent.send(r)
