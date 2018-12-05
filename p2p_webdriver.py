import credentials
from datetime import datetime
import glob
import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import time

def init_webdriver():
    #TODO: hide browser windows
    options = webdriver.ChromeOptions()
    dl_location = os.path.join(os.getcwd(), 'p2p_downloads')
    prefs = {"download.default_directory": dl_location}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def open_start_page(driver,  p2p_name, login_url, wait_until, delay, title_check=None):

    #Most platforms use their name in the title, title_check will handle the few cases where they don't
    if title_check==None:
        title_check = p2p_name
    
    try:
        driver.get(login_url)
        WebDriverWait(driver, delay).until(wait_until)
        assert title_check in driver.title
    except AssertionError:
        print('Die {0} Webseite konnte nicht geladen werden.'.format(p2p_name))
        return -1
    
    return 0
    
def log_into_page(driver,  p2p_name,   name_field,  password_field, delay, wait_until, \
    login_field=None, find_login_field='xpath', submit_button=None,  find_submit_button='xpath',  fill_delay=0):

    try:
        getattr(credentials, p2p_name)['username']
        getattr(credentials, p2p_name)['password']
    except AttributeError:
        print('Username/Passwort für {0} sind nicht vorhanden. Bitte manuell zu credentials.py hinzufügen.'\
            .format(p2p_name))
        return -1
    
    try:
        if login_field is not None:
            if find_login_field == 'xpath':
                driver.find_element_by_xpath(login_field).click()
            elif find_login_field == 'name':
                driver.find_element_by_name(login_field).click()
            else:
                print('Unbekannte Suchmethode beim Laden der {0}-Loginseite.'.format(p2p_name))
                return -1
            
        WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.NAME, name_field)))
        elem = driver.find_element_by_name(name_field)
        elem.clear()
        elem.send_keys(getattr(credentials, p2p_name)['username'])
        time.sleep(fill_delay)
        elem = driver.find_element_by_name(password_field)
        elem.clear()
        elem.send_keys(getattr(credentials, p2p_name)['password'])
        elem.send_keys(Keys.RETURN)
        
        if submit_button is not None:
            if find_submit_button == 'xpath':
                driver.find_element_by_xpath(submit_button).click()
            elif find_submit_button == 'name':
                driver.find_element_by_name(submit_button).click()
            else:
                print('Unbekannte Suchmethode beim Senden der {0}-Logindaten.'.format(p2p_name))
                return -1
        
        WebDriverWait(driver, delay).until(wait_until)
    except NoSuchElementException:
        print("{0}-Loginseite konnte leider nicht geladen werden.".format(p2p_name))
        return -1
    except TimeoutException:
        print("{0}-Login war leider nicht erfolgreich. Passwort korrekt?".format(p2p_name))
        return -1

    return 0

def open_account_statement_page(driver,  p2p_name,  cashflow_url,  title,  element_to_check,  delay,  check_by=By.ID):
    try:
        driver.get(cashflow_url)
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((check_by, element_to_check)))
        assert title in driver.title
    except (AssertionError,  TimeoutException):
        print("{0} Kontoauszugsseite konnte nicht geladen werden.".format(p2p_name))
        return -1
    
    return 0

def logout_page(p2p_name, driver, delay, logout_elem,  logout_elem_by, logout_success_title,\
    hover_elem=None, hover_elem_by=None):
    try:
        if hover_elem is not None:
            elem = driver.find_element(hover_elem_by, hover_elem)
            hover = ActionChains(driver).move_to_element(elem)
            hover.perform()
            WebDriverWait(driver, delay).until(EC.element_to_be_clickable((logout_elem_by, logout_elem)))

        driver.find_element(logout_elem_by, logout_elem).click()
        WebDriverWait(driver, delay).until(EC.title_contains(logout_success_title))
    except TimeoutException:
        print('{0}-Logout war nicht erfolgreich!'.format(p2p_name))
        #continue anyway
    
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

