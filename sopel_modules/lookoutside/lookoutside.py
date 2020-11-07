# coding=utf-8
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, embolalia.com
# Copyright 2018, Rusty Bower, rustybower.com
# Copyright 2020, Nick Stephens, manipulate.org
# Licensed under the Eiffel Forum License 2.
from __future__ import unicode_literals, absolute_import, print_function, division

import requests
import re

from datetime import datetime

from sopel.config.types import NO_DEFAULT, ChoiceAttribute, StaticSection, ValidatedAttribute
from sopel.module import commands, example, NOLIMIT
from sopel.modules.units import c_to_f

from .providers.weather.openweathermap import openweathermap_forecast, openweathermap_weather
from .providers.weather.airnow import airnow_aqi

WEATHER_PROVIDERS = [
    'openweathermap',
]


# Define our sopel weather configuration
class WeatherSection(StaticSection):
    geocoords_provider = ValidatedAttribute('geocoords_provider', str, default='locationiq')
    geocoords_api_key = ValidatedAttribute('geocoords_api_key', str, default='')
    weather_provider = ChoiceAttribute('weather_provider', WEATHER_PROVIDERS, default=NO_DEFAULT)
    weather_api_key = ValidatedAttribute('weather_api_key', str, default='')
    weather_units = ValidatedAttribute('weather_units', str, default='')
    airnow_api_key = ValidatedAttribute('airnow_api_key', str, default='')
    sunrise_sunset = ValidatedAttribute('sunrise_sunset', str, default=False)


def setup(bot):
    bot.config.define_section('weather', WeatherSection)


# Walk the user through defining variables required
def configure(config):
    config.define_section('weather', WeatherSection, validate=False)
    config.weather.configure_setting(
        'geocoords_provider',
        'Enter GeoCoords API Provider:',
        default=NO_DEFAULT
    )
    config.weather.configure_setting(
        'geocoords_api_key',
        'Enter GeoCoords API Key:',
        default=NO_DEFAULT
    )
    config.weather.configure_setting(
        'weather_provider',
        'Enter Weather API Provider: ({}):'.format(', '.join(WEATHER_PROVIDERS)),
        default=NO_DEFAULT
    )
    config.weather.configure_setting(
        'weather_api_key',
        'Enter Weather API Key:',
        default=NO_DEFAULT
    )
    config.weather.configure_setting(
        'weather_units',
        'Enter Weather Units (metric, imperial, both):',
        default=NO_DEFAULT
    )
    config.weather.configure_setting(
        'airnow_api_key',
        'Enter AirNow.gov API Key:',
        default=NO_DEFAULT
    )
    config.weather.configure_setting(
        'sunrise_sunset',
        'Enable sunrise/sunset:',
        default=False
    )


def get_temp(weather_units, temp):
    try:
        temp = float(temp)
    except (KeyError, TypeError, ValueError):
        return 'unknown'
    
    # check user preferences, default to both if unset
    if weather_units == "both" or weather_units is None:
        return u'%d\u00B0C (%d\u00B0F)' % (round(temp), round(c_to_f(temp)))
    elif weather_units == "metric":
        return u'%d\u00B0C' % (round(temp))
    elif weather_units == "imperial":
        return u'%d\u00B0F' % (round(c_to_f(temp)))

def get_humidity(humidity):
    try:
        humidity = int(humidity * 100)
    except (KeyError, TypeError, ValueError):
        return 'unknown'
    return "Humidity: %s%%" % humidity


