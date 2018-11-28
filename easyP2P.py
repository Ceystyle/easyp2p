import time
from datetime import datetime
import os
import pandas as pd
import p2p_webdriver as wd
import p2p_parser
from selenium.webdriver.common.keys import Keys

class P2P:
    def __init__(self,  name=None,  login_url=None, login_name=None, login_pw=None, cashflow_url=None):
        self.name = name
        self.login_url = login_url
        self.cashflow_url = cashflow_url

        self.login_name = login_name
        self.login_pw = login_pw
        
def choose_P2P():
    P2P_platforms = {
        "Bondora": "https://www.bondora.com/de/login",  \
        "Mintos": "https://www.mintos.com/de/", 
    }
    
    print ("Folgende Plattformen sind verfügbar:")
    print([p for p in P2P_platforms.keys()])
    
    platform = ""
    while platform not in P2P_platforms.keys():
        platform = input("Für welche P2P-Plattformen sollen Ergebnisse heruntergeladen werden? ")
        
        if platform not in P2P_platforms.keys():
            print("Diese Plattform ist nicht verfügbar.")
        
    return P2P_platforms[platform]

def get_date(date_label):
    cont = True
    while cont:
        try:
            input_date = input('Bitte geben Sie das '+date_label+' an: ')
            date = datetime.strptime(input_date,'%d.%m.%Y')
            cont = False
        except:
            print("Ungültige Angabe. Bitte geben Sie das Datum im Format dd.mm.yyyy ein!")
            
    return date
    
def combine_dfs(list_of_dfs):
    
    df_result = None
    for df in list_of_dfs:
        if df_result is not None:
            df_result = df_result.append(df,  sort=False).fillna(0)
        else:
            df_result = df

    return df_result

def show_results(df):
    
    if df is None:
        print('Keine Ergebnisse vorhanden')
        return -1

    target_columns = ['Investitionen', 'Tilgungszahlungen', 'Zinszahlungen', 'Verzugsgebühren',\
        'Rückkäufe', 'Zinszahlungen aus Rückkäufen']
    show_columns = [col for col in df.columns if col in target_columns]
        
    df.reset_index(level=['Datum', 'Währung'],  inplace=True)

    df['Datum'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y')
    df['Monat'] = df['Datum'].dt.strftime('%b %Y')
    print('Monatsergebnisse für den Zeitraum {0}-{1} pro Plattform:\n'.format(start_date.strftime('%d.%m.%Y'),\
        end_date.strftime('%d.%m.%Y')))
    print(pd.pivot_table(df, values=show_columns,  index=['Plattform',  'Währung', 'Monat'],  aggfunc=sum))    
    
    print('Gesamtergebnis für den Zeitraum {0}-{1} pro Plattform:\n'.format(start_date.strftime('%d.%m.%Y'),\
        end_date.strftime('%d.%m.%Y')))
    print(pd.pivot_table(df, values=show_columns,  index=['Plattform',  'Währung'],  aggfunc=sum))
        
    return 0

if __name__=="__main__":
    #url = choose_P2P()

    # Get start and end dates for statement generation
#    start_date = get_date('Startdatum')
#    end_date = get_date('Enddatum')
    start_date_dt = datetime.strptime('01.09.2018','%d.%m.%Y')
    end_date_dt = datetime.strptime('31.10.2018','%d.%m.%Y')
    start_date = datetime.date(start_date_dt)
    end_date = datetime.date(end_date_dt)
    
    # Check if download directory exists, if not create it
    dl_location = './p2p_downloads'
    if not os.path.isdir(dl_location):
        os.makedirs(dl_location)
    
    #TODO: hide browser windows
    #TODO: read passwords from file
    
    list_of_dfs = []
    
#    df_result = pd.DataFrame(columns=['Datum','Währung', 'Plattform', 'Anfangssaldo '+str(start_date), 'Investitionen',\
#        'Tilgungszahlungen', 'Zinszahlungen', 'Verzugsgebühren', 'Ausfälle', 'Rückkäufe',\
#        'Zinszahlungen aus Rückkäufen', 'Zinszahlungen (gesamt)','Endsaldo '+str(end_date)],  dtype='float64')

    #Bondora (Selenium)
#    open_selenium_bondora()
    #TODO: Fehlerfälle (int-Returns) behandeln
    #df_bondora.to_csv('Bondora_Gesamt.csv')
#    df_bondora = pd.read_csv('Bondora_Gesamt.csv',  index_col=0)
#    parse_bondora(start_date,  end_date,  df_bondora, df_result)
    
    #Mintos
#    if open_selenium_mintos(start_date,  end_date) < 0:
#        print('Mintos wird nicht im Ergebnis berücksichtigt')
#    else:
#        df_mintos = parse_mintos()
#        list_of_dfs.append(df_mintos)
    
    #Robocash
#    if open_selenium_robocash(start_date,  end_date) < 0:
#        print('Robocash wird nicht im Ergebnis berücksichtigt')
#    else:
#        df_robocash = parse_robocash()
#        list_of_dfs.append(df_robocash)
#
#    #Swaper
#    if open_selenium_swaper(start_date,  end_date) < 0:
#        print('Swaper wird nicht im Ergebnis berücksichtigt')
#    else:
#        df_swaper = parse_swaper()
#        list_of_dfs.append(df_swaper)
#
#    #Peerberry
#    if wd.open_selenium_peerberry(start_date,  end_date) < 0:
#        print('Peerberry wird nicht im Ergebnis berücksichtigt')
#    else:
#        df_peerberry = p2p_parser.peerberry()
#        list_of_dfs.append(df_peerberry)

    wd.open_selenium_peerberry(start_date,  end_date) 

#    df_mintos = p2p_parser.parse_mintos()
#    list_of_dfs.append(df_mintos)
#    df_robocash = parse_robocash()
#    list_of_dfs.append(df_robocash)
#    df_swaper = parse_swaper()
#    list_of_dfs.append(df_swaper)
    
    df_result = combine_dfs(list_of_dfs)
    show_results(df_result)

    # Get rid of download directory