def generate_statement_direct(p2p_name, driver, delay, start_date, end_date, start_id, end_id, date_format,\
    wait_until=None, submit_btn_id=None, submit_btn_name=None):
    try:
        date_from = driver.find_element_by_id(start_id)
        date_from.send_keys(Keys.CONTROL + 'a')
        date_from.send_keys(datetime.strftime(start_date, date_format))

        try:
            date_to = driver.find_element_by_id(end_id)
            date_to.send_keys(Keys.CONTROL + 'a')
            date_to.send_keys(datetime.strftime(end_date, date_format))
            date_to.send_keys(Keys.RETURN)
        except StaleElementReferenceException: # some sites refresh the page after a change which leads to this exception
            date_to = driver.find_element_by_id(end_id)
            date_to.send_keys(Keys.CONTROL + 'a')
            date_to.send_keys(datetime.strftime(end_date, date_format))

        if submit_btn_name is not None:
            WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.NAME, submit_btn_name)))
            driver.find_element_by_name(submit_btn_name).click()
        elif submit_btn_id is not None:
            WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.ID, submit_btn_id)))
            time.sleep(1) # Mintos needs some time until the button really works, TODO: find better fix
            driver.find_element_by_id(submit_btn_id).click()

        if wait_until is not None:
            WebDriverWait(driver, delay).until(wait_until)
    except NoSuchElementException:
        print('Generierung des {0} Kontoauszugs konnte nicht gestartet werden.'.format(p2p_name))
        return -1
    except TimeoutException:
        print('Generierung des {0} Kontoauszugs hat zu lange gedauert.'.format(p2p_name))
        return -1

    return 0

def generate_statement_calendar(p2p_name, driver, delay, start_date, end_date,  default_dates, arrows, days_table,\
    calendar_id_by, calendar_id):

    try:
        #identify the two calendars
        if calendar_id_by == 'name':
            start_calendar = driver.find_element_by_name(calendar_id[0])
            end_calendar = driver.find_element_by_name(calendar_id[1])
        elif calendar_id_by == 'class':
            datepicker = driver.find_elements_by_xpath("//div[@class='{0}']".format(calendar_id))
            start_calendar = datepicker[0]
            end_calendar = datepicker[1]
        else: # this should never happen
            print('Keine ID für Kalender übergeben')
            return -1

        # how many clicks on the arrow buttons are necessary?
        start_calendar_clicks = get_calendar_clicks(start_date,  default_dates[0])
        end_calendar_clicks = get_calendar_clicks(end_date,  default_dates[1])

        # identify the arrows for both start and end calendar
        left_arrows = driver.find_elements_by_xpath("//{0}[@class='{1}']".format(arrows[2], arrows[0]))
        right_arrows = driver.find_elements_by_xpath("//{0}[@class='{1}']".format(arrows[2], arrows[1]))

        # set start_date
        start_calendar.click()
        WebDriverWait(driver, delay).until(EC.visibility_of(left_arrows[0]))
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
        all_days = driver.find_elements_by_xpath(start_days_xpath)

        for elem in all_days:
            if current_day_identifier=='':
                if elem.text == str(start_date.day):
                    elem.click()
            else:
                if elem.text == str(start_date.day) and elem.get_attribute('class') == current_day_identifier:
                    elem.click()

        # set end_date
        end_calendar.click()
        WebDriverWait(driver, delay).until(EC.visibility_of(left_arrows[1]))
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
        all_days = driver.find_elements_by_xpath(end_days_xpath)

        for elem in all_days:
            if current_day_identifier=='':
                if elem.text == str(end_date.day):
                    elem.click()
            else:
                if elem.text == str(end_date.day) and elem.get_attribute('class') == current_day_identifier:
                    elem.click()
    except (NoSuchElementException,  TimeoutException):
        print('{0}: Konnte die gewünschten Daten für den Kontoauszug nicht setzen.'.format(p2p_name))
        return -1

    return 0

