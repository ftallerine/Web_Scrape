import CSSAssist
import json
import os
import statistics
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common import action_chains
import time
import calendar
import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import AccountInfo
import unittest
from selenium.webdriver.support import expected_conditions
import SeleniumAssist
import passlib
import smtplib
import collections
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from colour import Color
import EmailAssist
from passlib.hash import pbkdf2_sha256
import passlib
import MathAssist
import ColorAssist
import WeatherScrape


#   List of urls            ############################################
urlHomePage = "https://account.justenergy.com/Home"
urlAccountsPage = "https://account.justenergy.com/MyAccount"
urlAccountDetailsPage = urlAccountsPage + "/AccountDetails/"
urlUsagePage = "https://account.justenergy.com/UsageHistory/Index"
#   Base Class              ############################################


class SetUp(object):
    '''
    __init__:       Initialies driver and sets WebDriverWait object with
                    Wait time parameter
    _Login:         Logs into the profile account and selects a
                    particular account as there is more than once
    _LogOut:        Logs out of the account and prints a messages
                    confirming whether or not the action was sucessful
    _TearDown:          Closes the driver and prints a message on whether
                    of not the action was successful
    '''

    def __init__(self):
        '''
        Description:    Initialies driver and sets WebDriverWait object
                        with Wait time parameter
        '''
        # Driver setting and options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--window-size=1920x1080")
        self.chrome_options.add_argument("--incognito")
        self.chrome_driver = os.getcwd() + "\\chromedriver.exe"
        self.driver = webdriver.Chrome(
                                chrome_options=self.chrome_options,
                                executable_path=self.chrome_driver
                                )
        self.WaitTime = 25
        self.Wait = WebDriverWait(self.driver, self.WaitTime)

    '''
    def CheckPassword(self,RawPassword,EncodedPassword):
        return passlib.pbkdf2_sha256.verify(AccountInfo.PASSWORD,HASH)
    '''

    def _Login(self):
        '''
        Description:    This method navigates to the login page, enters
                        the txtUsername and txtPassword and submits the
                        form
        :return: None
        '''
        #Login to Just Energy profile
        self.driver.get(url=urlHomePage)
        #Set and submit txtUsername and txtPassword fields
        frmLogin = \
            self.driver.find_element_by_css_selector("[name=myForm]")
        txtUsername = \
            frmLogin.find_element_by_xpath('(//*[@id="username"])[2]')
        txtPassword = frmLogin.find_element_by_id("password")
        txtUsername.clear()
        txtPassword.clear()
        txtUsername.send_keys(AccountInfo.USERNAME)
        '''
        PASSWORD = input("Enter password: ")
        if(not(pbkdf2_sha256.verify(PASSWORD,AccountInfo.HASH))):
            print("Password is not valid.")
            self._LogOut()
        '''
        txtPassword.send_keys(AccountInfo.PASSWORD)
        btnProfileSubmitmit_button =     \
            frmLogin.find_element_by_xpath('//*[@id="btnLogin"]')
        print(btnProfileSubmitmit_button.text)
        btnProfileSubmitmit_button.click()
        time.sleep(15)
        #confirm login was successful
        try:
            self.driver.get_screenshot_as_file("accounts_page.png")
            #Confirm the accounts section is visible
            PageTitle = self.Wait.until(
                expected_conditions.visibility_of_element_located(
                    (By.XPATH, '//*[@id="demo"]/div[2]'))
            )
        except:
            print("Could not accounts section.")
            return

        self._SelectAccount(2)

        # confirm account selection was successfully loaded
        PageLoad = self.Wait.until(SeleniumAssist.PageHasURL(
            urlAccountDetailsPage
            )
        )
        if not (PageLoad):
            print("Page not loaded")
            return

        print("successful log in")

    def _SelectAccount(self, AccountIndex):
        # Select account
        AccountWrapper = \
            self.driver.find_element_by_xpath('//*[@id="demo"]/div[' \
                                              + str(AccountIndex) + ']')
        btnSubmit = \
            AccountWrapper.find_element_by_tag_name('a')
        self.driver.execute_script(
            "$(arguments[0]).click();", btnSubmit
        )

    def _LogOut(self):

        '''
        Description: This class method checks whether the driver
                    is on the Home Page (logged out already), on
                    the accounts page, or otherwise on an interal
                    account page and based on that logs out based on
                    that information
        :return: bool, True if log out was successful, False otherwise
        '''

        if self.driver.current_url == urlHomePage:
            print("You are already logged out.")
            return True
        elif self.driver.current_url == urlAccountsPage:
            print("You are on the accounts page.")
            try:
                AccountInfo = self.Wait.until(
                    expected_conditions.visibility_of_element_located(
                        (By.CLASS_NAME, 'account-head account-info')
                    )
                )
            except:
                print("Account Page not fully loaded")
                return False
            AccountInfoWrapper = self.driver.find_element_by_class_name(
                "account-head account-info'"
            )
            btnLogOut = AccountInfoWrapper.find_element_by_xpath(
                "//a[text()='LogOut']"
            )
            btnLogOut.click()
            time.sleep(10)
        else:
            #Check to see if the navigation bar is visible
            print("url ", self.driver.current_url)
            try:
                NavigationBar = self.Wait.until(
                    expected_conditions.visibility_of_element_located(
                        (By.CLASS_NAME, 'navbar-heading')
                    )
                )
            except:
                print("Logout button is not visible inside account.")
                return False
            NavigationHeading = self.driver.find_element_by_class_name(
                "navbar-heading"
            )
            btnLogOut = NavigationHeading.find_element_by_xpath(
                "//a[text()='Logout']"
            )
            btnLogOut.click()
            time.sleep(10)

        HomePageLoaded = self.Wait.until(
            SeleniumAssist.PageHasURL(urlHomePage)
        )
        if not(HomePageLoaded):
            print("logout was not successful")
            self._LogOut()

        print("Log out successful")
        return True

    def _TearDown(self):
        '''
        Description: Closes the browser window
        :return: None
        '''
        print("closing driver")
        self.driver.quit()
        
