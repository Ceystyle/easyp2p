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
    
def log_into_page(driver,  p2p_name,   name_field,  password_field, element_to_check, delay,\
    check_method=EC.presence_of_element_located,  check_by=By.XPATH,\
    login_field=None, find_login_field='xpath',\
    submit_button=None,  find_submit_button='xpath',  fill_delay=0):

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
        
        WebDriverWait(driver, delay).until(check_method((check_by,\
            element_to_check)))
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

def rename_statement(p2p_name, default_name,  file_format,  print_status=True):
    list = glob.glob('p2p_downloads/{0}.{1}'.format(default_name, file_format))
    if len(list) == 1:
        os.rename(list[0], 'p2p_downloads/{0}_statement.{1}'.format(p2p_name.lower(), file_format))
    elif len(list) == 0:
        if print_status==True:
            print('{0} Kontoauszug konnte nicht im Downloadverzeichnis gefunden werden.'.format(p2p_name))
        return -1
    else:
        # TODO: instead of bailing out, sort by date and rename newest download file
        if print_status==True:
            print('Alte {0} Downloads in ./p2p_downloads entdeckt. Bitte zuerst entfernen.'.format(p2p_name))
        return 1

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
    
    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay, \
        wait_until=EC.element_to_be_clickable((By.NAME, 'MyAccountButton'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='_username', password_field='_password', \
        element_to_check='Kontoauszug',  delay=delay, check_by=By.LINK_TEXT,\
        login_field='MyAccountButton',  find_login_field='name') < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Account Statement',\
        element_to_check='period-from',  delay=delay) < 0:
        return -1

    #Set start and end date for account statement
    try:
        elem = driver.find_element_by_id("period-from")
        elem.clear()
        elem.send_keys(datetime.strftime(start_date,'%d.%m.%Y'))
        elem = driver.find_element_by_id("period-to")
        elem.clear()
        elem.send_keys(datetime.strftime(end_date,'%d.%m.%Y'))
        
        #Select all payment types
        driver.find_element_by_xpath('//*[@id="sel-booking-types"]/div').click()
        driver.find_element_by_xpath('//*[@id="sel-booking-types"]/div/ul/li[1]/a').click()
        
        driver.find_element_by_id('filter-button').click()
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'export-button')))
    except NoSuchElementException:
        print("Fehler beim Generieren des Mintos Kontoauszugs!")
        return -1
    except TimeoutException:
        print("Die Generierung des Mintos Kontoauszugs hat zu lange gedauert...")
        return -1
        
    #Download  account statement
    driver.find_element_by_id('export-button').click()

    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem="//a[contains(@href,'logout')]",  logout_elem_by=By.XPATH,\
        logout_success_title='Vielen Dank')

    #Close browser window
    driver.close()

    #Rename downloaded file from generic YYYYMMDD-account-statement.xlsx
    today = datetime.today()
    default_name = '{0}{1}{2}-account-statement'.format(today.year,  today.strftime('%m'),\
        today.strftime('%d'))
    if rename_statement(p2p_name, default_name, 'xlsx') < 0:
        return -1

    return 0
    
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
    
    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', \
        element_to_check='/html/body/header/div/div/div[2]/nav/ul/li[3]/a',  delay=delay, \
        login_field='/html/body/header/div/div/div[3]/a[1]') < 0:
        return -1
    
    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Kontoauszug',\
        element_to_check='new_statement',  delay=delay) < 0:
        return -1

    # Create account statement for given date range
    try:
        driver.find_element_by_id('new_statement').click()
        date_after = driver.find_element_by_id('date-after')
        date_after.clear()
        date_after.send_keys(datetime.strftime(start_date,'%Y-%m-%d'))
        date_before = driver.find_element_by_id('date-before')
        date_before.clear()
        date_before.send_keys(datetime.strftime(end_date,'%Y-%m-%d'))
        date_before.send_keys(Keys.RETURN)
    except NoSuchElementException:
        print('Generierung des Robocash Kontoauszugs konnte nicht gestartet werden.')
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
    
    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay, \
        wait_until=EC.presence_of_element_located((By.NAME, 'email'))) < 0:
        return -1
    
    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', \
        element_to_check='open-investments', delay=delay,  check_method=EC.presence_of_element_located, \
        check_by = By.ID,  fill_delay=0.5) < 0:
        return -1
    
    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url,  title='Swaper',\
        element_to_check='account-statement',  delay=delay) < 0:
        return -1

    # Create account statement for given date range
    # Swaper does not allow direct input of the two dates, they need to be selected in the pop-up calendars
    # Furthermore, the id of the two datepickers is generated dynamically
    try:
        # find the two datepicker fields
        datepicker = driver.find_elements_by_xpath("//div[@class='datepicker-container']")
        from_date = datepicker[0]
        to_date = datepicker[1]
        
        # get the pre-filled default values in order to identify how often months need to be changed
        default_dates = driver.find_elements_by_xpath("//input[@type='text']")
        default_start_date = datetime.strptime(default_dates[0].get_attribute('value'),  '%Y-%m-%d')
        default_end_date = datetime.strptime(default_dates[1].get_attribute('value'),  '%Y-%m-%d')
        
        # how many clicks on the arrow buttons are necessary?
        left_calendar_clicks = get_calendar_clicks(start_date,  default_start_date)
        right_calendar_clicks = get_calendar_clicks(end_date,  default_end_date)
        
        # identify the arrows for both left and right calendar
        calendar_left_arrows = driver.find_elements_by_xpath("//div[@class='icon icon icon-left']")
        calendar_right_arrows = driver.find_elements_by_xpath("//div[@class='icon icon icon-right']")
        left_calendar_left_arrow = calendar_left_arrows[0]
        left_calendar_right_arrow = calendar_right_arrows[0]
        right_calendar_left_arrow = calendar_left_arrows[1]
        right_calendar_right_arrow = calendar_right_arrows[1]
        
        # set start_date
        from_date.click()
        if left_calendar_clicks < 0:
            for i in range(0, abs(left_calendar_clicks)):
                left_calendar_left_arrow.click()
        elif left_calendar_clicks > 0:
            for i in range(0, left_calendar_clicks):
                left_calendar_right_arrow.click()
                
        driver.find_elements_by_xpath("//span[text()={0}]".format(start_date.day))[0].click()
        
        # set end_date
        to_date.click()
        if right_calendar_clicks < 0:
            for i in range(0, abs(right_calendar_clicks)):
                right_calendar_left_arrow.click()
        elif right_calendar_clicks > 0:
            for i in range(0, right_calendar_clicks):
                right_calendar_right_arrow.click()
                
        driver.find_elements_by_xpath("//span[text()={0}]".format(end_date.day))[1].click()
    except NoSuchElementException:
        print('Konnte die gewünschten Daten für den Kontoauszug nicht setzen.')
        return -1
    
    #Download account statement
    try:
        download_button = driver.find_element_by_xpath('//*[@id="account-statement"]/div[3]/div[4]/div/div[1]/a/div[1]/div/span[2]')
        WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH,\
            '//*[@id="account-statement"]/div[3]/div[4]/div/div[1]/a/div[1]/div/span[2]')))
        download_button.click()

        #Wait max. 5 seconds until download has finished
        count = 0
        while rename_statement(p2p_name, 'excel-storage*', 'xlsx', print_status=False) < 0 or count > 5:
            time.sleep(1)
            count += 1

        if count > 5:
            raise TimeoutException
    except NoSuchElementException:
        print('Download des Swaper Kontoauszugs konnte nicht gestartet werden.')
        return -1
    except TimeoutException:
        print('Download des Swaper Kontoauszugs war nicht erfolgreich.')
        return -1
    
    #Logout
    try:
        driver.find_element_by_xpath('//*[@id="logout"]/span[1]/span').click()
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'about')))
    except (NoSuchElementException,  TimeoutException):
        print("Swaper-Logout war nicht erfolgreich!")
        #continue anyway

    #Close browser window
    driver.close()

    return 0