def download_statement(p2p_name, driver, default_name, file_format, download_btn_id=None,  download_btn_name=None, \
    download_btn_xpath=None, actions = None):
    try:
        if download_btn_id is not None:
            download_button = driver.find_element_by_id(download_btn_id)
        elif download_btn_xpath is not None:
            download_button = driver.find_element_by_xpath(download_btn_xpath)
        elif download_btn_name is not None:
            download_button = driver.find_element_by_name(download_btn_name)
        else: # this should never happen
            print('{0}-Download-Button konnte nicht identifziert werden'.format(p2p_name))
            return -1

        if actions == 'move_to_element':
            action = ActionChains(driver)
            action.move_to_element(download_button).perform()
        download_button.click()
    except NoSuchElementException:
        print('Download des {0} Kontoauszugs konnte nicht gestartet werden.'.format(p2p_name))
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
                print('Download des {0} Kontoauszugs abgebrochen.'.format(p2p_name))
                return -1
            elif duration < 1:
                time.sleep(1)
                duration += 1

    if rename_statement(p2p_name, default_name,  file_format) < 0:
        return -1

    return 0

def open_selenium_bondora():
    # TODO: this function is currently broken and needs to be fixed first
    login_url = "https://www.bondora.com/de/login"
    cashflow_url = "https://www.bondora.com/de/cashflow"
    logout_url = "https://www.bondora.com/de/authorize/logout"

    driver = init_webdriver()
    delay = 3 # seconds
    
    try:
        driver.get(login_url)
        assert "Bondora" in driver.title
    except:
        print("Die Bondora Webseite konnte nicht geladen werden.")
        return -1
    
    #Log in
    elem = driver.find_element_by_name("Email")
    elem.clear()
    elem.send_keys('')
    elem.send_keys(Keys.RETURN)
    
    elem = driver.find_element_by_name("Password")
    elem.clear()
    elem.send_keys('')
    elem.send_keys(Keys.RETURN)

    try:
        # TODO: this needs to fixed
        pass
#        WebDriverWait(driver, delay).until(EC.text_to_be_present_in_element(((By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[2]/div/div/div[1]')), \
#            'Eröffnungssaldo '+str(start_date).format('%Y-%m-%d')))
    except TimeoutException:
        print("Laden der Bondora-Seite hat zu lange gedauert!")
        return -1
    
    #Open cashflow page
    driver.get(cashflow_url)
    try:
        assert "Cashflow" in driver.title
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'th.text-center:nth-child(3)')))
    except:
        print("Cashflow-Übersicht konnte nicht geladen werden. Passwort korrekt?")
        return -1

    #Read cashflow page
    #TODO: make sure that all relevant columns are visible
    try:
        html = driver.page_source
        df = pd.read_html(html,  index_col=0)[1]
        assert len(df.index) > 0
    except:
        print("Cashflow-Tabelle konnte nicht ausgelesen werden.")
        return -3

    #Logout
    driver.get(logout_url)
    try:
        WebDriverWait(driver, delay).until(EC.title_contains('Einloggen'))
        print("Logout erfolgreich!")
    except:
        print("Logout nicht erfolgreich!")
        return -4

    #Browserfenster schließen
    driver.close()
    
    return df

