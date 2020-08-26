from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Dict
from enum import Enum
from aenum import MultiValueEnum
__all__ = ('WeatherInfo', 'Weather', 'Alarm', 'AlarmKind', 'AlarmDetail',
           'AlarmLevel')


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
    district_id: int
    "该地区在 weather.com.cn 中的编号"
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


class AlarmKind(MultiValueEnum):
    冰雹 = 10
    霜冻 = 11
    大雾 = 12
    霾 = 13
    道路结冰 = 14
    海上大雾 = 51
    雷暴大风 = 52
    持续低温 = 53
    浓浮尘 = 54
    龙卷风 = 55
    低温冻害 = 56
    海上大风 = 57
    低温雨雪冰冻 = 58
    强对流 = 59
    臭氧 = 60
    大雪 = 61
    强降雨 = 62
    强降温 = 63
    雪灾 = 64
    森林草原火险 = 65
    雷暴 = 66
    严寒 = 67
    沙尘 = 68
    海上雷雨大风 = 69
    海上雷电 = 70
    海上台风 = 71
    低温 = 72, 99
    寒冷 = 91
    灰霾 = 92
    雷雨大风 = 93
    森林火险 = 94
    降温 = 95
    道路冰雪 = 96
    干热风 = 97
    空气重污染 = 98
    台风 = 1
    暴雨 = 2
    暴雪 = 3
    寒潮 = 4
    大风 = 5
    沙尘暴 = 6
    高温 = 7
    干旱 = 8
    雷电 = 9


class AlarmLevel(Enum):
    蓝色 = 1
    黄色 = 2
    橙色 = 3
    红色 = 4
    白色 = 5


class Alarm(BaseModel):
    location: str
    "位置"
    lng_E: float
    "东经"
    lat_N: float
    "北纬"
    location_id: int
    "该地区在 weather.com.cn 中的编号"
    kind: AlarmKind
    "预警类型"
    level: AlarmLevel
    "预警级别"
    time: datetime
    "时间"
    short_url: str


class AlarmDetail(BaseModel):
    title: str
    "标题"
    alarm_id: str
    "预警 id"
    province_name: str
    "省"
    city_name: str
    "地区（市、区县）"
    time: datetime
    "时间"
    content: str
    "预警描述"
    relieve_time: datetime
    "解除预警时间"
    kind: AlarmKind
    "预警类型"
    level: AlarmLevel
    "预警级别"
    raw_info: Dict[str, str]
    "天气网站的原始信息"


provincial_cities: set = {'香港', '澳门', '重庆', '北京', '天津', '上海'}
provinces: set = {
    '北京', '安徽', '重庆', '福建', '甘肃', '广东', '广西', '贵州', '海南', '河北', '河南', '湖北',
    '湖南', '黑龙江', '吉林', '江苏', '江西', '辽宁', '内蒙古', '宁夏', '青海', '山东', '陕西', '山西',
    '上海', '四川', '天津', '西藏', '新疆', '云南', '浙江', '香港', '澳门', '台湾'
}