#   Get Usage Data Class    ############################################


class UsagePage(SetUp):
    '''
    Description/purpose:        This class iniherits the set up base
                                class with the addition that it can
                                navigate to the usage page and scrape
                                hourly data for a requested date
    Attributes:
        __init__:               Inherits the base class's constructor
        _Login:                 Inherits the base class's constructor
        SetDatet:              This method sets the date requested and
                                submits change so the page posts data
                                for that date
        GetData:  This method scraps the bar chart on the
                                page for the date requested by calling
                                the SetDates method
        _LogOut:                Inherits the base class's constructor
        _TearDown:                  Inherits the base class's constructor
    '''

    def __init__(self):
        super(UsagePage, self).__init__()

    def _Login(self):
        #Inherit the Test Base Class method
        super(UsagePage, self)._Login()
        #Driver navigates to the usage page
        self.driver.get(urlUsagePage)
        #confirm page has loaded
        UsagePageLoaded = self.Wait.until(
            SeleniumAssist.PageHasURL(urlUsagePage)
        )

        if not(UsagePageLoaded):
            print("Usage page not loaded")
            return

        #Waits for the Height chart to be visible
        try:
            HighChart = self.Wait.until(
                expected_conditions.visibility_of_element_located(
                    (By.CLASS_NAME, 'highcharts-container')
                )
            )
        except:
            self.driver.get_screenshot_as_file("Chart_Visible.png")
            print("Chart data not visible")
            return
        #Selects button to load the hourly chart data
        btnHourly = \
            self.driver.find_element_by_xpath(
                "//*[contains(text(), 'Hourly Usage')]"
            )
        self.driver.execute_script("$(arguments[0]).click();", btnHourly)
        # //////////////////////////////////////////////////////////////
        #Need to test and remove this
        time.sleep(15)
        # //////////////////////////////////////////////////////////////
        #Waits for the hourly chart to be visible
        try:
            HourlyChart = self.Wait.until(
                expected_conditions.visibility_of_element_located(
                    (By.ID, "hourlyusage")
                )
            )
            self.driver.get_screenshot_as_file("HourlyChart.png")
        except:
            print("Hourly section didn't show up")
            return

    def SetDate(self, requested_date):
        '''
        Description:    This method takes a datetime object and sets a
                        applies it to the usages page's hourly chart,
                        loading the hourly chart data for the requested
                        date
        :param requested_date:
                        type: datetime,
                        Description: this is the requested date to set
                                      for the Calendardatepicker date
                                      value
        :return:
                        type: bool
                        Description: if True setting the requested date
                                      was successful and if False it was
                                      not
        '''
        #Make sure the clandar icon is visible
        try:
            CalendarIcon = self.Wait.until(
                expected_conditions.visibility_of_element_located(
                    (By.XPATH, '//*[@id="UsageChartStartDate"]/span/i')
                )
            )
        except:
            print("Calendaricon is not visible")
            return
        ################################################################
        # Select the calendar icon (button)
        #self.driver.get_screenshot_as_file("calander_clickable.png")
        btnCalendar = self.driver.find_elements_by_xpath(
                            '//*[@id="UsageChartStartDate"]/span'
                          )
        #///////////////////////////////////////////////////////////////
        #Need to test and remove this
        time.sleep(15)
        #///////////////////////////////////////////////////////////////
        btnCalendar[0].click()
        #Make sure the calander date picker element is visible
        try:
            dtpCalendarSelect = self.Wait.until(
                expected_conditions.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                        'body > div.datepicker.datepicker-dropdown.dropdown-menu'
                     )
                )
            )
        except:
            print("Calander element is not visible")
            return
        ################################################################
        #Set the calandar's current month
        btnDatePickerSwitch = \
            self.driver.find_element_by_class_name("datepicker-switch")
        CurrentMonth = \
            (btnDatePickerSwitch.text)[:(btnDatePickerSwitch.text).find(' ')]
        RequestedMonth = \
            calendar.month_name[requested_date.month]

        #If the requested month's name does not match current month's
        ## name set the month to match the requested month
        if(CurrentMonth != RequestedMonth):
            #Click the datepicker switch button
            self.driver.execute_script(
                "$(arguments[0]).click();", btnDatePickerSwitch
            )
            #///////////////////////////////////////////////////////////
            #Need to replace Wait with try and except
            time.sleep(15)
            #///////////////////////////////////////////////////////////
            #Select the calander section
            dtpMonthCalendar = self.driver.find_element_by_css_selector(
                'body > div.datepicker.datepicker-dropdown.dropdown-menu'
            )
            #Select the requested month, the month's are a list of
            # span's and as expected in sequencial order
            #  thus the desired month will be the span indexed at the
            # same position as the month's indez
            TargetMonth = dtpMonthCalendar.find_elements_by_tag_name("span")[requested_date.month-1]
            TargetMonth.click()
            #///////////////////////////////////////////////////////////
            #need to replace this with try and except
            time.sleep(5)

        #///////////////////////////////////////////////////////////////
        #Need to check if this copied reassignment is necessary
        btnDatePickerSwitch = self.driver.find_element_by_class_name(
                                        "datepicker-switch"
                                )
        print("This is the current month ", btnDatePickerSwitch.text)

        ################################################################
        # Select the datepicker calanader itself now that it is visible
        # need to check if this is true since we may have changed the month
        dtpMonthCalendar = self.driver.find_element_by_css_selector(
                            'body > div.datepicker.datepicker-dropdown.dropdown-menu'
                        )
        TargetDate = dtpMonthCalendar.find_elements_by_xpath(
                            "//td[text()='" + str(requested_date.day) +
                            "'][@class='day']"
                        )
        print("Date selected ", TargetDate[0].text)
        TargetDate[0].click()
        #Why is this needed
        btnCalendar = self.driver.find_elements_by_xpath(
                                '//*[@id="UsageChartStartDate"]/span'
                          )
        time.sleep(15)
        btnCalendar[0].click()
        time.sleep(15)
        #Why is this needed
        txtStartDate = self.driver.find_element_by_css_selector(
                            '#dailyStartDate').get_attribute('value')
        print("date: ", txtStartDate)

        # Select the submit button for the hourly graph
        btnApply = self.driver.find_element_by_name("Apply")
        btnApply.click()
        time.sleep(10)
        #Gets the chart's date
        ChartSubTitle = self.driver.find_element_by_class_name("highcharts-subtitle")
        ChartDate = ChartSubTitle.find_element_by_css_selector("tspan:nth-child(2)").text
        ChartDay =ChartDate[3:-5]
        return(True if int(ChartDay) == requested_date.day else False)

    def GetData(self, date):
        '''
        Description:        This class method scrapes chart data for a
                            given requested date
        :param date:
            type:           datetime
            description:    this is the date requested
        :return:
            type:           tule
            description:    this is the kWh data where pairs hour and
                            it's kWh usage are stored
        '''

        if(not(UsagePage.SetDate(self, date))):
            print("Date couldn't be set")
            return

        '''
          [A] GET GRID LINE INCREMENT (DIFFERENCE BETWEEN EACH GRIDLINE)
          [B] GET CHART BARS
          [C] GET THE X-AXIS LIST OF INDICES
          [D] GET THE Y-AXIS LIST OF INDICES
          [E] COMPILE DATA 
        '''
        ################################################################
        self.driver.get_screenshot_as_file("hourly_chart.png")
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        SVG = soup.find('svg')
        ################################################################
        #[A] GET GRID LINE INCREMENT (DIFFERENCE BETWEEN EACH GRID LINE)
        # The code below gets the average difference in Height
        # from one grid line to another
        Heights = []
        gElements = SVG.find_all('g')

        #1] Get the path's description and extract only the move to value
        for path in gElements[2]:
            Height = path['d'][1:((path['d'])).find('L')]
            Height = Height.split(" ")
            for elmt in Height:
                Heights.append(elmt)
        #2] Remove any value that is repeated,
        #   as we are only interested in the vertical move to value
        #   which since each grid line is above another there will
        #   not be repeated values
        for elmt in Heights:
            if (Heights.count(elmt) > 1):
                while elmt in Heights:
                    index = Heights.index(elmt)
                    Heights.remove(elmt)
        #3] Removes any empty values
        for elmt in Heights:
            if (elmt == "" or elmt is None):
                while elmt in Heights:
                    index = Heights.index(elmt)
                    Heights.remove(elmt)
        #4] Convert string to float
        for elmt in Heights:
            index = Heights.index(elmt)
            Heights[index] = float(elmt)

        #sort Height dataset
        Heights = sorted(Heights)
        #Get differences from one grid line to another
        #***************************************************************
        #           if you are going to use three lines just make it
        #            a for loop
        #***************************************************************
        DeltsHeight = \
            [round(j, 0)-round(i, 0)
             for i, j in zip(Heights[:-1], Heights[1:])]
        #Get the average difference
        DeltsHeight = round((statistics.mean(DeltsHeight)), 0)
        print("Height Difference ", DeltsHeight)
        ################################################################
        #[B]    -   GET CHART BARS
        # The code below gets the Height of each bar in the graph
        # (representing the kWh data for a given hour)
        ChartBars = (SVG.find_all('g')[6])
        kWhData = []
        #Need to rewrite this into a line for loop
        #Need to replace ChartBars with ChartBars.find_all('rect')
        # to be more specific
        for bar in ChartBars:
            kWhData.append(round(((float(bar['height']))/DeltsHeight), 1))
        print("kWh data: ", kWhData)
        ################################################################
        # [C]    -   GET THE X-AXIS LIST OF INDICES
        #This should probably be a find method called not findAll
        X_Axis = SVG.findAll("g", {"class": "highcharts-axis-labels highcharts-xaxis-labels"})
        #print(X_Axis.text)
        X_Axis_Marks = []
        [X_Axis_Marks.append(x.text) for x in X_Axis[0]]
        #Need to check here if the number of x-axis indices match in
        # count to the number of bar graphs
        temp = []*((len(X_Axis_Marks))*2)
        for index, interval in zip(range(len(X_Axis_Marks)), X_Axis_Marks):
            #if the last x-axis index is missing fill it in
            start_index = (X_Axis_Marks[index]).find("-")
            if (index+1 >= len(X_Axis_Marks)):
                if (len(kWhData) > len(X_Axis_Marks)):
                    filler = (X_Axis_Marks[index][start_index+1:-2]) \
                             + "-" + str((int(X_Axis_Marks[index][start_index+1:-2])+1)) + \
                             (X_Axis_Marks[index][-2:])
                    temp.append(filler)
                else:
                    temp.append(interval)
                break
            end_index =(X_Axis_Marks[index+1]).find("-")
            temp.append(interval)
            filler = (X_Axis_Marks[index][start_index + 1:-2]) + "-" \
                     + (X_Axis_Marks[index + 1][:end_index]) \
                     + (X_Axis_Marks[index][-2:])
            temp.append(filler)
        X_Axis_Marks = temp
        print(X_Axis_Marks)
        ################################################################
        #[D]    -   GET THE Y-AXIS LIST OF INDICES
        Y_Axis = SVG.findAll("g", {"class": "highcharts-axis-labels highcharts-yaxis-labels"})
        Y_Axis_Marks = []
        print(Y_Axis[0].text)
        for index in Y_Axis[0]:
            Y_Axis_Marks.append(index.text)
        ################################################################
        #[E]    -   Compile chart data
        ChartData = {}
        for (x, y) in zip(X_Axis_Marks, kWhData):
            ChartData[x] = y

        return ChartData

    def EmailData(self,data):
        #Emailer variables
        TO = "franktallerine@gmail.com"
        SUBJECT = "Your Weekly Usage You Beautiful Tigerrr"
        htmlTables = {'htmlUsageOnly': "", 'htmlTempOnly': "", 'htmlUsageTemp': ""}
        TEXT = "Below is information on your usage during the period ."

        #Initiate thang
        Emailer = EmailAssist.HTMLEmailer(TO)
        Emailer.SetUp()

        #HTML variables
        #Get hours
        FirstDate = next(iter(data))
        Hours = [hour for hour in data[FirstDate]]
        formatter = '%Y-%#m-%#d'
        #formatter = '%#d-%#m-%Y'

        TableHeader = '<table style="color: black; ' \
                         'width:75%;border:2px cream solid;" \
                         border="1"><tbody><tr><th align="center">Hour</th>'
        TableColumns = '<th align="center"> {} </th>'
        TableHourColumn = '<tr><td align="center"> {} </td>'
        TableBodyData = '<td align="center" bgcolor=" {} "> {} </td>'
        htmlHeader = "<table><tbody>"
        htmlUsageSpectrum = ""
        htmlTempSpectrum = ""

        HourkWhTotal = []

        ''' 
        Colors 
            High Usage -> Red 
            Low Usage  -> Bue 
            High Temp  -> Yellow
            Low Temp   -> Red 
            
           Usage  Temperature       Color 
            High	High   -> 	  Orange (neutral) 
            High	Low	   ->     Red (Wasting Money)
            Low	    High   ->     Green (Saving Money) 
            Low	    Low	   ->     Purple 
        '''

        # Create Color Lists
        UsageSpectrum = ColorAssist.GenerateColorList("Blue", "Red", 10)
        TempSpectrum = ColorAssist.GenerateColorList("Red", "Yellow", 10)
        htmlUsageSpectrum += "<table><tbody><tr><td> Low Usage </td>" + ("<td></td>") * 8 +  "<td> High Usage </td></tr><tr>"
        htmlUsageSpectrum += ''.join([("<td bgcolor=" + str(usage) + "></td>") for usage in UsageSpectrum])
        htmlUsageSpectrum += "</tr></tbody></table>"
        htmlTempSpectrum += "<table><tbody><tr><td> Low Usage </td>" + ("<td></td>") * 8 +  "<td> High Usage </td></tr><tr>"
        htmlTempSpectrum += ''.join([("<td bgcolor=" + str(temp) + "></td>") for temp in TempSpectrum])
        htmlTempSpectrum += "</tr></tbody></table>"

        print(htmlUsageSpectrum)

        #Get Temp Data
        WeatherScraper = WeatherScrape.SetUp(self.driver)
        hourkWhAverage = {}
        TempDict = {}
        #Get Temperatures
        for day in data:
            formattedDate = day.strftime(formatter)
            DaysData = WeatherScraper.getHistoricalDateData(formattedDate)
            TempDict[day] = DaysData
        #print("These are the temperatures: ")
        #print(TempDict)

        #print(htmlUsageSpectrum)
        #print(htmlTempSpectrum)
        #Generate HTML data tables
        #Generate header
        for table in htmlTables: htmlTables[table] += TableHeader

        for date in data:
            for table in htmlTables: htmlTables[table] \
                += TableColumns.format(str(date))

        #Generate table body
        for hour in Hours:
            for table in htmlTables: htmlTables[table] \
                += TableHourColumn.format(hour)
            for day in data:
                #print(day, hour)
                #Temp Hourly Data
                formattedDate = day.strftime(formatter)
                dayWeatherData = TempDict[day]
                DateTimehour = hour[:hour.index("-")]
                if(hour[-2:] == "PM"):
                    if hour[:2] == str(12):DateTimehour = datetime.time(hour=(12))
                    else:DateTimehour = datetime.time(hour=(int(DateTimehour) + 12))
                else:
                    if hour[:2] == str(12): DateTimehour = datetime.time(hour=(0))
                    else: DateTimehour = datetime.time(hour=int(DateTimehour))
                hourTemp = float(dayWeatherData[DateTimehour]['Temperature'])
                Temperature = []
                # No you need to do this above the loops
                for item in dayWeatherData.values():
                    Temperature.append(float(item['Temperature']))
                dayTempMin = min(Temperature)
                dayTempMax = max(Temperature)
               # print("target", hourTemp, type(hourTemp))
               # print("min", dayTempMin, type(dayTempMin))
               # print("Max", dayTempMax, type(dayTempMax))
                normTempColor = TempSpectrum[
                        int(MathAssist.NormalizeNumber(hourTemp, dayTempMin, dayTempMax))
                ]
                #Usage Hourly Data
                kWhs = []
                for item in data[day].values():
                    kWhs.append(item)
                daykWhMin = min(kWhs)
                daykWhMax = max(kWhs)
                print(dayTempMax, dayTempMin)
                normUsageColor = UsageSpectrum[
                    int(MathAssist.NormalizeNumber(
                        (data[day][hour]),
                        daykWhMin,
                        daykWhMax,
                        range(0,10)
                    ))]

                #print(normUsageColor, normTempColor)
                CellColor = ColorAssist.HalfWayColor(normTempColor, normUsageColor)
                #print(CellColor)

                htmlTables['htmlUsageOnly'] += TableBodyData.format(
                    str(normUsageColor), str(data[day][hour]))
                htmlTables['htmlTempOnly'] += TableBodyData.format(
                    str(normTempColor), str(hourTemp))
                htmlTables['htmlUsageTemp'] += TableBodyData.format(
                    str(CellColor), str(data[day][hour]))
            #The hour's average kWh usage

            hourkWhAverage[hour] = statistics.mean([data[date][hour] for date in data])
            htmlTables['htmlUsageTemp'] +=  '<td>' + str(round(hourkWhAverage[hour],1)) + '</td>'
            for table in htmlTables: htmlTables[table] += "</tr>"

        htmlTables['htmlUsageTemp'] += "</tr><tr><td>Total</td>"
        daykWhData = [[data[day][hour] for hour in data[day]] for day in data]
        for idx in range(len(data)):
            htmlTables['htmlUsageTemp'] += '<td>' + str((sum(daykWhData[idx]))) + '</td>'
        htmlTables['htmlUsageTemp'] += '<td>' + str(sum(hourkWhAverage.values())) + '</td></tr>'
        for table in htmlTables: htmlTables[table] += "</tbody></table>"
        
        HTML = htmlTempSpectrum + htmlUsageSpectrum \
               + htmlTables['htmlUsageTemp'] \
               + htmlTables['htmlUsageOnly'] \
               + htmlTables['htmlTempOnly']
        print(HTML)
        #COMBINE HTML TABLES

        Emailer.SendMessage(SUBJECT,TEXT,HTML)

    def _LogOut(self):
        super(UsagePage, self)._LogOut()

    def _TearDown(self):
        super(UsagePage, self)._TearDown()
###############################################


class Test_Billing(SetUp):
    def _init_(self):
        super(Test_Billing, self)._init_()

########################################################################
#These classes will test whether or not a page or element has loaded

########################################################################
if __name__ == '__main__':
    #Create date variable
    start_date = datetime.date(2018, 7, 23)
    end_date = datetime.date(2018, 7, 23)

    delta_days = end_date - start_date
    dates = []
    for date in range(delta_days.days+1):
        dates.append(start_date+datetime.timedelta(date))

    #Test 2
    test2 = UsagePage()
    test2._Login()

    dates_list = []
    data = {}
    for date in dates:
        data[date] = test2.GetData(date)
    print(data)

    test2.EmailData(data)
    test2._LogOut()
    test2._TearDown()