def get_wind(weather_units, speed, bearing):
    m_s = float(round(speed, 1))
    mph = round(m_s * 2.237)
    speed = int(round(m_s * 1.94384, 0))
    bearing = int(bearing)

    if speed < 1:
        description = 'Calm'
    elif speed < 4:
        description = 'Light air'
    elif speed < 7:
        description = 'Light breeze'
    elif speed < 11:
        description = 'Gentle breeze'
    elif speed < 16:
        description = 'Moderate breeze'
    elif speed < 22:
        description = 'Fresh breeze'
    elif speed < 28:
        description = 'Strong breeze'
    elif speed < 34:
        description = 'Near gale'
    elif speed < 41:
        description = 'Gale'
    elif speed < 48:
        description = 'Strong gale'
    elif speed < 56:
        description = 'Storm'
    elif speed < 64:
        description = 'Violent storm'
    else:
        description = 'Hurricane'

    if (bearing <= 22.5) or (bearing > 337.5):
        bearing = u'\u2193'
    elif (bearing > 22.5) and (bearing <= 67.5):
        bearing = u'\u2199'
    elif (bearing > 67.5) and (bearing <= 112.5):
        bearing = u'\u2190'
    elif (bearing > 112.5) and (bearing <= 157.5):
        bearing = u'\u2196'
    elif (bearing > 157.5) and (bearing <= 202.5):
        bearing = u'\u2191'
    elif (bearing > 202.5) and (bearing <= 247.5):
        bearing = u'\u2197'
    elif (bearing > 247.5) and (bearing <= 292.5):
        bearing = u'\u2192'
    elif (bearing > 292.5) and (bearing <= 337.5):
        bearing = u'\u2198'

    # check user preferences, default to both if unset
    if weather_units == "both" or weather_units is None:
        formSpeed = "{} m/s ({} mph)".format(str(m_s), str(mph))
    elif weather_units == "metric":
        formSpeed = "{} m/s)".format(str(m_s))
    elif weather_units == "imperial":
        formSpeed = "{} mph".format(str(mph))

    return description + ' ' + formSpeed + ' (' + bearing + ')'


def get_geocoords(bot, trigger):
    url = "https://us1.locationiq.com/v1/search.php"  # This can be updated to their EU endpoint for EU users
    data = {
        'key': bot.config.weather.geocoords_api_key,
        'q': trigger.group(2),
        'format': 'json',
        'addressdetails': 1,
        'limit': 1
    }
    r = requests.get(url, params=data)
    if r.status_code != 200:
        raise Exception(r.json()['error'])
    latitude = r.json()[0]['lat']
    longitude = r.json()[0]['lon']
    address = r.json()[0]['address']

    # Zip codes give us town versus city
    if 'city' in address.keys():
        location = '{}, {}, {}'.format(address['city'],
                                       address['state'],
                                       address['country_code'].upper())
    elif 'town' in address.keys():
        location = '{}, {}, {}'.format(address['town'],
                                       address['state'],
                                       address['country_code'].upper())
    elif 'county' in address.keys():
        location = '{}, {}, {}'.format(address['county'],
                                       address['state'],
                                       address['country_code'].upper())
    elif 'city_district' in address.keys():
        location = '{}, {}'.format(address['city_district'],
                                   address['country_code'].upper())
    else:
        location = 'Unknown'

    return latitude, longitude, location


# 24h Forecast: Oshkosh, US: Broken Clouds, High: 0°C (32°F), Low: -7°C (19°F)
def get_forecast(bot, trigger):
    location = trigger.group(2)
    if not location:
        latitude = bot.db.get_nick_value(trigger.nick, 'latitude')
        longitude = bot.db.get_nick_value(trigger.nick, 'longitude')
        location = bot.db.get_nick_value(trigger.nick, 'location')
    else:
        latitude, longitude, location = get_geocoords(bot, trigger)

    # OpenWeatherMap
    if bot.config.weather.weather_provider == 'openweathermap':
        return openweathermap_forecast(bot, latitude, longitude, location)
    # Unsupported Provider
    else:
        raise Exception('Error: Unsupported Provider')


def get_weather(bot, trigger):
    location = trigger.group(2)
    if not location:
        latitude = bot.db.get_nick_value(trigger.nick, 'latitude')
        longitude = bot.db.get_nick_value(trigger.nick, 'longitude')
        location = bot.db.get_nick_value(trigger.nick, 'location')
    else:
        latitude, longitude, location = get_geocoords(bot, trigger)

    # OpenWeatherMap
    if bot.config.weather.weather_provider == 'openweathermap':
        return openweathermap_weather(bot, latitude, longitude, location)
    # Unsupported Provider
    else:
        raise Exception('Error: Unsupported Provider')