def open_selenium_mintos(start_date,  end_date):

    p2p_name = 'Mintos'
    login_url = "https://www.mintos.com/de/"
    cashflow_url = "https://www.mintos.com/de/kontoauszug/"
    
    today = datetime.today()
    default_name = '{0}{1}{2}-account-statement'.format(today.year,  today.strftime('%m'),\
        today.strftime('%d'))
    file_format = 'xlsx'
    if clean_download_location(p2p_name, default_name, file_format) < 0:
        return -1

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay, \
        wait_until=EC.element_to_be_clickable((By.NAME, 'MyAccountButton'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='_username', password_field='_password', \
        delay=delay, wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')),\
        login_field='MyAccountButton',  find_login_field='name') < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Account Statement',\
        element_to_check='period-from',  delay=delay) < 0:
        return -1

    #Set start and end date for account statement
    if generate_statement_direct(p2p_name, driver, delay, start_date, end_date, start_id='period-from', end_id='period-to',\
        date_format='%d.%m.%Y', wait_until=EC.presence_of_element_located((By.ID, 'export-button')),\
        submit_btn_id='filter-button') < 0:
        return -1
        
    #Download  account statement
    if download_statement(p2p_name, driver, default_name,  file_format,  download_btn_id='export-button') < 0:
        success = -1
    else:
        success = 0

    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem="//a[contains(@href,'logout')]",  logout_elem_by=By.XPATH,\
        logout_success_title='Vielen Dank')

    #Close browser window
    driver.close()

    return success
    
def open_selenium_robocash(start_date,  end_date):

    p2p_name = 'Robocash'
    login_url = "https://robo.cash/de"
    cashflow_url = "https://robo.cash/de/cabinet/statement"
    logout_url = "https://robo.cash/de/logout"
    
    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay, \
        wait_until=EC.presence_of_element_located((By.XPATH, '/html/body/header/div/div/div[3]/a[1]')),\
        title_check='Robo.cash') < 0:
        return -1
    
    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', delay=delay,\
        wait_until=EC.element_to_be_clickable((By.XPATH, '/html/body/header/div/div/div[2]/nav/ul/li[3]/a')),\
        login_field='/html/body/header/div/div/div[3]/a[1]') < 0:
        return -1
    
    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Kontoauszug',\
        element_to_check='new_statement',  delay=delay) < 0:
        return -1

    # Create account statement for given date range
    try:
        driver.find_element_by_id('new_statement').click()
    except NoSuchElementException:
        print('Generierung des Robocash Kontoauszugs konnte nicht gestartet werden.')
        return -1

    if generate_statement_direct(p2p_name, driver, delay, start_date, end_date, start_id='date-after',\
        end_id='date-before', date_format='%Y-%m-%d') < 0:
        return -1

    # Robocash does not show download button after statement generation is done without reload
    present = False
    wait = 0
    while not present:
        try:
            driver.get(cashflow_url)
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'download_statement')))
            present = True
        except TimeoutException:
            wait += 1
            if wait > 10: # roughly 10*delay=30 seconds
                print('Generierung des Robocash Kontoauszugs abgebrochen.')
                return -1
                
            print('Generierung des Robocash Kontoauszugs noch in Arbeit...')

    #Download account statement
    download_url = driver.find_element_by_id('download_statement').get_attribute('href')
    driver_cookies = driver.get_cookies()
    cookies_copy = {}
    for driver_cookie in driver_cookies:
        cookies_copy[driver_cookie["name"]] = driver_cookie["value"]
    r = requests.get(download_url, cookies = cookies_copy)
    with open('p2p_downloads/robocash_statement.xls', 'wb') as output:
        output.write(r.content)
    
    #Logout
    try:
        driver.get(logout_url)
        WebDriverWait(driver, delay).until(EC.title_contains('Willkommen'))
    except TimeoutException:
        print("Robocash-Logout war nicht erfolgreich!")
        #continue anyway

    #Close browser window
    driver.close()
    
    return 0
    
