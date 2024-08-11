import os
import requests

AMAP_KEY = os.getenv("AMAP_API_KEY")

def getCurrentLocation(tool_input):
    """用于获取用户当前位置的城市、adcode信息"""
    url="https://restapi.amap.com/v3/ip?key={}".format(AMAP_KEY)
    res = requests.get(url).json()
    print(url)
    print(res)
    if res["status"] != "1":
        return "对不起，无法获取您的地理位置信息"
    else:
        return {
            "city": res["city"],
            "adcode": res["adcode"],
        }

def getPostionInfo(postion,city):
    """城市名以中文输入，用于对城市地名、周边设施进行搜索，从而得到地址的详细地址，adcode信息"""
    url="https://restapi.amap.com/v3/place/text?key={}&extensions=all&keywords={}&city={}".format(AMAP_KEY,postion,city)
    res = requests.get(url).json()
    if len(res["pois"]) != 0:
        return {
            "address": res["pois"][0]["cityname"]+res["pois"][0]["adname"]+res["pois"][0]["address"]+res["pois"][0]["business_area"]+res["pois"][0]["name"],
            "adcode": res["pois"][0]["adcode"],
        }
    if len(res["suggestion"]["cities"]) != 0:
        return {
            "address": res["suggestion"]["cities"][0]["name"],
            "adcode": res["suggestion"]["cities"][0]["adcode"],
        }
    
    return "对不起，没有找到您所查询的地点和adcode信息"
    

def getTemperature(adcode):
    """根据用户输入的adcode，查询目标区域当前/未来的天气情况"""
    url = "https://restapi.amap.com/v3/weather/weatherInfo?key={}&city={}&extensions=all".format(AMAP_KEY,adcode)
    res = requests.get(url).json()
    if res["info"] != "OK":
        return "对不起，无法获取该地区的天气信息"
    return res["forecasts"]
    
if __name__ == "__main__":
    print(getCurrentLocation())
    print(getPostionInfo("郑州大学"))
    print(getTemperature('410102'))
    