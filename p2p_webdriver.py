import calendar
import credentials
from datetime import datetime,  date,  timedelta
import glob
import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import time

class P2P:
    def __init__(self,  name, login_url, statement_url, logout_url=None):
        self.name = name
        self.login_url = login_url
        self.statement_url = statement_url
        self.logout_url = logout_url
        self.delay = 5
        self.init_webdriver()

    def init_webdriver(self):
        #TODO: hide browser windows
        options = webdriver.ChromeOptions()
        dl_location = os.path.join(os.getcwd(), 'p2p_downloads')
        prefs = {"download.default_directory": dl_location}
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        self.driver = driver

    def open_start_page(self, wait_until, title_check=None):
        #Most platforms use their name in the title, title_check will handle the few cases where they don't
        if title_check==None:
            title_check = self.name

        try:
            self.driver.get(self.login_url)
            self.wdwait(wait_until)
            assert title_check in self.driver.title
        except AssertionError:
            print('Die {0} Webseite konnte nicht geladen werden.'.format(self.name))
            return -1
        except TimeoutException:
            print('Das Laden der {0} Webseite hat zu lange gedauert.'.format(self.name))

        return 0

    def log_into_page(self, name_field, password_field, wait_until, login_field=None, find_login_by=By.XPATH,\
        submit_button=None,  find_submit_button='xpath',  fill_delay=0):

        try:
            getattr(credentials, self.name)['username']
            getattr(credentials, self.name)['password']
        except AttributeError:
            print('Username/Passwort für {0} sind nicht vorhanden. Bitte manuell zu credentials.py hinzufügen.'\
                .format(self.name))
            return -1

        try:
            if login_field is not None:
                self.driver.find_element(find_login_by, login_field).click()

            self.wdwait(EC.element_to_be_clickable((By.NAME, name_field)))
            elem = self.driver.find_element_by_name(name_field)
            elem.clear()
            elem.send_keys(getattr(credentials, self.name)['username'])
            time.sleep(fill_delay)
            elem = self.driver.find_element_by_name(password_field)
            elem.clear()
            elem.send_keys(getattr(credentials, self.name)['password'])
            elem.send_keys(Keys.RETURN)

            if submit_button is not None:
                if find_submit_button == 'xpath':
                    self.driver.find_element_by_xpath(submit_button).click()
                elif find_submit_button == 'name':
                    self.driver.find_element_by_name(submit_button).click()
                else:
                    print('Unbekannte Suchmethode beim Senden der {0}-Logindaten.'.format(self.name))
                    return -1

            self.wdwait(wait_until)
        except NoSuchElementException:
            print("{0}-Loginseite konnte leider nicht geladen werden.".format(self.name))
            return -1
        except TimeoutException:
            print("{0}-Login war leider nicht erfolgreich. Passwort korrekt?".format(self.name))
            return -1

        return 0

    def open_account_statement_page(self, title, element_to_check, check_by=By.ID):
        try:
            self.driver.get(self.statement_url)
            self.wdwait(EC.presence_of_element_located((check_by, element_to_check)))
            assert title in self.driver.title
        except (AssertionError,  TimeoutException):
            print("{0} Kontoauszugsseite konnte nicht geladen werden.".format(self.name))
            return -1

        return 0

    def logout_by_button(self, logout_elem,  logout_elem_by, wait_until, hover_elem=None, hover_elem_by=None):
        try:
            if hover_elem is not None:
                elem = self.driver.find_element(hover_elem_by, hover_elem)
                hover = ActionChains(self.driver).move_to_element(elem)
                hover.perform()
                self.wdwait(EC.element_to_be_clickable((logout_elem_by, logout_elem)))

            self.driver.find_element(logout_elem_by, logout_elem).click()
            self.wdwait(wait_until)
        except TimeoutException:
            print('{0}-Logout war nicht erfolgreich!'.format(self.name))
            #continue anyway

    def logout_by_url(self, wait_until):
        try:
            self.driver.get(self.logout_url)
            self.wdwait(wait_until)
        except TimeoutException:
            print("{0}-Logout war nicht erfolgreich!".format(self.name))

    def generate_statement_direct(self, start_date, end_date, start_element, end_element, date_format,\
        find_elem_by=By.ID, wait_until=None, submit_btn_id=None, submit_btn_name=None):
        try:
            date_from = self.driver.find_element(find_elem_by, start_element)
            date_from.send_keys(Keys.CONTROL + 'a')
            date_from.send_keys(datetime.strftime(start_date, date_format))

            try:
                date_to = self.driver.find_element(find_elem_by,  end_element)
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(datetime.strftime(end_date, date_format))
                date_to.send_keys(Keys.RETURN)
            except StaleElementReferenceException: # some sites refresh the page after a change which leads to this exception
                date_to = self.driver.find_element(find_elem_by,  end_element)
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(datetime.strftime(end_date, date_format))

            if submit_btn_name is not None:
                self.wdwait(EC.element_to_be_clickable((By.NAME, submit_btn_name)))
                self.driver.find_element_by_name(submit_btn_name).click()
            elif submit_btn_id is not None:
                self.wdwait(EC.element_to_be_clickable((By.ID, submit_btn_id)))
                time.sleep(1) # Mintos needs some time until the button really works, TODO: find better fix
                self.driver.find_element_by_id(submit_btn_id).click()

            if wait_until is not None:
                self.wdwait(wait_until)
        except NoSuchElementException:
            print('Generierung des {0} Kontoauszugs konnte nicht gestartet werden.'.format(self.name))
            return -1
        except TimeoutException:
            print('Generierung des {0} Kontoauszugs hat zu lange gedauert.'.format(self.name))
            return -1

        return 0

    def generate_statement_calendar(self, start_date, end_date, default_dates, arrows, days_table,\
        calendar_id_by, calendar_id):

        try:
            #identify the two calendars
            if calendar_id_by == 'name':
                start_calendar = self.driver.find_element_by_name(calendar_id[0])
                end_calendar = self.driver.find_element_by_name(calendar_id[1])
            elif calendar_id_by == 'class':
                datepicker = self.driver.find_elements_by_xpath("//div[@class='{0}']".format(calendar_id))
                start_calendar = datepicker[0]
                end_calendar = datepicker[1]
            else: # this should never happen
                print('Keine ID für Kalender übergeben')
                return -1

            # how many clicks on the arrow buttons are necessary?
            start_calendar_clicks = get_calendar_clicks(start_date,  default_dates[0])
            end_calendar_clicks = get_calendar_clicks(end_date,  default_dates[1])

            # identify the arrows for both start and end calendar
            left_arrows = self.driver.find_elements_by_xpath("//{0}[@class='{1}']".format(arrows[2], arrows[0]))
            right_arrows = self.driver.find_elements_by_xpath("//{0}[@class='{1}']".format(arrows[2], arrows[1]))

            # set start_date
            start_calendar.click()
            self.wdwait(EC.visibility_of(left_arrows[0]))
            if start_calendar_clicks < 0:
                for i in range(0, abs(start_calendar_clicks)):
                    left_arrows[0].click()
            elif start_calendar_clicks > 0:
                for i in range(0, start_calendar_clicks):
                    right_arrows[0].click()

            # get all dates from left calendar and find the start day
            day_table_class_name = days_table[0]
            day_table_identifier = days_table[1]
            current_day_identifier = days_table[2]
            id_from_calendar = days_table[3]

            if id_from_calendar == True:
                start_days_xpath = "//*[@{0}='{1}']//table//td".format(day_table_identifier, start_calendar.get_attribute('id'))
            else:
                start_days_xpath = "//*[@{0}='{1}']//table//td".format(day_table_identifier, day_table_class_name)
            all_days = self.driver.find_elements_by_xpath(start_days_xpath)

            for elem in all_days:
                if current_day_identifier=='':
                    if elem.text == str(start_date.day):
                        elem.click()
                else:
                    if elem.text == str(start_date.day) and elem.get_attribute('class') == current_day_identifier:
                        elem.click()

            # set end_date
            end_calendar.click()
            self.wdwait(EC.visibility_of(left_arrows[1]))
            if end_calendar_clicks < 0:
                for i in range(0, abs(end_calendar_clicks)):
                    left_arrows[1].click()
            elif end_calendar_clicks > 0:
                for i in range(0, end_calendar_clicks):
                    right_arrows[1].click()

            # get all dates from right calendar and find the end day
            if id_from_calendar == True:
                end_days_xpath = "//*[@{0}='{1}']//table//td".format(day_table_identifier, end_calendar.get_attribute('id'))
            else:
                end_days_xpath = "//*[@{0}='{1}']//table//td".format(day_table_identifier, day_table_class_name)
            all_days = self.driver.find_elements_by_xpath(end_days_xpath)

            for elem in all_days:
                if current_day_identifier=='':
                    if elem.text == str(end_date.day):
                        elem.click()
                else:
                    if elem.text == str(end_date.day) and elem.get_attribute('class') == current_day_identifier:
                        elem.click()
        except (NoSuchElementException,  TimeoutException):
            print('{0}: Konnte die gewünschten Daten für den Kontoauszug nicht setzen.'.format(self.name))
            return -1

        return 0

    def download_statement(self, default_name, file_format, download_btn, find_btn_by, actions = None):
        try:
            download_button = self.driver.find_element(find_btn_by, download_btn)

            if actions == 'move_to_element':
                action = ActionChains(self.driver)
                action.move_to_element(download_button).perform()
            download_button.click()
        except NoSuchElementException:
            print('Download des {0} Kontoauszugs konnte nicht gestartet werden.'.format(self.name))
            return -1

        download_finished = False
        duration = 0
        while download_finished == False:
            list = glob.glob('p2p_downloads/{0}.{1}'.format(default_name, file_format))
            if len(list) == 1:
                download_finished = True
            elif len(list) == 0:
                list = glob.glob('p2p_downloads/{0}.{1}.crdownload'.format(default_name, file_format))
                if len(list) < 1 and duration > 1:
                    print('Download des {0} Kontoauszugs abgebrochen.'.format(self.name))
                    return -1
                elif duration < 1:
                    time.sleep(1)
                    duration += 1

        if rename_statement(self.name, default_name,  file_format) < 0:
            return -1

        return 0

    def wdwait(self, wait_until):
        return WebDriverWait(self.driver, self.delay).until(wait_until)