def open_selenium_swaper(start_date,  end_date):

    p2p_name = 'Swaper'
    login_url = 'https://www.swaper.com/#/dashboard'
    cashflow_url = 'https://www.swaper.com/#/overview/account-statement'

    default_name = 'excel-storage*'
    file_format = 'xlsx'
    if clean_download_location(p2p_name, default_name, file_format) < 0:
        return -1

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay, \
        wait_until=EC.presence_of_element_located((By.NAME, 'email'))) < 0:
        return -1

    if log_into_page(driver,  p2p_name, 'email', 'password', delay,\
        EC.presence_of_element_located((By.ID, 'open-investments')), fill_delay=0.5) < 0:
        return -1
    
    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Swaper',\
        element_to_check='account-statement',  delay=delay) < 0:
        return -1

    # Create account statement for given date range
    calendar_id_by = 'class'
    calendar_id = 'datepicker-container'
    arrows = ['icon icon icon-left', 'icon icon icon-right',  'div']
    days_table = ['', 'id', ' ',  True]
    default_dates = [datetime.today().replace(day=1),  datetime.now()]

    if generate_statement_calendar(p2p_name, driver, delay, start_date, end_date,  default_dates, \
        arrows, days_table, calendar_id_by,  calendar_id) < 0:
        return -1

    #Download account statement
    if download_statement(p2p_name, driver, default_name, file_format,\
        download_btn_xpath='//*[@id="account-statement"]/div[3]/div[4]/div/div[1]/a/div[1]/div/span[2]') < 0:
        success = -1
    else:
        success = 0
    
    #Logout
    try:
        driver.find_element_by_xpath('//*[@id="logout"]/span[1]/span').click()
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'about')))
    except (NoSuchElementException,  TimeoutException):
        print("Swaper-Logout war nicht erfolgreich!")
        #continue anyway

    #Close browser window
    driver.close()

    return success

def open_selenium_peerberry(start_date,  end_date):

    p2p_name = 'PeerBerry'
    login_url = 'https://peerberry.com/de/login'
    cashflow_url = 'https://peerberry.com/de/statement'

    default_name = 'transactions'
    file_format = 'csv'
    if clean_download_location(p2p_name, default_name, file_format) < 0:
        return -1

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name+'.com', login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'email'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', delay=delay, \
        wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug'))) < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Kontoauszug',\
        element_to_check='startDate',  delay=delay,  check_by=By.NAME) < 0:
        return -1

    # Close the cookie policy, if present
    try:
        driver.find_element_by_xpath('//*[@id="app"]/div/div/div/div[4]/div/div/div[1]').click()
    except NoSuchElementException:
        pass

    # Create account statement for given date range
    default_dates = [datetime.now(),  datetime.now()]
    arrows = ['rdtPrev', 'rdtNext', 'th']
    calendar_id_by = 'name'
    calendar_id = ['startDate',  'endDate']
    days_table = ['rdtDays', 'class', 'rdtDay', False]

    if generate_statement_calendar(p2p_name, driver, delay, start_date, end_date,  default_dates, \
        arrows, days_table, calendar_id_by, calendar_id) < 0:
        return -1

    # Generate account statement
    try:
        driver.find_element_by_xpath('/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[1]/div/div[2]/div/div[2]/div/span').click()
        WebDriverWait(driver, delay).until(EC.text_to_be_present_in_element(((By.XPATH, '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[2]/div/div/div[1]')), \
            'Eröffnungssaldo '+str(start_date).format('%Y-%m-%d')))
    except (NoSuchElementException,  TimeoutException):
        print('Die Generierung des Peerberry-Kontoauszugs konnte nicht gestartet werden.')
        return -1
    
    #Download  account statement
    if download_statement(p2p_name, driver, default_name, file_format,\
        download_btn_xpath='//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div',\
        actions='move_to_element') < 0:
        success = -1
    else:
        success = 0
    
    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem='//*[@id="app"]/div/div/div/div[1]/div[1]/div/div/div[2]/div',  logout_elem_by=By.XPATH,\
        logout_success_title='Einloggen')

    #Close browser window
    driver.close()

    return success