def open_selenium_peerberry(start_date,  end_date):

    p2p_name = 'PeerBerry'
    login_url = 'https://peerberry.com/de/login'
    cashflow_url = 'https://peerberry.com/de/statement'
    
    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name+'.com', login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'email'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', \
        #user_name='nsandschn@gmx.de',  password='PeerNick2018',\
        element_to_check='Kontoauszug',  delay=delay, check_by=By.LINK_TEXT) < 0:
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
    # Peerberry does not allow direct input of the two dates, they need to be selected in the pop-up calendars
    try:
        # how many clicks on the arrow buttons are necessary? They open on the current month
        left_calendar_clicks = get_calendar_clicks(start_date,  datetime.now())
        right_calendar_clicks = get_calendar_clicks(end_date,  datetime.now())
        
        # identify the arrows for both left and right calendar
        # the two left arrows will be used to check if the page has loaded already
        left_calendar_left_arrow_xpath = '//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/div[1]/div/div/div/table/thead/tr[1]/th[1]/span'
        right_calendar_left_arrow_xpath = '//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/div[2]/div/div/div/table/thead/tr[1]/th[1]/span'
        left_calendar_left_arrow = driver.find_element_by_xpath(left_calendar_left_arrow_xpath)
        left_calendar_right_arrow = driver.find_element_by_xpath('//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/div[1]/div/div/div/table/thead/tr[1]/th[3]/span')
        right_calendar_left_arrow = driver.find_element_by_xpath(right_calendar_left_arrow_xpath)
        right_calendar_right_arrow = driver.find_element_by_xpath('//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/div[2]/div/div/div/table/thead/tr[1]/th[3]/span')
        
        # set start_date
        driver.find_element_by_name("startDate").click()
        WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, left_calendar_left_arrow_xpath)))
        if left_calendar_clicks < 0:
            for i in range(0, abs(left_calendar_clicks)):
                left_calendar_left_arrow.click()
        elif left_calendar_clicks > 0:
            for i in range(0, left_calendar_clicks):
                left_calendar_right_arrow.click()
                
        # get all dates from left calendar and find the start day
        all_dates = driver.find_elements_by_xpath('//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/div[1]/div/div/div/table//td')
        
        for elem in all_dates:
            if elem.text == str(start_date.day) and elem.get_attribute('class') == 'rdtDay':
                elem.click()
        
        # set end_date
        driver.find_element_by_name("endDate").click()
        WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, right_calendar_left_arrow_xpath)))
        if right_calendar_clicks < 0:
            for i in range(0, abs(right_calendar_clicks)):
                right_calendar_left_arrow.click()
        elif right_calendar_clicks > 0:
            for i in range(0, right_calendar_clicks):
                right_calendar_right_arrow.click()
    
        # get all dates from right calendar and find the end day
        all_dates = driver.find_elements_by_xpath('//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div[1]/div/div[2]/div/div/div/table//td')
        
        for elem in all_dates:
            if elem.text == str(end_date.day) and elem.get_attribute('class') == 'rdtDay':
                elem.click()
            
    except (NoSuchElementException,  TimeoutException):
        print('Peerberry: Konnte die gewünschten Daten für den Kontoauszug nicht setzen.')
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
    try:
        download_button = driver.find_element_by_xpath('//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div')
        actions = ActionChains(driver)
        actions.move_to_element(download_button).perform()
        download_button.click()
    except NoSuchElementException:
        print('Der Peerberry Kontoauszug konnte nicht heruntergeladen werden')
        return -1
    
    #It usually takes several seconds until the download actually starts
    #TODO: make sure that download finished before closing the window