def get_calendar_clicks(target_date,  start_date):
    # right arrow clicks are positive, left arrow clicks negative

    if target_date.year != start_date.year:
        clicks = 12 * (target_date.year - start_date.year)
    else:
        clicks = 0

    if target_date.month != start_date.month:
        clicks += target_date.month - start_date.month

    return clicks

def clean_download_location(p2p_name, default_name, file_format):
    list = glob.glob('p2p_downloads/{0}.{1}'.format(default_name, file_format))
    if len(list) > 0:
        print('Alte {0} Downloads in ./p2p_downloads entdeckt.'.format(p2p_name))
        choice = None
        while choice != 'a' or choice != 'm':
            choice = input('(A)utomatisch löschen oder (M)anuell entfernen?').lower
        if choice == 'm':
            return -1
        else:
            for file in list:
                os.remove(file)

    return 0

def rename_statement(p2p_name, default_name,  file_format):
    list = glob.glob('p2p_downloads/{0}.{1}'.format(default_name, file_format))
    if len(list) == 1:
        os.rename(list[0], 'p2p_downloads/{0}_statement.{1}'.format(p2p_name.lower(), file_format))
    elif len(list) == 0:
        print('{0} Kontoauszug konnte nicht im Downloadverzeichnis gefunden werden.'.format(p2p_name))
        return -1
    else:
        # this should never happen
        print('Alte {0} Downloads in ./p2p_downloads entdeckt. Bitte zuerst entfernen.'.format(p2p_name))
        return 1

    return 0

