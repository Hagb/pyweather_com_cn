from typing import List, Union, Optional, Dict, Tuple, Iterable
from requests import Session, Response
from datetime import datetime, timezone, timedelta
from .model import Alarm, AlarmLevel, AlarmKind, AlarmDetail
import ast
from bidict import bidict
import json
__all__ = ('AlarmCrawler')


class AlarmCrawler():
    "气象预警爬虫"
    url: str = 'https://product.weather.com.cn/alarm/grepalarm_cn.php'
    session: Session
    TIMEZONE: timezone = timezone(timedelta(hours=8), "Asia/Shanghai")

    #cache_IDs: bidict
    #cache_levels: bidict

    def __init__(self, session: Optional[Session] = None):
        self.session: Session = session if session else Session()
        #self.cache_IDs: bidict = bidict()
        #self.cache_levels: bidict = bidict()

    def getAlarms(self) -> List[Alarm]:
        resp: Response = self.session.get(self.url)
        resp.encoding = resp.apparent_encoding
        alarms_list: List[List[str]] = self._paramJsVar(resp.text)['data']
        alarms: List[Alarm] = []
        for alarm_l in alarms_list:
            short_url: str = alarm_l[1]
            url_info: List[str] = short_url[:-5].split('-')
            time: datetime = datetime(int(url_info[1][:4]),
                                      int(url_info[1][4:6]),
                                      int(url_info[1][6:8]),
                                      int(url_info[1][8:10]),
                                      int(url_info[1][10:12]),
                                      int(url_info[1][12:]),
                                      tzinfo=self.TIMEZONE)
            alarms.append(
                Alarm(location=alarm_l[0],
                      lng_E=float(alarm_l[2]),
                      lat_N=float(alarm_l[3]),
                      location_id=int(url_info[0]),
                      short_url=short_url,
                      time=time,
                      kind=AlarmKind(int(url_info[2][:2])),
                      level=AlarmLevel(int(url_info[2][2:]))))
        return alarms

    def getAlarmDetail(self, short_url: str) -> AlarmDetail:
        def timeStrToUTC8(text: str) -> datetime:
            time_tzless: datetime = datetime.fromisoformat(text)
            return datetime.combine(time_tzless.date(),
                                    time_tzless.time(),
                                    tzinfo=self.TIMEZONE)

        resp: Response = self.session.get(self.shortUrlToCompleted(short_url))
        resp.encoding = resp.apparent_encoding
        info: Dict[str, str] = self._paramJsVar(resp.text)
        return AlarmDetail(title=info['head'],
                           alarm_id=info['ALERTID'],
                           province_name=info['PROVINCE'],
                           city_name=info["CITY"],
                           time=timeStrToUTC8(info["ISSUETIME"]),
                           content=info["ISSUECONTENT"],
                           relieve_time=timeStrToUTC8(info["RELIEVETIME"]),
                           kind=AlarmKind(int(info["TYPECODE"])),
                           level=AlarmLevel(int(info["LEVELCODE"])),
                           raw_info=info)

    @staticmethod
    def shortUrlToCompleted(url: str) -> str:
        return f"http://product.weather.com.cn/alarm/webdata/{url}"

    @staticmethod
    def shortUrlToHuman(url: str) -> str:
        return f"http://www.weather.com.cn/alarm/newalarmcontent.shtml?file={url}"

    @staticmethod
    def _paramJsVar(data: str) -> Union[list, dict]:
        '解析 weather.com.cn 上作为数据的 js 变量定义'
        info: List[str] = data.strip().split('=', maxsplit=1)
        return ast.literal_eval(
            info[1] if info[1][-1] != ';' else info[1][:-1])

    def getSession(self) -> Session:
        return self.session
