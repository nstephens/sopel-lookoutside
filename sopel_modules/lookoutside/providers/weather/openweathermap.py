# coding=utf-8
import requests
from datetime import datetime
import pytz

def openweathermap_forecast(bot, latitude, longitude, location):
    url = 'https://api.openweathermap.org/data/2.5/onecall?appid={}&lat={}&lon={}'.format(
        bot.config.weather.weather_api_key,
        latitude,
        longitude
    )

    params = {
        'exclude': 'current,minutely,hourly',
        'units': 'metric'
    }
    r = requests.get(url, params=params)
    data = r.json()
    if r.status_code != 200:
        raise Exception('Error: {}'.format(data['message']))
    else:
        weather_data = {'location': location, 'data': []}
        for day in data['daily'][0:4]:
            weather_data['data'].append({
                'dow': datetime.fromtimestamp(day['dt']).strftime('%A'),
                'summary': day['weather'][0]['main'],
                'high_temp': day['temp']['max'],
                'low_temp': day['temp']['min']
            })
        return weather_data


def openweathermap_weather(bot, latitude, longitude, location):
    url = 'https://api.openweathermap.org/data/2.5/onecall?appid={}&lat={}&lon={}'.format(
        bot.config.weather.weather_api_key,
        latitude,
        longitude
    )

    params = {
        'exclude': 'minutely,hourly,daily',
        'units': 'metric'
    }
    r = requests.get(url, params=params)
    data = r.json()

    if r.status_code != 200:
        raise Exception('Error: {}'.format(data['message']))
    else:
        weather_data = {
            'location': location,
            'weather_tz': data['timezone'],
            'temp': data['current']['temp'],
            'condition': data['current']['weather'][0]['main'],
            'humidity': float(data['current']['humidity'] / 100),  # Normalize this to decimal percentage
            'wind': {'speed': data['current']['wind_speed'], 'bearing': data['current']['wind_deg']},
            'sunrise': data['current']['sunrise'],
            'sunset': data['current']['sunset']
        }

        # convert the naive timestamp to dt obj with utc tz
        sr_utc = datetime.fromtimestamp(weather_data['sunrise'], tz=pytz.timezone('UTC'))
        ss_utc = datetime.fromtimestamp(weather_data['sunset'], tz=pytz.timezone('UTC'))
        # localize for weather regions timezone
        weather_data['sunrise'] = sr_utc.astimezone(pytz.timezone(weather_data['weather_tz'])).strftime('%I:%M %p')
        weather_data['sunset'] = ss_utc.astimezone(pytz.timezone(weather_data['weather_tz'])).strftime('%I:%M %p')
        return weather_data
