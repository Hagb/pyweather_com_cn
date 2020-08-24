from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class WeatherInfo(BaseModel):
    "天气信息"
    event: str
    "天气现象"
    wind_dir: str
    "风向"
    wind_scale: str
    "风力"


class Weather(BaseModel):
    "县/区天气"
    province: str
    "省"
    province_url: str
    "该省在 weather.com.cn 中的网址"
    city: str
    "市"
    district: str
    "县/区"
    district_url: str
    "该地区在 weather.com.cn 中的网址"
    date: date
    "日期"
    update_time: datetime
    "天气预报更新时间"
    day_weather: Optional[WeatherInfo]
    "白天天气"
    night_weather: WeatherInfo
    "夜间天气"
    temp_max: Optional[int]
    "最高气温"
    temp_min: int
    "最低气温"


provincial_cities: set = {'香港', '澳门', '重庆', '北京', '天津', '上海'}
