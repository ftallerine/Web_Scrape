import os
#Selenium and bs4 modules
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common import action_chains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import SeleniumAssist
from bs4 import BeautifulSoup
#Time modules
from time import strptime
import time
import datetime
#other modules
import collections
import statistics

#   List of url(s)            ############################################
urlHomePate = "https://www.wunderground.com/"

#   Base Class              ############################################

'''
class MyOrderedDict(collections.OrderedDict):
   def next_key(self, key):
        next = self._OrderedDict__map[key][1]
        if next is self._OrderedDict__root:
            raise ValueError("{!r} is the last key".format(key))
        return next[2]
   def first_key(self):
            for key in self: return key
            raise ValueError("OrderedDict() is empty")
'''


class SetUp(object):
    '''

    '''
    def __init__(self, driver):
        '''and sets WebDriverWait object
                        with Wait time parameter
        '''
        self.driver = driver
        self.WaitTime = 15
        self.Wait = WebDriverWait(self.driver, self.WaitTime)

    def getHistoricalDateData(self,Date):
        formatter = '%I:%M %p'
        urlDate = urlHomePate \
                  + "/history/daily/us/tx/winchester-country/KTXWINCH2/date/" \
                  + Date + "?cm_ven=localwx_history"
        self.driver.get(urlDate)
        self.driver.refresh()
        # confirm page was successfully loaded
        self.driver.get_screenshot_as_file("temp_date_data.png")
        PageLoad = self.Wait.until(SeleniumAssist.PageHasURL(urlDate))
        if not (PageLoad):
            print("Page not loaded")
            return
        self.driver.refresh()
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        CalandarTempTable = soup.find_all(
            "table",
            {"class": "tablesaw-sortable"}
        )
        Rows = CalandarTempTable[0].find_all("tr")
        HourData = collections.OrderedDict()
        Headers = []
        #Get each header
        for header in Rows[0]:
            header = header.find("button")
            if(header == -1): continue
            else: Headers.append(header.string)
        #Get table body's data
        for row in Rows[1:]:
            # Get fist cell, ie. the hour
            span = (row.find_all("span", text=True))
            #collect each cell in the row
            # why loop through each cell????
            for idx, item in zip(range(len(span)), span):
                hour = RoundHour(datetime.datetime.strptime(span[0].string,formatter).time())
                HourData[hour] = {}
            #collect each cell's value in the row after the first cell
            for header, data in zip(Headers[1:],span[1:]):
                HourData[hour][header] = data.string
        #Sort hour data by key (by the hour)
        HourData = collections.OrderedDict(
            sorted(HourData.items(),key=lambda t: t[0])
        )
        #Fill in any missing data (missing hours) and assign temperature
        HourData = self.FillInTimes((HourData))
        # Sort hour data by key (by the hour)
        # is this really necessary ???
        HourData = collections.OrderedDict(
            sorted(HourData.items(), key=lambda t: t[0])
        )
        return HourData


    def FillInTimes(self, hourdata):
        #check if day is empty
        if len(hourdata) == 0:
            print("Hour data empty")
            return
        #convert each string hour to datetime type
        fulltimes = [datetime.time(hour) for hour in range(24)]
        # If there are hours missing, fill them in
        if not(set(fulltimes) == set(hourdata)):
            for hour in fulltimes:
                if hour not in hourdata:
                    #get nearest before and after temperatures
                    HourBeforeTemp, HourAfterTemp = \
                        self.TempBeforeAndAfter(hour,fulltimes,hourdata)
                    #Take the average and assign it to the missing hour
                    AverageTemp = round(statistics.mean([int(HourBeforeTemp),int(HourAfterTemp)]),0)
                    hourdata[hour] = {}
                    hourdata[hour]['Temperature'] = AverageTemp
        return  hourdata

    def TempBeforeAndAfter(self, hour,hoursinday, data):
        #change in hours increment equal to one hour
        deltaHour = datetime.timedelta(hours=1)
        earliesthour = min(data)
        latesthour = max(data)
        #why do you need to assign these variables here???
        BeforeTemp = None
        AfterTemp = None
        #if this is the first hour
        if hour == hoursinday[0]:
            BeforeTemp = AfterTemp = data[earliesthour]['Temperature']
        #if this is the last hour
        elif hour == hoursinday[-1]:
             BeforeTemp = AfterTemp = data[latesthour]['Temperature']
        else:
            #Otherwise the before hour is know to exist and after hour
            # existing or will be assigned
            BeforeHour = datetime.time(hour.hour-1)
            BeforeTemp = data[BeforeHour]['Temperature']
            if hour < earliesthour:
                AfterTemp = data[earliesthour]['Temperature']
            else:
                #if this is the latest hour in the day simply set
                # it equal to the average
                if hour > latesthour:
                    TempSum = 0
                    for hour in data:
                        TempSum += float(data[hour]['Temperature'])
                    AverageTemp = TempSum/len(data)
                    AfterTemp = AverageTemp
                #else get the next hour in the list
                else:
                    AfterHour = list((data.keys()))[BeforeHour.hour+1]
                    AfterTemp = data[AfterHour]['Temperature']
        return (BeforeTemp, AfterTemp)

    def teardown(self):
        self.driver.quit()

#need to add this to a separate module
def RoundHour(time):
    if(time.minute >= 30):
        return (time.replace(
                        second=0,
                        microsecond=0,
                        minute=0,
                        hour=(time.hour+1)%24
                    )
                )
    else:
        return (time.replace(
                        second=0,
                        microsecond=0,
                        minute=0
                    )
                )

if __name__ == '__main__':

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--incognito")
    chrome_driver = os.getcwd() + "\\chromedriver.exe"
    driver = webdriver.Chrome(
        chrome_options=chrome_options,
        executable_path=chrome_driver
    )
    tester = SetUp(driver)
    tester.getHistoricalDateData("2018-7-1")

