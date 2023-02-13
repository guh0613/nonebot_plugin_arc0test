from typing import List, Optional
from ..basemodel import Base
from .song_info import SongInfo
from .score_info import ScoreInfo
from .account_info import AccountInfo




class UserInfo(Base):
    account_info: AccountInfo
    recent_score: List[ScoreInfo]
    songinfo: List[SongInfo]