@commands('weatherset', 'wset')
def weather_set(bot, trigger):
    if trigger.is_privmsg is False:
        return(bot.say("These commands must be sent in privmsg to avoid channel spam"))
    
    try:
        req = trigger.group(2).split(' ')
        wsetting = req[0]
        wvalue = req[1]
    except:
        helpmsg = [
            "You can customize what weather info is displayed by msging me with the following .weatherset arguments:",
            "'.weatherset units [metric|imperial|both]'",
            "'.weatherset [condition|humidity|sunrise|wind|aqi] [true|false]"
        ]
        for msg in helpmsg:
            bot.say(msg)
        return

    if re.search("units", wsetting):
        if wvalue == "imperial" or wvalue == "metric" or wvalue == "both":
            bot.db.set_nick_value(trigger.nick, 'weather-units', wvalue)
            return(bot.say("Preference set {wsetting}: {wvalue}".format(wsetting=wsetting, wvalue=wvalue)))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}, or {opt3}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='metric',
                opt2='imperial',
                op3='both'
            ))
    
    if re.search("condition", wsetting):
        if wvalue == "true" or wvalue == "false":
            bot.db.set_nick_value(trigger.nick, 'weather-show-condition', wvalue)
            return(bot.say("Preference set {wsetting}: {wvalue}".format(wsetting=wsetting, wvalue=wvalue)))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='true',
                opt2='false',
            ))
    
    if re.search("humidity", wsetting):
        if wvalue == "true" or wvalue == "false":
            bot.db.set_nick_value(trigger.nick, 'weather-show-humidity', wvalue)
            return(bot.say("Preference set {wsetting}: {wvalue}".format(wsetting=wsetting, wvalue=wvalue)))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='true',
                opt2='false',
            ))

    if re.search("sunrise", wsetting):
        if wvalue == "true" or wvalue == "false":
            bot.db.set_nick_value(trigger.nick, 'weather-show-sunriseset', wvalue)
            return(bot.say("Preference set {wsetting}: {wvalue}".format(wsetting=wsetting, wvalue=wvalue)))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='true',
                opt2='false',
            ))
    
    if re.search("wind", wsetting):
        if wvalue == "true" or wvalue == "false":
            bot.db.set_nick_value(trigger.nick, 'weather-show-wind', wvalue)
            return(bot.say("Preference set {wsetting}: {wvalue}".format(wsetting=wsetting, wvalue=wvalue)))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='true',
                opt2='false',
            ))
    
    if re.search("aqi", wsetting):
        if wvalue == "true" or wvalue == "false":
            bot.db.set_nick_value(trigger.nick, 'weather-show-aqi', wvalue)
            return(bot.say("Preference set {wsetting}: {wvalue}".format(wsetting=wsetting, wvalue=wvalue)))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='true',
                opt2='false',
            ))
    
    if re.search("reset", wsetting):
        if wvalue == "true":
            for wsetting in ['weather-units', 'weather-show-condition', 'weather-show-humidity', 'weather-show-sunriseset', 'weather-show-wind', 'weather-show-aqi']:
                bot.db.delete_nick_value(trigger.nick, wsetting)
            return(bot.say("Preferences reset to default"))
        else:
            return bot.say("sorry, {wvalue} isn't a valid option for {wsetting}. Please use {opt1}, {opt2}.".format(
                wvalue=wvalue,
                wsetting=wsetting,
                opt1='true',
                opt2='false',
            ))