def short_month_to_nbr(short_name):
    short_month_to_nbr = {'Jan': '01',  'Feb': '02', 'Mrz': '03', 'Mar': '03', 'Apr': '04', 'Mai': '05', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', \
        'Sep': '09', 'Okt': '10', 'Oct': '10', 'Nov': '11', 'Dez': '12', 'Dec': '12'}
    return short_month_to_nbr[short_name]

def nbr_to_short_month(nbr):
    #Only German locale is used so far
    nbr_to_short_month = {'01': 'Jan', '02': 'Feb', '03': 'Mrz', '04': 'Apr', '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Okt', \
        '11': 'Nov', '12': 'Dez'}
    return nbr_to_short_month[nbr]

def open_selenium_bondora(start_date, end_date):
    bondora = P2P('Bondora', 'https://www.bondora.com/de/login', 'https://www.bondora.com/de/cashflow', 'https://www.bondora.com/de/authorize/logout')

    if bondora.open_start_page(EC.element_to_be_clickable((By.NAME, 'Email'))) < 0:
        return -1

    if bondora.log_into_page(name_field='Email', password_field='Password', \
        wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'Cashflow'))) < 0:
        return -1

    if bondora.open_account_statement_page(title='Cashflow', element_to_check='StartYear') < 0:
        return -1

    #Set start and end date for account statement
    start_year = Select(bondora.driver.find_element_by_id('StartYear')).first_selected_option.text
    start_month = Select(bondora.driver.find_element_by_id('StartMonth')).first_selected_option.text
    end_year = Select(bondora.driver.find_element_by_id('EndYear')).first_selected_option.text
    end_month = Select(bondora.driver.find_element_by_id('EndMonth')).first_selected_option.text

    if start_year != start_date.year:
        select = Select(bondora.driver.find_element_by_id('StartYear'))
        select.select_by_visible_text(str(start_date.year))

    if short_month_to_nbr(start_month) != start_date.strftime('%m'):
        select = Select(bondora.driver.find_element_by_id('StartMonth'))
        select.select_by_visible_text(nbr_to_short_month(start_date.strftime('%m')))

    if end_year != end_date.year:
        select = Select(bondora.driver.find_element_by_id('EndYear'))
        select.select_by_visible_text(str(end_date.year))

    if short_month_to_nbr(end_month) != end_date.strftime('%m'):
        select = Select(bondora.driver.find_element_by_id('EndMonth'))
        select.select_by_visible_text(nbr_to_short_month(end_date.strftime('%m')))

    bondora.driver.find_element_by_xpath('//*[@id="page-content-wrapper"]/div/div/div[1]/form/div[3]/button').click()
    bondora.wdwait(EC.text_to_be_present_in_element((By.XPATH, '/html/body/div[1]/div/div/div/div[3]/div/table/tbody/tr[2]/td[1]/a'), \
    '{0} {1}'.format(start_date.strftime('%b'), start_date.year)))

    #Read cashflow data from webpage and write it to file
    cashflow_table = bondora.driver.find_element_by_id('cashflow-content')
    df = pd.read_html(cashflow_table.get_attribute("innerHTML"),  index_col=0, thousands='.', decimal=',')
    df[0].to_csv('p2p_downloads/bondora_statement.csv')

    #Logout
    bondora.logout_by_url(EC.title_contains('Einloggen'))

    #Close browser window
    bondora.driver.close()

    return 0

