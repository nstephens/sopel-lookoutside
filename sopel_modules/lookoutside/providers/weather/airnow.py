# coding=utf-8
import requests
from datetime import datetime

def airnow_aqi(bot, latitude, longitude):
    lat = '%.2f' % float(latitude)
    lon = '%.2f' % float(longitude)
    distance = 5
    success = False

    while success is False:
        url = "https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={}&longitude={}&distance={}&API_KEY={}".format(
            lat,
            lon,
            distance,
            bot.config.weather.airnow_api_key
        )
        r = requests.get(url)
        data = r.json()
        if data and r.status_code == 200:
            # we have to check to see what data is avail:
            airnow_data = {}
            if data[0]['ReportingArea']:
                airnow_data['reporting_area'] = data[0]['ReportingArea']
            
            if data[0]['StateCode']:
                airnow_data['state'] = data[0]['StateCode']
            
            if data[0]['AQI']:
                airnow_data['o3_aqi'] = data[0]['AQI']
            
            if data[0]['Category']['Name']:
                airnow_data['o3_status'] = data[0]['Category']['Name']
            
            if len(data) > 1 and data[1]['AQI']:
                airnow_data['pm_aqi'] = data[1]['AQI']
            
            if len(data) > 1 and data[1]['Category']['Name']:
                airnow_data['pm_status'] = data[1]['Category']['Name']
            
            success = True
            return airnow_data
        else:
            distance += 5 #increase range by 5 miles until we find results