@commands('weather', 'wea')
@example('.weather')
@example('.weather London')
@example('.weather Seattle, US')
@example('.weather 90210')
def weather_command(bot, trigger):
    """.weather location - Show the weather at the given location."""
    if bot.config.weather.weather_api_key is None or bot.config.weather.weather_api_key == '':
        return bot.reply("Weather API key missing. Please configure this module.")
    if bot.config.weather.geocoords_api_key is None or bot.config.weather.geocoords_api_key == '':
        return bot.reply("GeoCoords API key missing. Please configure this module.")

    # Ensure we have a location for the user
    location = trigger.group(2)
    if not location:
        latitude = bot.db.get_nick_value(trigger.nick, 'latitude')
        longitude = bot.db.get_nick_value(trigger.nick, 'longitude')
        if not latitude or not longitude:
            return bot.say("I don't know where you live. "
                           "Give me a location, like {pfx}{command} London, "
                           "or tell me where you live by saying {pfx}setlocation "
                           "London, for example.".format(command=trigger.group(1),
                                                         pfx=bot.config.core.help_prefix))

    data = get_weather(bot, trigger)


    # check to see the user has configured their preferences
    if bot.db.get_nick_value(trigger.nick, 'weather-units') is None:
        nagcount = bot.db.get_nick_value(trigger.nick, 'weather-config-nag', default=0)
        if nagcount == 0:
            helpmsg = ("I noticed that you have not told me how you like to see your weather!  "
            "You can tailor your experience by using the .weatherset (or .wset) command."
            )
            exmsg = ("You can set your units to Imperial (US), Metric (EU), or both, as well as setting "
                    " any of the following features to true (shown) or false: "
                    "condition | humidity | sunrise | wind | aqi. Use .help weatherset for more info!"
            )
            nagmsg = "Don't worry if you don't have time, I'll remind you later (but not too often!)"
            for msg in [helpmsg, exmsg, nagmsg]:
                bot.say(msg, trigger.nick)
        nagcount += 1
        if nagcount >= 10:
            nagcount = 0 #reset
        bot.db.set_nick_value(trigger.nick, 'weather-config-nag', nagcount)

    # start customizing the return string

    # get weather units preference
    if bot.db.get_nick_value(trigger.nick, 'weather-units') is not None:
        weather_units = bot.db.get_nick_value(trigger.nick, 'weather-units')
    else:
        weather_units = 'both'

    weather = u'{location}: {temp}'.format(
        location=data['location'],
        temp=get_temp(weather_units, data['temp'])
    )

    if bot.db.get_nick_value(trigger.nick, 'weather-show-condition') is True or bot.db.get_nick_value(trigger.nick, 'weather-show-condition') is None:
        weather += ', {condition}'.format(condition=data['condition'])
    
    if bot.db.get_nick_value(trigger.nick, 'weather-show-humidity') is True or bot.db.get_nick_value(trigger.nick, 'weather-show-humidity') is None:
        weather += ', {humidity}'.format(humidity=get_humidity(data['humidity']))

    # # Some providers don't give us UV Index
    # if 'uvindex' in data.keys():
    #     weather += ', UV Index: {uvindex}'.format(uvindex=data['uvindex'])

    if bot.db.get_nick_value(trigger.nick, 'weather-show-sunriseset') is True or bot.db.get_nick_value(trigger.nick, 'weather-show-sunriseset') is None:
        weather += ', Sunrise: {sunrise} Sunset: {sunset}'.format(sunrise=data['sunrise'], sunset=data['sunset'])
    
    if bot.db.get_nick_value(trigger.nick, 'weather-show-wind') is True or bot.db.get_nick_value(trigger.nick, 'weather-show-wind') is None:
        weather += ', {wind}'.format(wind=get_wind(weather_units, data['wind']['speed'], data['wind']['bearing']))
    
    if bot.db.get_nick_value(trigger.nick, 'weather-show-aqi') is True or bot.db.get_nick_value(trigger.nick, 'weather-show-aqi') is None:
        aqi_method = "weather" # to handle how we build the string
        weather += ',{aqi_data}'.format(aqi_data=get_aqi(bot, latitude, longitude, aqi_method))

    return bot.say(weather)