def open_selenium_estateguru(start_date,  end_date):

    p2p_name = 'Estateguru'
    login_url = 'https://estateguru.co/portal/login/auth?lang=de'
    cashflow_url = 'https://estateguru.co/portal/portfolio/account'
    logout_url = 'https://estateguru.co/portal/logout/index'
    
    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'username')), title_check='Sign in/Register') < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='username', password_field='password', \
        delay=delay, wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND'))) < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Übersicht',\
        element_to_check='/html/body/section/div/div/div/div[2]/section[1]/div/div/div[2]/div/form/div[2]/ul/li[5]/a',\
        delay=delay,  check_by=By.XPATH) < 0:
        return -1

    #Estateguru currently doesn't offer functionality for downloading cashflow statements.
    #Therefore they have to be read directly from the webpage after applying the filter
    #Since the filter functionality is not really convenient currently (it takes time and the site needs to be reloaded)
    #We just import the default table, which shows all cashflows ever generated for this account
    #The filter settings are commented out in case we will need them again in the future
    
#    try:
#        #click filter button
#        driver.find_element_by_xpath('/html/body/section/div/div/div/div[2]/section[2]/div[1]/div[1]/button').click()
#        WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.ID, 'dateApproveFilter')))
#        elem = driver.find_element_by_id('dateApproveFilter')
#        elem.clear()
#        elem.send_keys(datetime.strftime(start_date,'%d.%m.%Y'))
#        elem = driver.find_element_by_id('dateApproveFilterTo')
#        elem.clear()
#        elem.send_keys(datetime.strftime(end_date,'%d.%m.%Y'))
#        elem.send_keys(Keys.RETURN)
#        
#        #click 'Los' button
#        driver.find_element_by_xpath('/html/body/section/div/div/div/div[2]/section[2]/div[1]/div[3]/form/div[6]/div/div[3]/button').click()
#        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '/html/body/section/div/div/div/div[2]/section[2]/div[2]/div/div/table')))
#    except NoSuchElementException:
#        print("Fehler beim Generieren des Estateguru Kontoauszugs!")
#        return -1
#    except TimeoutException:
#        print("Die Generierung des Estateguru Kontoauszugs hat zu lange gedauert...")
#        return -1
    
    #Read cashflow data from webpage
    cashflow_table = driver.find_element_by_xpath('//*[@id="divTransactionList"]/div')
    df = pd.read_html(cashflow_table.get_attribute("innerHTML"),  index_col=0, thousands='.', decimal=',')

    #Export data to file
    df[0].to_csv('p2p_downloads/estateguru_statement.csv')
    
    #Logout
    try:
        driver.get(logout_url)
        WebDriverWait(driver, delay).until(EC.title_contains('Einloggen/Registrieren'))
    except TimeoutException:
        print("Estateguru-Logout war nicht erfolgreich!")
        #continue anyway

    #Close browser window
    driver.close()

    return 0

def open_selenium_iuvo(start_date,  end_date):

    p2p_name = 'Iuvo'
    login_url = 'https://www.iuvo-group.com/de/login/'
    cashflow_url = 'https://www.iuvo-group.com/de/account-statement/'

    default_name = 'AccountStatement*'
    file_format = 'xlsx'
    if clean_download_location(p2p_name, default_name, file_format) < 0:
        return -1

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'login'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='login', password_field='password', \
        delay=delay, wait_until=EC.element_to_be_clickable((By.ID, 'p2p_btn_deposit_page_add_funds'))) < 0:
        return -1

    # Click away cookie policy, if present
    try:
        driver.find_element_by_id('CybotCookiebotDialogBodyButtonAccept').click()
        print('Iuvo: Cookies wurden akzeptiert')
    except NoSuchElementException:
        pass

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Kontoauszug',\
        element_to_check='date_from', delay=delay) < 0:
        return -1

    # Create account statement for given date range
    if generate_statement_direct(p2p_name, driver, delay, start_date, end_date, start_id='date_from', end_id='date_to',\
        date_format='%Y-%m-%d', wait_until=EC.text_to_be_present_in_element((By.XPATH,\
        '//*[@id="p2p_cont"]/div/div[4]/div/table/tbody/tr[1]/td[2]/strong'),\
        'Anfangsbestand '+str(start_date.strftime('%Y-%m-%d')))) < 0:
        return -1

    #Download  account statement
    if download_statement(p2p_name, driver, default_name, file_format,\
        download_btn_xpath='/html/body/div[5]/main/div/div/div/div[3]/div[2]/a') < 0:
        success = -1
    else:
        success = 0

    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem='p2p_logout',  logout_elem_by=By.ID,\
        logout_success_title='Investieren Sie in Kredite',\
        hover_elem='User name', hover_elem_by=By.NAME)

    #Close browser window
    driver.close()

    return success

