from .best_30.chieri_style import draw_user_b30, draw_ptt
from io import BytesIO
from nonebot.adapters.onebot.v11.message import MessageSegment

from .single_song.andreal_style_v3 import draw_single_song


class UserArcaeaInfo:
    @staticmethod
    async def draw_user_b30(data, language="en"):
        try:
            image = draw_user_b30(data=data, language=language)
            buffer = BytesIO()
            image.convert("RGB").save(buffer, "jpeg")
            return MessageSegment.image(buffer)
        except Exception as e:
            return str(e)

    @staticmethod
    async def draw_user_recent(data, language="en"):
        try:
            image = draw_single_song(data=data, language=language)
            buffer = BytesIO()
            image.convert("RGB").save(buffer, "jpeg")
            return MessageSegment.image(buffer)
        except Exception as e:
            return str(e)