@commands('forecast')
@example('.forecast')
@example('.forecast London')
@example('.forecast Seattle, US')
@example('.forecast 90210')
def forecast_command(bot, trigger):
    aqi_method = "forecast" # to handle how we build the string
    """.forecast location - Show the weather forecast for tomorrow at the given location."""
    if bot.config.weather.weather_api_key is None or bot.config.weather.weather_api_key == '':
        return bot.reply("Weather API key missing. Please configure this module.")
    if bot.config.weather.geocoords_api_key is None or bot.config.weather.geocoords_api_key == '':
        return bot.reply("GeoCoords API key missing. Please configure this module.")

    # Ensure we have a location for the user
    location = trigger.group(2)
    if not location:
        latitude = bot.db.get_nick_value(trigger.nick, 'latitude')
        longitude = bot.db.get_nick_value(trigger.nick, 'longitude')
        if not latitude or not longitude:
            return bot.say("I don't know where you live. "
                           "Give me a location, like {pfx}{command} London, "
                           "or tell me where you live by saying {pfx}setlocation "
                           "London, for example.".format(command=trigger.group(1),
                                                         pfx=bot.config.core.help_prefix))

    data = get_forecast(bot, trigger)

    # # start customizing the return string

    # get weather units preference
    if bot.db.get_nick_value(trigger.nick, 'weather-units') is not None:
        weather_units = bot.db.get_nick_value(trigger.nick, 'weather-units')
    else:
        weather_units = 'both'

    forecast = '{location}'.format(location=data['location'])

    for day in data['data']:
        forecast += ' :: {dow} - {summary} - {high_temp} / {low_temp}'.format(
            dow=day.get('dow'),
            summary=day.get('summary'),
            high_temp=get_temp(weather_units, day.get('high_temp')),
            low_temp=get_temp(weather_units, day.get('low_temp'))
        )
    return bot.say(forecast)

@commands('aqi')
@example('.aqi')
@example('.aqi London')
@example('.aqi Seattle, US')
@example('.aqi 90210')
def aqi_command(bot, trigger):
    """.aqi location - Show the air quality index within 5miles of set or given location."""
    aqi_method = "aqi" # to handle how we build the string
    # Ensure we have a location for the user
    location = trigger.group(2)
    if not location:
        latitude = bot.db.get_nick_value(trigger.nick, 'latitude')
        longitude = bot.db.get_nick_value(trigger.nick, 'longitude')
        location = bot.db.get_nick_value(trigger.nick, 'location')
    else:
        latitude, longitude, location = get_geocoords(bot, trigger)
    if not latitude or not longitude:
        return bot.say("I don't know where you live. "
                        "Tell me where you live by saying {pfx}setlocation "
                        "Los Angeles, for example.".format(command=trigger.group(1),
                                                        pfx=bot.config.core.help_prefix))

    aqi = get_aqi(bot, latitude, longitude, aqi_method)

    return bot.say(aqi)

def get_aqi(bot, latitude, longitude, aqi_method):
    data = airnow_aqi(bot, latitude, longitude)
    aqi = ""
    # Fremont, CA: O3 Good (AQI: 28), PM2.5 Good (AQI: 18)
    if aqi_method == "aqi":
        if 'reporting_area' in data.keys():
            aqi += "{}".format(data['reporting_area'])
        
        if 'state' in data.keys():
            aqi += ", {}".format(data['state'])

        aqi += ": "

    if 'o3_status' in data.keys():
        aqi += " O3 {}".format(data['o3_status'])
        
    if 'o3_aqi' in data.keys():
        aqi += " (AQI: {})".format(data['o3_aqi'])
    
    if 'pm_status' in data.keys():
        aqi += " PM2.5 {}".format(data['pm_status'])
    
    if 'pm_aqi' in data.keys():
        aqi += " (AQI: {})".format(data['pm_aqi'])

    return aqi
        
@commands('setlocation')
@example('.setlocation London')
@example('.setlocation Seattle, US')
@example('.setlocation 90210')
@example('.setlocation w7174408')
def update_location(bot, trigger):
    if bot.config.weather.geocoords_api_key is None or bot.config.weather.geocoords_api_key == '':
        return bot.reply("GeoCoords API key missing. Please configure this module.")

    # Return an error if no location is provided
    if not trigger.group(2):
        bot.reply('Give me a location, like "London" or "90210".')
        return NOLIMIT

    # Get GeoCoords
    latitude, longitude, location = get_geocoords(bot, trigger)

    # Assign Latitude & Longitude to user
    bot.db.set_nick_value(trigger.nick, 'latitude', latitude)
    bot.db.set_nick_value(trigger.nick, 'longitude', longitude)
    bot.db.set_nick_value(trigger.nick, 'location', location)

    return bot.reply('I now have you at {}'.format(location))
