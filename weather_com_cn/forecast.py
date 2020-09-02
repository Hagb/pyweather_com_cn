import ast
from .model import Weather, WeatherInfo, provincial_cities, provinces
from datetime import datetime, timezone, timedelta, date
from requests import Session, Response
from typing import Union, Optional, Dict, List, Iterable, Union
from bs4 import BeautifulSoup, element

__all__ = ('WeatherCrawler')


class WeatherCrawler():
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

    @staticmethod
    def _isDistrictUnmatch(district: List[str], districts_included,
                           districts_excluded) -> int:
        """判断某区域是否被过滤器过滤

        返回被过滤的行政单位级别：1 省级，2 市级，3 区县级
        """
        m: int = len(district) + 1
        for n, i in enumerate(district):
            if districts_included is None:
                break
            if i in districts_included:
                if isinstance(districts_included, set):
                    break
                districts_included = districts_included[i]
            else:
                m = n + 1 if districts_included else max(n, 0)
                break
        else:
            m = n + 1

        for n, i in enumerate(district):
            if districts_excluded is None:
                return min(max(n, 1), m)
            if i in districts_excluded:
                if isinstance(districts_excluded, set):
                    return min(n + 1, m)
                districts_excluded = districts_excluded[i]
            else:
                if m == len(district) + 1:
                    return 0
                else:
                    return m
        return min(n + 1, m)

    @classmethod
    def filterWeathers(cls,
                       weathers: Iterable[Weather],
                       districts_included: Optional[Union[dict, list]] = None,
                       districts_excluded: Union[dict, list] = {},
                       dates_included: Optional[Iterable[date]] = None,
                       dates_excluded: Iterable[date] = {}) -> List[Weather]:
        return [
            w for w in weathers if
            not cls._isDateUnmatch(w.date, dates_included, dates_excluded) and
            not cls._isDistrictUnmatch([w.province, w.city, w.district],
                                       districts_included, districts_excluded)
        ]

    @staticmethod
    def _isDateUnmatch(date_: date,
                       dates_included: Optional[Iterable[date]] = None,
                       dates_excluded: Iterable[date] = {}) -> bool:
        "判断某日期是否被过滤器过滤"
        return (dates_included is not None
                and date_ not in dates_included) or date_ in dates_excluded

    def getNationWideWeathers(
            self,
            districts_included: Optional[Union[dict, list]] = None,
            districts_excluded: Union[dict, list] = {},
            dates_included: Optional[Iterable[date]] = None,
            dates_excluded: Iterable[date] = {}) -> List[Weather]:
        return self.getWeathers(self.getAreasList().values(),
                                districts_included, districts_excluded,
                                dates_included, dates_excluded)

    def getWeathers(self,
                    url: Union[str, Iterable[str]],
                    districts_included: Optional[Union[dict, list]] = None,
                    districts_excluded: Union[dict, list] = {},
                    dates_included: Optional[Iterable[date]] = None,
                    dates_excluded: Iterable[date] = {}) -> List[Weather]:
        if not isinstance(url, str):
            weathers: List[Weather] = []
            for u in url:
                weathers.extend(
                    self.getWeathers(u, districts_included, districts_excluded,
                                     dates_included, dates_excluded))
            return weathers
        resp: Response = self.session.get(self.base_url + url)
        resp.encoding = resp.apparent_encoding
        bs: BeautifulSoup = BeautifulSoup(resp.text, 'lxml')

        content: element.Tag = bs.find('div', attrs={'class': 'contentboxTab'})

        # 获取天气预报更新时间
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

        # 是否为省级行政单位的天气预报页面（除了省级以外，还有一种是如“西南”这种更大的区域的）
        is_province_page: bool = province_tmp in provinces
        if is_province_page and self._isDistrictUnmatch(
            [province_tmp, '', ''], districts_included,
                districts_excluded) == 1:
            return []
        weathers = []
        dates: List[date] = []
        weather_all_tabs: List[element.Tag] = content.find(
            'div', attrs={
                'class': 'hanml'
            }).findAll('div', attrs={'class': 'conMidtab'})
        weather_tabs: List[element.Tag] = []
        date_tmp: date

        # 获取提供天气预报的日期
        for n, date_li in enumerate(
                content.find('ul', attrs={
                    'class': 'day_tabs'
                }).findAll('li')):
            date_str: List[str] = date_li.text[date_li.text.find('(') +
                                               1:-2].split('月')
            month: int = int(date_str[0])
            day: int = int(date_str[1])
            if month < update_time.month:
                date_tmp = date(update_time.year - 1, month, day)
            else:
                date_tmp = date(update_time.year, month, day)
            if not self._isDateUnmatch(date_tmp, dates_included,
                                       dates_excluded):
                weather_tabs.append(weather_all_tabs[n])
                dates.append(date_tmp)

        # 以日期为单位的迭代
        for n, weather_tab in enumerate(weather_tabs):
            date_tmp = dates[n]
            # 以表格为单位的迭代
            for weather_div in weather_tab.children:
                if weather_div.name != 'div':
                    continue
                # 以单个区域（区县或市）为单位的迭代（以表的行为单位来迭代）
                for tr in weather_div.findAll('tr'):
                    is_provincial_city: bool
                    city: str
                    province: str
                    province_url: str
                    tds: List[element.Tag] = tr.findAll('td')
                    if (tds[2].text[-2:] == '白天' and tds[3].text[-2:] == '夜间'
                        ) or tds[0].text == '天气现象':  # 该行为上侧的表头
                        continue
                    else:
                        if tds[0].get('class') == ['rowsPan']:  # 该列为左侧的表头
                            if is_province_page:
                                city = tds[0].text.strip()
                                province = province_tmp
                                province_url = province_url_tmp
                            else:
                                province = tds[0].text.strip()
                                province_url = tds[0].find('a')['href']
                            is_provincial_city = province in provincial_cities
                            if is_provincial_city:
                                city = province
                            tds = tds[1:]
                        district: str = tds[0].text.strip()
                        district_url: str = tds[0].find('a')['href']
                        if not (is_provincial_city or is_province_page):
                            city = district
                        unmatch_no: int = self._isDistrictUnmatch(
                            [province, city, district], districts_included,
                            districts_excluded)
                        if unmatch_no == 3:  # 区县级行政单位被过滤
                            continue
                        elif unmatch_no == 2:  # 整个市级行政单位被过滤
                            if is_provincial_city or is_province_page:
                                break
                            else:
                                continue
                        elif unmatch_no == 1:  # 整个省级行政单位被过滤
                            break
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
                            Weather(province=province,
                                    province_url=province_url,
                                    city=city,
                                    district=district,
                                    district_id=int(district_url[-15:-6]),
                                    date=date_tmp,
                                    update_time=update_time,
                                    day_weather=day_weather,
                                    night_weather=night_weather,
                                    temp_max=int(tds[3].text)
                                    if day_weather else None,
                                    temp_min=int(tds[6].text)))
        return weathers