#    peerberry_window = driver.window_handles[0]
#    driver.execute_script('window.open();')
#    download_window = driver.window_handles[1]
#    driver.switch_to.window(download_window)
#    for count in range(0, 10):
#        try:
#            time.sleep(2)
#            driver.get('chrome://downloads/')
#            print(driver.find_elements_by_id('content'))
#        except NoSuchElementException:
#            print('Download läuft noch')
#    driver.switch_to.window(peerberry_window)
    time.sleep(10)
    
    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem='//*[@id="app"]/div/div/div/div[1]/div[1]/div/div/div[2]/div',  logout_elem_by=By.XPATH,\
        logout_success_title='Einloggen')

    #Close browser window
    driver.close()

    #Rename downloaded file from generic transactions.csv
    if rename_statement(p2p_name, 'transactions', 'csv') < 0:
        return -1

    return 0

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
        element_to_check='KONTOSTAND',  delay=delay, check_by=By.LINK_TEXT) < 0:
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

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'login'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='login', password_field='password', \
        element_to_check='p2p_btn_deposit_page_add_funds',  delay=delay, check_by=By.ID) < 0:
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
    try:
        date_from = driver.find_element_by_id('date_from')
        date_from.clear()
        date_from.send_keys(datetime.strftime(start_date,'%Y-%m-%d'))
        date_to = driver.find_element_by_id('date_to')
        date_to.clear()
        date_to.send_keys(datetime.strftime(end_date,'%Y-%m-%d'))
        driver.find_element_by_id('account_statement_filters_btn').click()
        WebDriverWait(driver, delay).until(EC.text_to_be_present_in_element((By.XPATH,\
            '//*[@id="p2p_cont"]/div/div[4]/div/table/tbody/tr[1]/td[2]/strong'),\
            'Anfangsbestand '+str(start_date.strftime('%Y-%m-%d'))))
    except NoSuchElementException:
        print('Generierung des Iuvo Kontoauszugs konnte nicht gestartet werden.')
        return -1
    except TimeoutException:
        print('Generierung des Iuvo Kontoauszugs hat zu lange gedauert.')
        return -1

    #Download account statement
    try:
        driver.find_element_by_xpath('/html/body/div[5]/main/div/div/div/div[3]/div[2]/a').click()
    except NoSuchElementException:
        print('Download des Iuvo Kontoauszugs konnte nicht gestartet werden.')
        return -1

    #Logout
    logout_page(p2p_name=p2p_name, driver=driver, delay=delay,\
        logout_elem='p2p_logout',  logout_elem_by=By.ID,\
        logout_success_title='Investieren Sie in Kredite',\
        hover_elem='User name', hover_elem_by=By.NAME)

    #Close browser window
    driver.close()

    #Rename downloaded file from generic name
    if rename_statement(p2p_name, 'AccountStatement*', 'xlsx') < 0:
        return -1

    return 0

