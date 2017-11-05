# -*- coding: utf-8-*-
import re
import datetime
import struct
import urllib
import feedparser
import requests
import bs4
from client.app_utils import getTimezone
from semantic.dates import DateService

WORDS = ["WEATHER", "TODAY", "TOMORROW"]


def replaceAcronyms(text):
    """
    Replaces some commonly-used acronyms for an improved verbal weather report.
    """

    def parseDirections(text):
        words = {
            'N': 'north',
            'S': 'south',
            'E': 'east',
            'W': 'west',
        }
        output = [words[w] for w in list(text)]
        return ' '.join(output)
    acronyms = re.findall(r'\b([NESW]+)\b', text)

    for w in acronyms:
        text = text.replace(w, parseDirections(w))

    text = re.sub(r'(\b\d+)F(\b)', '\g<1> Fahrenheit\g<2>', text)
    text = re.sub(r'(\b)mph(\b)', '\g<1>miles per hour\g<2>', text)
    text = re.sub(r'(\b)in\.', '\g<1>inches', text)
    text = re.sub(r'(\b)&deg;(\b)', '\g<1> degrees \g<2>', text)
    text = re.sub(r'(\b)hPa(\b)', '\g<1> hectopascals \g<2>', text)


    return text


def get_locations():
    r = requests.get('http://www.wunderground.com/about/faq/' +
                     'international_cities.asp')
    soup = bs4.BeautifulSoup(r.text)
    data = soup.find(id="inner-content").find('pre').string
    # Data Stucture:
    #  00 25 location
    #  01  1
    #  02  2 region
    #  03  1
    #  04  2 country
    #  05  2
    #  06  4 ID
    #  07  5
    #  08  7 latitude
    #  09  1
    #  10  7 logitude
    #  11  1
    #  12  5 elevation
    #  13  5 wmo_id
    s = struct.Struct("25s1s2s1s2s2s4s5s7s1s7s1s5s5s")
    for line in data.splitlines()[3:]:
        row = s.unpack_from(line)
        info = {'name': row[0].strip(),
                'region': row[2].strip(),
                'country': row[4].strip(),
                'latitude': float(row[8].strip()),
                'logitude': float(row[10].strip()),
                'elevation': int(row[12].strip()),
                'id': row[6].strip(),
                'wmo_id': row[13].strip()}
        yield info


def get_forecast_by_name(location_name):
    entries = feedparser.parse("http://rss.wunderground.com/auto/rss_full/%s"
                               % urllib.quote(location_name))['entries']
    if entries:
        # We found weather data the easy way
        return entries
    else:
        # We try to get weather data via the list of stations
        for location in get_locations():
            if location['name'] == location_name:
                return get_forecast_by_wmo_id(location['wmo_id'])


def get_forecast_by_wmo_id(wmo_id):
    return feedparser.parse("http://rss.wunderground.com/auto/" +
                            "rss_full/global/stations/%s.xml"
                            % wmo_id)['entries']


def get_date_object_from_text(text, profile):
    # str => {'weekday': str, 'keyword': str}
    tz = getTimezone(profile)
    service = DateService(tz=tz)
    dateWords = ['today', 'tonight', 'tomorrow']

    print("looking for date object!")
    date = service.extractDay(text)
    weekday = None
    date_keyword = None
    print("this is the date: " + str(date))

    if not date:
        print("no explicit date in request")
        for i in range(len(dateWords)):
            print("searching for " + dateWords[i])
            index = text.find(dateWords[i])
            if index >= 0:
                print("Found " + dateWords[i])
                weekday = dateWords[i]
                date_keyword = date_keyword[i]
                break

        date = datetime.datetime.now(tz=tz)
        if not weekday:
            weekday = service.__daysOfWeek__[date.weekday()]

    if date.weekday() == datetime.datetime.now(tz=tz).weekday():
        if not date_keyword:
            date_keyword = "Today"
    elif date.weekday() == (
            datetime.datetime.now(tz=tz).weekday() + 1) % 7:
        date_keyword = "Tomorrow"
    else:
        date_keyword = "On " + weekday



def handle(text, mic, profile):
    """
    Responds to user-input, typically speech text, with a summary of
    the relevant weather for the requested date (typically, weather
    information will not be available for days beyond tomorrow).

    Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
    """
    forecast = None
    if 'wmo_id' in profile:
        forecast = get_forecast_by_wmo_id(str(profile['wmo_id']))
    elif 'location' in profile:
        forecast = get_forecast_by_name(str(profile['location']))

    if not forecast:
        mic.say("I'm sorry, I can't seem to access that information. Please " +
                "make sure that you've set your location on the dashboard.")
        return

    # Find Date
    dateObj = get_date_object_from_text(text, profile)

    tz = getTimezone(profile)

    service = DateService(tz=tz)
    date = service.extractDay(text)
    if not date:
        date = datetime.datetime.now(tz=tz)
    weekday = service.__daysOfWeek__[date.weekday()]

    if date.weekday() == datetime.datetime.now(tz=tz).weekday():
        date_keyword = "Today"
    elif date.weekday() == (
            datetime.datetime.now(tz=tz).weekday() + 1) % 7:
        date_keyword = "Tomorrow"
    else:
        date_keyword = "On " + weekday

    output = None

    # Added
    # create log output
    print('Weekday: ' +  weekday)
    print("keyword: " + date_keyword)
    log = open('log.txt', 'w')
    log.truncate()
    count = 0
    # print("test 1")
    # print("forecast: " + str(type(forecast)))
    for entry in forecast:
        #print(str(entry))
        print("elemement " + str(count))
        log.write('%d : %s \n\n' % (count, entry))

        count += 1
        try:
            date_desc = entry['title'].split()[0].strip().lower()
            # Added
            print(date_desc)

            if date_desc == 'forecast':
                # For global forecasts
                date_desc = entry['title'].split()[2].strip().lower()
                weather_desc = entry['summary']
            elif date_desc == 'current':
                # For first item of global forecasts
                continue
            else:
                # US forecasts
                weather_desc = entry['summary'].split('-')[1]
            print(weekday + ' is equal to ' + date_desc + " :  " + str(weekday == date_desc))
            if weekday == date_desc:
                output = date_keyword + \
                    ", the weather will be " + weather_desc + "."
                break
        except:
            print("~failed")
            continue
    log.close()

    if output:
        output = replaceAcronyms(output)
        mic.say(output)
    else:
        mic.say(
            "I'm sorry. I can't see that far ahead.")


def isValid(text):
    """
        Returns True if the text is related to the weather.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return bool(re.search(r'\b(weathers?|temperature|forecast|outside|hot|' +
                          r'cold|jacket|coat|rain)\b', text, re.IGNORECASE))