def open_selenium_grupeer(start_date,  end_date):

    p2p_name = 'Grupeer'
    login_url = 'https://www.grupeer.com/de/login'
    cashflow_url = 'https://www.grupeer.com/de/account-statement'

    default_name = 'Account statement'
    file_format = 'xlsx'
    if clean_download_location(p2p_name, default_name, file_format) < 0:
        return -1

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'email'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', \
        delay=delay, wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'Meine Investments'))) < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url, \
        title='Account Statement', element_to_check='from', delay=delay) < 0:
        return -1

    # Create account statement for given date range
    if generate_statement_direct(p2p_name, driver, delay, start_date, end_date, start_id='from', end_id='to',\
        date_format='%d.%m.%Y', wait_until=EC.text_to_be_present_in_element((By.XPATH,\
        '/html/body/div[4]/div/div[2]/div/div/div[1]/div[2]'),\
        'Bilanz geöffnet am '+str(start_date.strftime('%d.%m.%Y')))) < 0:
        return -1

    #Download account statement
    if download_statement(p2p_name, driver, default_name, file_format,\
        download_btn_name='excel') < 0:
        success = -1
    else:
        success = 0

    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem='Ausloggen',  logout_elem_by=By.LINK_TEXT,\
        logout_success_title='P2P Investitionsplattform Grupeer',\
        hover_elem='/html/body/div[4]/header/div/div/div[2]/div[1]/div/div/ul/li/a/span', hover_elem_by=By.XPATH)

    #Close browser window
    driver.close()

    #Rename downloaded file from generic name
    if rename_statement(p2p_name, 'Account statement', 'xlsx') < 0:
        return -1

    return success

def open_selenium_dofinance(start_date,  end_date):

    p2p_name = 'DoFinance'
    login_url = 'https://www.dofinance.eu/de/users/login'
    cashflow_url = 'https://www.dofinance.eu/de/users/statement'
    logout_url = 'https://www.dofinance.eu/de/users/logout'

    default_name = 'Statement_{0} 00_00_00-{1} 23_59_59'.format(start_date.strftime('%Y-%m-%d'),\
        end_date.strftime('%Y-%m-%d'))
    file_format = 'xlsx'
    if clean_download_location(p2p_name, default_name, file_format) < 0:
        return -1

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'email')), title_check='Anmeldung') < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', \
        delay=delay, wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN'))) < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url, \
        title='Transaktionen', element_to_check='date-from', delay=delay) < 0:
        return -1

    # Create account statement for given date range
    if generate_statement_direct(p2p_name=p2p_name, driver=driver, delay=delay, start_date=start_date, end_date=end_date,\
        start_id='date-from', end_id='date-to', date_format='%d.%m.%Y',\
        wait_until=EC.text_to_be_present_in_element((By.XPATH, '/html/body/section[1]/div/div/div[2]/div[1]/div[4]/div[1]'),\
        'Schlussbilanz '+str(end_date.strftime('%d.%m.%Y'))),  submit_btn_name='trans_type') < 0:
        return -1

    #Download account statement
    if download_statement(p2p_name, driver, default_name, file_format, download_btn_name='xls') < 0:
        success = -1
    else:
        success = 0

    #Logout
    try:
        driver.get(logout_url)
        WebDriverWait(driver, delay).until(EC.title_contains('Kreditvergabe Plattform'))
    except TimeoutException:
        print("{0}-Logout war nicht erfolgreich!".format(p2p_name))
        #continue anyway

    #Close browser window
    driver.close()

    return success
