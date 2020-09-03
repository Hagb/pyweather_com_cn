from requests import Session, Response
from typing import Optional, List, Dict
import json
__all__ = ("LocationID")


class LocationID():
    def __init__(self, session: Optional[Session] = None):
        self.session = session if session else Session()

    def getProvincesIDs(self) -> Dict[str, int]:
        resp: Response = self.session.get(
            'http://www.weather.com.cn/data/city3jdata/china.html')
        if resp.status_code == 404:
            return {}
        resp.encoding = resp.apparent_encoding
        ids_dict: dict = json.loads(resp.text)
        return {ids_dict[i]: int(i) for i in ids_dict}

    def getCitiesIDs(self, province_id: int) -> Dict[str, int]:
        resp: Response = self.session.get(
            f'http://www.weather.com.cn/data/city3jdata/provshi/{province_id}.html'
        )
        if resp.status_code == 404:
            return {}
        resp.encoding = resp.apparent_encoding
        ids_dict: dict = json.loads(resp.text)
        return {ids_dict[i]: int(str(province_id) + i) for i in ids_dict}

    def getDistrictsIDs(self, city_id: int) -> Dict[str, int]:
        resp: Response = self.session.get(
            f'http://www.weather.com.cn/data/city3jdata/station/{city_id}.html'
        )
        if resp.status_code == 404:
            return {}
        resp.encoding = resp.apparent_encoding
        ids_dict: dict = json.loads(resp.text)
        return {ids_dict[i]: int(str(city_id) + i) for i in ids_dict}

    def getIDFromName(self,
                      province: str,
                      city: Optional[str] = None,
                      district: Optional[str] = None) -> int:
        provinces = self.getProvincesIDs()
        if province in provinces:
            id_tmp = provinces[province]
            if city is None:
                return id_tmp
            else:
                cities = self.getCitiesIDs(id_tmp)
                if city in cities:
                    id_tmp = cities[city]
                    if district is None:
                        return id_tmp
                    else:
                        districts = self.getDistrictsIDs(id_tmp)
                        if district in districts:
                            return districts[district]
                        else:
                            return 0
                else:
                    return 0
        else:
            return 0

    def getNameFromID(self, id_: int) -> List[str]:
        id_str = str(id_)
        if len(id_str) == 9:
            id2 = int(id_str[:-2])
            for district, id3 in self.getDistrictsIDs(id2).items():
                if id3 == id_:
                    return [*self.getNameFromID(id2), district]
            return []
        elif len(id_str) == 7:
            id2 = int(id_str[:-2])
            for city, id3 in self.getCitiesIDs(id2).items():
                if id3 == id_:
                    return [*self.getNameFromID(id2), city]
            return []
        elif len(id_str) == 5:
            for province, id3 in self.getProvincesIDs().items():
                if id3 == id_:
                    return [province]
            return []
        else:
            return []

    @staticmethod
    def isHaveCommonArea(id1: int, id2: int) -> bool:
        id1_str = str(id1)
        id2_str = str(id2)
        if id1_str.startswith(id2_str) or id2_str.startswith(id1_str):
            return True
        else:
            return False