def open_selenium_grupeer(start_date,  end_date):

    p2p_name = 'Grupeer'
    login_url = 'https://www.grupeer.com/de/login'
    cashflow_url = 'https://www.grupeer.com/de/account-statement'

    driver = init_webdriver()
    delay = 3 # seconds

    if open_start_page(driver=driver,  p2p_name=p2p_name, login_url=login_url, delay=delay,\
        wait_until=EC.element_to_be_clickable((By.NAME, 'email'))) < 0:
        return -1

    if log_into_page(driver=driver,  p2p_name=p2p_name, name_field='email', password_field='password', \
        element_to_check='Meine Investments',  delay=delay, check_by=By.LINK_TEXT) < 0:
        return -1

    if open_account_statement_page(driver=driver,  p2p_name=p2p_name,  cashflow_url=cashflow_url, \
        title='Account Statement', element_to_check='from', delay=delay) < 0:
        return -1

    # Create account statement for given date range
    try:
        date_from = driver.find_element_by_id('from')
        date_from.clear()
        date_from.send_keys(datetime.strftime(start_date,'%d.%m.%Y'))
        date_to = driver.find_element_by_id('to')
        date_to.clear()
        date_to.send_keys(datetime.strftime(end_date,'%d.%m.%Y'))
        driver.find_element_by_name('submit').click()
        WebDriverWait(driver, delay).until(EC.text_to_be_present_in_element((By.XPATH,\
            '/html/body/div[4]/div/div[2]/div/div/div[1]/div[2]'),\
            'Bilanz geöffnet am '+str(start_date.strftime('%d.%m.%Y'))))
    except NoSuchElementException:
        print('Generierung des Grupeer Kontoauszugs konnte nicht gestartet werden.')
        return -1
    except TimeoutException:
        print('Generierung des Grupeer Kontoauszugs hat zu lange gedauert.')
        return -1

    #Download account statement
    try:
        driver.find_element_by_name('excel').click()
    except NoSuchElementException:
        print('Download des Grupeer Kontoauszugs konnte nicht gestartet werden.')
        return -1

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

    return 0
