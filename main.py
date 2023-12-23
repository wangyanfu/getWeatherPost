import json
import os
import requests
from requests_oauthlib import OAuth1Session

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
    
    try:
        result = requests.get(weatherUrl, timeout=30)
    except Exception as e:
        print(e)
        
    return result

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

def tweet_post(weather_data):
    # tweet auth
    consumer_key = os.environ["consumer_key"]
    consumer_secret = os.environ["consumer_secret"]
    access_token = os.environ["access_token"]
    access_token_secret = os.environ["access_token_secret"]
    
    # Be sure to add replace the text of the with the text you wish to Tweet. You can also add parameters to post polls, quote Tweets, Tweet with reply settings, and Tweet to Super Followers in addition to other features.
    payload = {"text": weather_data}

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

def main():
    # get the weather data
    weather_data = parse_weather_data()
    tweet_post(weather_data)
    
    
    
    
# Call the main function to test with the provided example
main()