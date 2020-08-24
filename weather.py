#import json
import ast
from model import Weather, WeatherInfo, provincial_cities
from datetime import datetime, timezone, timedelta, date
from requests import Session, Response
from typing import Union, Optional, Dict, List
from bs4 import BeautifulSoup, element
#import re

__all__ = ('WeatherChinaCrawler')


class WeatherComCn():
    def __init__(self):
        pass

    class UnknownFormat(ValueError):
        pass

    @staticmethod
    def paramJsVar(data: str) -> Union[list, dict]:
        '解析 weather.com.cn 上作为数据的 js 变量定义'
        index: int = data.find('=')
        if index == -1:
            raise WeatherComCn.UnknownFormat()
        try:
            return ast.literal_eval(data[index + 1:-1])
        except (ValueError, SyntaxError, IndexError):
            raise WeatherComCn.UnknownFormat

    @staticmethod
    def paramDateStr(date):
        pass


class WeatherAlarmList():
    "气象预警爬虫"
    url: str = 'https://product.weather.com.cn/alarm/grepalarm_cn.php'
    session: Session

    def __init__(self, session: Optional[Session] = None):
        self.session: Session = session if session else Session()


class WeatherAlarm(dict):
    page_url: str = 'http://product.weather.com.cn/alarm/webdata/{page}'

    def __init__(self):
        pass


class WeatherWorldCrawler():
    "国际天气预报爬虫"
    url: str = "http://www.weather.com.cn/forecast/world.shtml"
    session: Session

    def __init__(self, session: Optional[Session] = None):
        self.session: Session = session if session else Session()


class WeatherChinaCrawler():
    "国内天气预报爬虫"
    base_url: str = "http://www.weather.com.cn"
    url: str = "http://www.weather.com.cn/textFC/hb.shtml"
    TIMEZONE: timezone = timezone(timedelta(hours=8), "Asia/Shanghai")
    session: Session

    def __init__(self, session: Optional[Session] = None):
        self.session: Session = session if session else Session()

    def getProvincesList(self) -> Dict[str, str]:
        resp: Response = self.session.get(self.url)
        resp.encoding = resp.apparent_encoding
        bs: BeautifulSoup = BeautifulSoup(resp.text, 'lxml')
        div = bs.find('div', attrs={'class': 'lqcontentBoxheader'})
        assert isinstance(div, element.Tag)
        return {
            city_bs.text: city_bs['href']
            for city_bs in div.find_all('a', target='_blank')
        }

    def getAreasList(self) -> Dict[str, str]:
        resp: Response = self.session.get(self.url)
        resp.encoding = resp.apparent_encoding
        bs: BeautifulSoup = BeautifulSoup(resp.text, 'lxml')
        ul = bs.find('ul', attrs={'class': 'lq_contentboxTab2'})
        assert isinstance(ul, element.Tag)
        return {city_bs.text: city_bs['href'] for city_bs in ul.find_all('a')}

    def getWeathers(self,
                    url: str,
                    dates_filter Optional[List[date]] = None,
                    districts_filter: Optional[List[str]] = None) -> List[Weather]:
        resp: Response = self.session.get(self.base_url + url)
        resp.encoding = resp.apparent_encoding
        bs: BeautifulSoup = BeautifulSoup(resp.text, 'lxml')

        content: element.Tag = bs.find('div', attrs={'class': 'contentboxTab'})

        dt_span: element.Tag = content.find('span')
        dt_str: str = dt_span.text.strip()[-16:]
        update_time: datetime = datetime(int(dt_str[:4]),
                                         int(dt_str[5:7]),
                                         int(dt_str[8:10]),
                                         int(dt_str[11:13]),
                                         int(dt_str[14:16]),
                                         tzinfo=self.TIMEZONE)

        area_a: element.Tag = dt_span.findPrevious('a')
        province_tmp: str = area_a.text
        province_url_tmp: str = area_a['href']
        weathers: List[Weather] = []

        for weather_tab in content.findAll('div', attrs={'class':
                                                         'conMidtab'}):
            for tr in weather_tab.findAll('tr'):
                is_provincial_city: bool
                is_province_page: bool
                city: str
                province: str
                province_url: str
                date_tmp: date
                tds: List[element.Tag] = tr.findAll('td')
                if tds[2].text[-2:] == '白天' and tds[3].text[-2:] == '夜间':
                    date_str: List[str] = tds[2].text[3:-4].split('月')
                    month: int = int(date_str[0])
                    day: int = int(date_str[1])
                    if month < update_time.month:
                        date_tmp = date(update_time.year - 1, month, day)
                    else:
                        date_tmp = date(update_time.year, month, day)
                elif tds[0].text == '天气现象':
                    continue
                else:
                    if tds[0].get('class') == ['rowsPan']:
                        a: Optional[element.Tag] = tds[0].find('a')
                        is_province_page = a is None
                        if is_province_page:
                            city = tds[0].text.strip()
                            province = province_tmp
                            province_url = province_url_tmp
                        else:
                            province = tds[0].text.strip()
                            province_url = a['href']
                        is_provincial_city = province in provincial_cities
                        if is_provincial_city:
                            city = province
                        tds = tds[1:]
                    district: str = tds[0].text.strip()
                    district_url: str = tds[0].find('a')['href']
                    if tds[1].text != '-':
                        day_wind_spans: List[element.Tag] = tds[2].findAll(
                            'span')
                        day_weather: Optional[WeatherInfo] = WeatherInfo(
                            event=tds[1].text,
                            wind_dir=day_wind_spans[0].text,
                            wind_scale=day_wind_spans[1].text)
                    else:
                        day_weather = None
                    night_wind_spans: List[element.Tag] = tds[5].findAll(
                        'span')

                    night_weather: WeatherInfo = WeatherInfo(
                        event=tds[4].text,
                        wind_dir=night_wind_spans[0].text,
                        wind_scale=night_wind_spans[1].text)
                    weathers.append(
                        Weather(
                            province=province,
                            province_url=province_url,
                            city=city if is_provincial_city or is_province_page
                            else district,
                            district=district,
                            district_url=district_url,
                            date=date_tmp,
                            update_time=update_time,
                            day_weather=day_weather,
                            night_weather=night_weather,
                            temp_max=int(tds[3].text) if day_weather else None,
                            temp_min=int(tds[6].text)))
        return weathers

    def getDetailWeather(self, district_url):
        pass
