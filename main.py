import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
import requests
import time
import logging
from requests_oauthlib import OAuth1Session

logging.basicConfig(level=logging.ERROR)

def dms_to_decimal(degrees, minutes, seconds):
    """
    Convert degrees, minutes, seconds (DMS) to decimal degrees.

    :param degrees: The degrees part of the coordinate
    :param minutes: The minutes part of the coordinate
    :param seconds: The seconds part of the coordinate
    :return: The coordinate in decimal degrees
    """
    return float(degrees + (minutes / 60) + (seconds / 3600))

def get_weather_info():
    """
    Construct and request the weather api
    
    :params see doc: https://openweathermap.org/api/one-call-3
    
    Returns: weather data from openweathermap api
        _type_: json-type data
    """
    # Example coordinates: 30°41'08"N 104°07'30"E
    # Latitude conversion
    latitude_dms = (30, 41, 8)
    decimal_latitude = dms_to_decimal(*latitude_dms)
    # Longitude conversion
    longitude_dms = (104, 7, 30)
    decimal_longitude = dms_to_decimal(*longitude_dms)
    # API_key
    weather_api_key = os.environ["weather_api_key"]
    # Temp type
    units = "metric" 
    # Construct the url
    weatherUrl = f"https://api.openweathermap.org/data/3.0/onecall?lat={decimal_latitude}&lon={decimal_longitude}&appid={weather_api_key}&units={units}"
    
    attempts, max_attempts, backoff_factor = 0, 3, 2
    while attempts < max_attempts:
        try:
            result = requests.get(weatherUrl, timeout=30)

            if result.status_code == 200:
                return result
            else:
                logging.error(f"API 请求返回非 200 状态码: {result.status_code}, 响应内容: {result.text}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"API 请求异常: {e}")
            attempts += 1
            time.sleep(backoff_factor ** attempts)  # 指数退避

    logging.error("超过最大重试次数，API 请求失败")
    return None


def parse_weather_data():
    """Construct the weather info."""
    result = get_weather_info().json()
    current_info = result["current"]
    weather, description, temp, wind_speed, visibility, human_feel_temp, clouds, pressure = \
            current_info["weather"][0]["main"], current_info["weather"][0]["description"], current_info["temp"],\
            current_info["wind_speed"], current_info["visibility"] / 1000, \
                current_info["feels_like"], current_info["clouds"], current_info["pressure"]
            
    output_info = f"""
    Current weather of Chengdu City:
{weather} ({description}), temp: {temp} °C, feels like: {human_feel_temp} °C
Wind speed: {wind_speed} m/s, visibility: {visibility} km
Cloudiness: {clouds}%
Pressure at sea level: {pressure} hPa
    """
    return output_info    


def get_aqi_data():
    location = "chengdu"
    aqi_token = os.environ["aqi_token"]
    aqi_url = f"https://api.waqi.info/feed/{location}/?token={aqi_token}"

    attempts, max_attempts, backoff_factor = 0, 3, 2
    while attempts < max_attempts:
        try:
            result = requests.get(aqi_url, timeout=30)

            if result.status_code == 200:
                return result
            else:
                logging.error(f"API 请求返回非 200 状态码: {result.status_code}, 响应内容: {result.text}")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"API 请求异常: {e}")
            attempts += 1
            time.sleep(backoff_factor ** attempts)  # 指数退避

    logging.error("超过最大重试次数，API 请求失败")
    return None
    

def parse_aqi_data():
    aqi = get_aqi_data().json()['data']['aqi']
    if aqi <= 50:
        return f"""Current air quality of Chengdu City: {aqi}. 
Air quality is considered satisfactory, and air pollution poses little or no risk."""
    elif aqi > 50 and aqi <= 100:
        return f"""Current air quality of Chengdu City: {aqi}.
Air quality is acceptable; 
however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution."""
    elif aqi > 100 and aqi <= 150:
        return f"""Current air quality of Chengdu City: {aqi}.
Members of sensitive groups may experience health effects. 
The general public is not likely to be affected."""
    elif aqi > 150 and aqi <= 200:
        return f"""Current air quality of Chengdu City: {aqi}.
Everyone may begin to experience health effects; 
members of sensitive groups may experience more serious health effects."""
    elif aqi > 200 and aqi <= 300:
        return f"""Current air quality of Chengdu City: {aqi}.
Health warnings of emergency conditions. 
The entire population is more likely to be affected."""
    else:
        return f"""Current air quality of Chengdu City: {aqi}.
Health alert: everyone may experience more serious health effects."""


def tweet_post(message):
    # tweet auth
    consumer_key = os.environ["consumer_key"]
    consumer_secret = os.environ["consumer_secret"]
    access_token = os.environ["access_token"]
    access_token_secret = os.environ["access_token_secret"]

     # Be sure to add replace the text of the with the text you wish to Tweet. You can also add parameters to post polls, quote Tweets, Tweet with reply settings, and Tweet to Super Followers in addition to other features.
    payload = {"text": message}
    
    # Make the request
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Making the request
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(response.status_code, response.text)
        )

    print("Response code: {}".format(response.status_code))

    # Saving the response as JSON
    json_response = response.json()
    print(json.dumps(json_response, indent=4, sort_keys=True))

def lambda_handler(event, context):
    # 获取触发事件的规则 ARN
    rule_arn = event.get('resources', [])[0] if event.get('resources') else None

    if rule_arn:
        if 'lambda' in rule_arn:
            # 处理由 'lambda' 规则触发的事件
            weather_data = parse_weather_data()
            tweet_post(weather_data)
        elif 'AQI_request' in rule_arn:
            # 处理由 'AQI_request' 规则触发的事件
            aqi_data = parse_aqi_data()
            tweet_post(aqi_data)
    #     else:
    #         # 未知规则的默认处理
    #         handle_default(event)
    # else:
    #     # 非 EventBridge 触发的事件处理
    #     handle_other_trigger(event)