def open_selenium_mintos(start_date,  end_date):

    mintos = P2P('Mintos', 'https://www.mintos.com/de/', 'https://www.mintos.com/de/kontoauszug/')

    today = datetime.today()
    default_name = '{0}{1}{2}-account-statement'.format(today.year,  today.strftime('%m'),\
        today.strftime('%d'))
    file_format = 'xlsx'
    if clean_download_location(mintos.name, default_name, file_format) < 0:
        return -1

    if mintos.open_start_page(EC.element_to_be_clickable((By.NAME, 'MyAccountButton'))) < 0:
        return -1

    if mintos.log_into_page(name_field='_username', password_field='_password', \
        wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')),\
        login_field='MyAccountButton',  find_login_by=By.NAME) < 0:
        return -1

    if mintos.open_account_statement_page(title='Account Statement', element_to_check='period-from') < 0:
        return -1

    #Set start and end date for account statement
    if mintos.generate_statement_direct(start_date, end_date, 'period-from', 'period-to', '%d.%m.%Y', \
        wait_until=EC.presence_of_element_located((By.ID, 'export-button')), submit_btn_id='filter-button') < 0:
        return -1

    #Download  account statement
    if mintos.download_statement(default_name,  file_format,  download_btn='export-button', find_btn_by=By.ID) < 0:
        success = -1
    else:
        success = 0

    #Logout
    mintos.logout_by_button("//a[contains(@href,'logout')]",  By.XPATH, EC.title_contains('Vielen Dank'))

    #Close browser window
    mintos.driver.close()

    return success

def open_selenium_robocash(start_date,  end_date):

    robocash = P2P('Robocash', 'https://robo.cash/de', 'https://robo.cash/de/cabinet/statement', \
    'https://robo.cash/de/logout')

    if robocash.open_start_page(EC.presence_of_element_located((By.XPATH, '/html/body/header/div/div/div[3]/a[1]')),\
        'Robo.cash') < 0:
        return -1

    if robocash.log_into_page(name_field='email', password_field='password',\
        wait_until=EC.element_to_be_clickable((By.XPATH, '/html/body/header/div/div/div[2]/nav/ul/li[3]/a')),\
        login_field='/html/body/header/div/div/div[3]/a[1]') < 0:
        return -1

    if robocash.open_account_statement_page(title='Kontoauszug', element_to_check='new_statement') < 0:
        return -1

    # Create account statement for given date range
    try:
        robocash.driver.find_element_by_id('new_statement').click()
    except NoSuchElementException:
        print('Generierung des Robocash Kontoauszugs konnte nicht gestartet werden.')
        return -1

    if robocash.generate_statement_direct(start_date, end_date, 'date-after', 'date-before', '%Y-%m-%d') < 0:
        return -1

    # Robocash does not show download button after statement generation is done without reload
    present = False
    wait = 0
    while not present:
        try:
            robocash.driver.get(robocash.statement_url)
            robocash.wdwait(EC.element_to_be_clickable((By.ID, 'download_statement')))
            present = True
        except TimeoutException:
            wait += 1
            if wait > 10: # roughly 10*delay=30 seconds
                print('Generierung des Robocash Kontoauszugs abgebrochen.')
                return -1

            print('Generierung des Robocash Kontoauszugs noch in Arbeit...')

    #Download account statement
    download_url = robocash.driver.find_element_by_id('download_statement').get_attribute('href')
    driver_cookies = robocash.driver.get_cookies()
    cookies_copy = {}
    for driver_cookie in driver_cookies:
        cookies_copy[driver_cookie["name"]] = driver_cookie["value"]
    r = requests.get(download_url, cookies = cookies_copy)
    with open('p2p_downloads/robocash_statement.xls', 'wb') as output:
        output.write(r.content)

    #Logout
    robocash.logout_by_url(EC.title_contains('Willkommen'))

    #Close browser window
    robocash.driver.close()

    return 0

def open_selenium_swaper(start_date,  end_date):

    swaper = P2P('Swaper', 'https://www.swaper.com/#/dashboard', \
        'https://www.swaper.com/#/overview/account-statement')

    default_name = 'excel-storage*'
    file_format = 'xlsx'
    if clean_download_location(swaper.name, default_name, file_format) < 0:
        return -1

    if swaper.open_start_page(EC.presence_of_element_located((By.NAME, 'email'))) < 0:
        return -1

    if swaper.log_into_page('email', 'password', EC.presence_of_element_located((By.ID, 'open-investments')), \
        fill_delay=0.5) < 0:
        return -1

    if swaper.open_account_statement_page(title='Swaper', element_to_check='account-statement') < 0:
        return -1

    # Create account statement for given date range
    calendar_id_by = 'class'
    calendar_id = 'datepicker-container'
    arrows = ['icon icon icon-left', 'icon icon icon-right',  'div']
    days_table = ['', 'id', ' ',  True]
    default_dates = [datetime.today().replace(day=1),  datetime.now()]

    if swaper.generate_statement_calendar(start_date, end_date,  default_dates, arrows, days_table, \
        calendar_id_by,  calendar_id) < 0:
        return -1

    #Download account statement
    if swaper.download_statement(default_name, file_format,\
        download_btn='//*[@id="account-statement"]/div[3]/div[4]/div/div[1]/a/div[1]/div/span[2]', find_btn_by=By.XPATH) < 0:
        success = -1
    else:
        success = 0

    #Logout
    swaper.logout_by_button('//*[@id="logout"]/span[1]/span', By.XPATH, EC.presence_of_element_located((By.ID, 'about')))

    #Close browser window
    swaper.driver.close()

    return success

def open_selenium_peerberry(start_date,  end_date):

    peerberry = P2P('PeerBerry', 'https://peerberry.com/de/login', 'https://peerberry.com/de/statement')

    default_name = 'transactions'
    file_format = 'csv'
    if clean_download_location(peerberry.name, default_name, file_format) < 0:
        return -1

    if peerberry.open_start_page(EC.element_to_be_clickable((By.NAME, 'email')), 'PeerBerry.com') < 0:
        return -1

    if peerberry.log_into_page('email', 'password', EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug'))) < 0:
        return -1

    if peerberry.open_account_statement_page('Kontoauszug', 'startDate', check_by=By.NAME) < 0:
        return -1

    # Close the cookie policy, if present
    try:
        peerberry.driver.find_element_by_xpath('//*[@id="app"]/div/div/div/div[4]/div/div/div[1]').click()
    except NoSuchElementException:
        pass

    # Create account statement for given date range
    default_dates = [datetime.now(),  datetime.now()]
    arrows = ['rdtPrev', 'rdtNext', 'th']
    calendar_id_by = 'name'
    calendar_id = ['startDate',  'endDate']
    days_table = ['rdtDays', 'class', 'rdtDay', False]

    if peerberry.generate_statement_calendar(start_date, end_date,  default_dates, arrows, days_table, \
        calendar_id_by, calendar_id) < 0:
        return -1

    # Generate account statement
    try:
        peerberry.driver.find_element_by_xpath('/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[1]/div/div[2]/div/div[2]/div/span').click()
        peerberry.wdwait(EC.text_to_be_present_in_element(((By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[2]/div/div/div[1]')), \
            'Eröffnungssaldo '+str(start_date).format('%Y-%m-%d')))
    except (NoSuchElementException,  TimeoutException):
        print('Die Generierung des Peerberry-Kontoauszugs konnte nicht gestartet werden.')
        return -1

    #Download  account statement
    if peerberry.download_statement(default_name, file_format,\
        download_btn='//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div', find_btn_by=By.XPATH, \
        actions='move_to_element') < 0:
        success = -1
    else:
        success = 0

    #Logout
    peerberry.logout_by_button('//*[@id="app"]/div/div/div/div[1]/div[1]/div/div/div[2]/div', By.XPATH, \
        EC.title_contains('Einloggen'))

    #Close browser window
    peerberry.driver.close()

    return success

def open_selenium_estateguru(start_date,  end_date):

    estateguru = P2P('Estateguru', 'https://estateguru.co/portal/login/auth?lang=de', \
        'https://estateguru.co/portal/portfolio/account', 'https://estateguru.co/portal/logout/index')

    if estateguru.open_start_page(EC.element_to_be_clickable((By.NAME, 'username')), 'Sign in/Register') < 0:
        return -1

    if estateguru.log_into_page('username', 'password', EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND'))) < 0:
        return -1

    if estateguru.open_account_statement_page('Übersicht',\
        element_to_check='/html/body/section/div/div/div/div[2]/section[1]/div/div/div[2]/div/form/div[2]/ul/li[5]/a',\
        check_by=By.XPATH) < 0:
        return -1

    #Estateguru currently doesn't offer functionality for downloading cashflow statements.
    #Therefore they have to be read directly from the webpage after applying the filter
    #Since the filter functionality is not really convenient currently (it takes time and the site needs to be reloaded)
    #we just import the default table, which shows all cashflows ever generated for this account

    #Read cashflow data from webpage
    cashflow_table = estateguru.driver.find_element_by_xpath('//*[@id="divTransactionList"]/div')
    df = pd.read_html(cashflow_table.get_attribute("innerHTML"),  index_col=0, thousands='.', decimal=',')

    #Export data to file
    df[0].to_csv('p2p_downloads/estateguru_statement.csv')

    #Logout
    estateguru.logout_by_url(EC.title_contains('Einloggen/Registrieren'))

    #Close browser window
    estateguru.driver.close()

    return 0

def open_selenium_iuvo(start_date,  end_date):

    iuvo = P2P('Iuvo', 'https://www.iuvo-group.com/de/login/', \
        'https://www.iuvo-group.com/de/account-statement/')

    if iuvo.open_start_page(EC.element_to_be_clickable((By.NAME, 'login'))) < 0:
        return -1

    if iuvo.log_into_page('login', 'password', EC.element_to_be_clickable((By.ID, 'p2p_btn_deposit_page_add_funds'))) < 0:
        return -1

    # Click away cookie policy, if present
    try:
        iuvo.driver.find_element_by_id('CybotCookiebotDialogBodyButtonAccept').click()
        print('Iuvo: Cookies wurden akzeptiert')
    except NoSuchElementException:
        pass

    if iuvo.open_account_statement_page('Kontoauszug', 'date_from') < 0:
        return -1

    #Since Dec 2018 Iuvo only provides aggregated cashflows for the whole requested date range, no more detailed information
    #Workaround to get monthly data: create account statement for each month in date range

    #Get all required monthly date ranges
    months = []
    m = start_date
    while m < end_date:
        months.append([date(m.year, m.month, 1), date(m.year, m.month, calendar.monthrange(m.year, m.month)[1])])
        m = m + timedelta(days=31)

    df_result = None
    for month in months:
        start_balance = iuvo.driver.find_element_by_xpath('/html/body/div[5]/main/div/div/div/div[4]/div/table/thead/tr[1]/td[2]/strong').text
        # Create account statement for given date range
        if iuvo.generate_statement_direct(month[0], month[1], 'date_from', 'date_to', '%Y-%m-%d', \
            EC.text_to_be_present_in_element((By.XPATH, '/html/body/div[5]/main/div/div/div/div[4]/div/table/thead/tr[1]/td[1]/strong'),\
            'Anfangsbestand'), submit_btn_id='account_statement_filters_btn') < 0:
            return -1

        #Read statement from page
        new_start_balance = iuvo.driver.find_element_by_xpath('/html/body/div[5]/main/div/div/div/div[4]/div/table/thead/tr[1]/td[2]/strong').text
        if new_start_balance == start_balance: # if the start balance didn't change, the calculation is most likely not finished yet
            time.sleep(3) #TODO: find better way for waiting until new statement is generated
        statement_table = iuvo.driver.find_element_by_class_name('table-responsive')
        df = pd.read_html(statement_table.get_attribute("innerHTML"), index_col=0)[0]
        df = df.T
        df['Datum'] = month[0].strftime('%d.%m.%Y')

        if df_result is None:
            df_result = df
        else:
            df_result = df_result.append(df, sort=True)

    df_result.to_csv('p2p_downloads/iuvo_statement.csv')

    #Logout
    iuvo.logout_by_button('p2p_logout', By.ID, EC.title_contains('Investieren Sie in Kredite'),\
        hover_elem='User name', hover_elem_by=By.LINK_TEXT)

    #Close browser window
    iuvo.driver.close()

    return 0

def open_selenium_grupeer(start_date,  end_date):

    grupeer = P2P('Grupeer', 'https://www.grupeer.com/de/login', 'https://www.grupeer.com/de/account-statement')

    default_name = 'Account statement'
    file_format = 'xlsx'
    if clean_download_location(grupeer.name, default_name, file_format) < 0:
        return -1

    if grupeer.open_start_page(EC.element_to_be_clickable((By.NAME, 'email'))) < 0:
        return -1

    if grupeer.log_into_page('email', 'password', EC.element_to_be_clickable((By.LINK_TEXT, 'Meine Investments'))) < 0:
        return -1

    if grupeer.open_account_statement_page('Account Statement', 'from') < 0:
        return -1

    # Create account statement for given date range
    if grupeer.generate_statement_direct(start_date, end_date, 'from', 'to', '%d.%m.%Y', \
        EC.text_to_be_present_in_element((By.CLASS_NAME, 'balance-block'), 'Bilanz geöffnet am '+str(start_date.strftime('%d.%m.%Y'))), \
        submit_btn_name='submit') < 0:
        return -1

    #Download account statement
    if grupeer.download_statement(default_name, file_format, download_btn='excel', find_btn_by=By.NAME) < 0:
        success = -1
    else:
        success = 0

    #Logout
    grupeer.logout_by_button('Ausloggen', By.LINK_TEXT, EC.title_contains('P2P Investitionsplattform Grupeer'),\
        '/html/body/div[4]/header/div/div/div[2]/div[1]/div/div/ul/li/a/span', By.XPATH)

    #Close browser window
    grupeer.driver.close()

    return success

def open_selenium_dofinance(start_date,  end_date):

    dofinance = P2P('DoFinance', 'https://www.dofinance.eu/de/users/login', \
        'https://www.dofinance.eu/de/users/statement', 'https://www.dofinance.eu/de/users/logout')

    default_name = 'Statement_{0} 00_00_00-{1} 23_59_59'.format(start_date.strftime('%Y-%m-%d'),\
        end_date.strftime('%Y-%m-%d'))
    file_format = 'xlsx'
    if clean_download_location(dofinance.name, default_name, file_format) < 0:
        return -1

    if dofinance.open_start_page(EC.element_to_be_clickable((By.NAME, 'email')), title_check='Anmeldung') < 0:
        return -1

    if dofinance.log_into_page('email', 'password', EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN'))) < 0:
        return -1

    if dofinance.open_account_statement_page('Transaktionen', 'date-from') < 0:
        return -1

    # Create account statement for given date range
    if dofinance.generate_statement_direct(start_date, end_date, 'date-from', 'date-to', '%d.%m.%Y', \
        EC.text_to_be_present_in_element((By.XPATH, '/html/body/section[1]/div/div/div[2]/div[1]/div[4]/div[1]'),\
        'Schlussbilanz '+str(end_date.strftime('%d.%m.%Y'))), submit_btn_name='trans_type') < 0:
        return -1

    #Download account statement
    if dofinance.download_statement(default_name, file_format, download_btn='xls', find_btn_by=By.NAME) < 0:
        success = -1
    else:
        success = 0

    #Logout
    dofinance.logout_by_url(EC.title_contains('Kreditvergabe Plattform'))

    #Close browser window
    dofinance.driver.close()

    return success
