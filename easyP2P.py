import time
from datetime import datetime
import os
import pandas as pd
import p2p_webdriver as wd
import p2p_parser

class P2P:
    def __init__(self,  name=None,  login_url=None, login_name=None, login_pw=None, cashflow_url=None):
        self.name = name
        self.login_url = login_url
        self.cashflow_url = cashflow_url

        self.login_name = login_name
        self.login_pw = login_pw
        
def choose_P2P():
    P2P_platforms = {
        '0': 'Alle', \
        '1': 'Mintos', \
        '2': 'Robocash',\
        '3': 'Swaper', \
        '4': 'PeerBerry', \
        '5': 'Estateguru', \
        '6': 'Iuvo'
    }
    
    print ('Folgende Plattformen sind verfügbar:')
    for k, v in P2P_platforms.items():
        print('{0}: {1}'.format(k, v))
    
    cont = True
    
    while cont:
        platform_set = set(input('Für welche P2P-Plattformen sollen Ergebnisse heruntergeladen werden? '))
        platform_set.discard(',')
        platform_set.discard(' ')
        check_list = platform_set - set(P2P_platforms.keys())
        if len(check_list) > 0:    
            print("Die Plattformen {0} sind nicht verfügbar.".format(list(check_list)))
        else:
            cont = False

    platforms = []
    if '0' in platform_set:
        platforms = list(P2P_platforms.values())
        platforms.remove('Alle')
    else:
        for pl in platform_set:
            platforms.append(P2P_platforms[pl])

    return platforms

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

def show_results(df,  start_date,  end_date):
    
    if df is None:
        print('Keine Ergebnisse vorhanden')
        return -1

    target_columns = ['Investitionen', 'Tilgungszahlungen', 'Zinszahlungen', 'Verzugsgebühren',\
        'Rückkäufe', 'Zinszahlungen aus Rückkäufen']
    show_columns = [col for col in df.columns if col in target_columns]

    df.reset_index(level=['Datum', 'Währung'],  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y')
    df['Monat'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y').dt.to_period('M')

    #Make sure we only show results between start and end date
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    df = df[(df['Datum'] >= start_date) & (df['Datum'] <= end_date)]

    print('Monatsergebnisse für den Zeitraum {0}-{1} pro Plattform:\n'.format(start_date.strftime('%d.%m.%Y'),\
        end_date.strftime('%d.%m.%Y')))
    month_pivot_table = pd.pivot_table(df, values=show_columns,  index=['Plattform',  'Währung', 'Monat'],  aggfunc=sum)
    print(month_pivot_table)
    
    print('Gesamtergebnis für den Zeitraum {0}-{1} pro Plattform:\n'.format(start_date.strftime('%d.%m.%Y'),\
        end_date.strftime('%d.%m.%Y')))
    print(pd.pivot_table(df, values=show_columns,  index=['Plattform',  'Währung'],  aggfunc=sum))
        
    return 0

if __name__=="__main__":

    p2p_choice = choose_P2P()

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
    
    for platform in p2p_choice:
        try:
            func = getattr(wd, 'open_selenium_'+platform.lower())
        except AttributeError:
            print('Die Funktion zum Öffnen von {0} konnte nicht gefunden werden. Ist p2p_webdriver.py vorhanden?'\
                .format(platform))
        else:
            if func(start_date,  end_date) < 0:
                print('{0} wird nicht im Ergebnis berücksichtigt'.format(platform))
            else:
                try:
                    parser = getattr(p2p_parser, platform.lower())
                except AttributeError:
                    print('Der Parser für {0} konnte nicht gefunden werden. Ist p2p_parser.py vorhanden?'.format(platform))
                else:
                    df = parser()
                    list_of_dfs.append(df)

#    df_mintos = p2p_parser.parse_mintos()
#    list_of_dfs.append(df_mintos)
#    df_robocash = parse_robocash()
#    list_of_dfs.append(df_robocash)
#    df_swaper = parse_swaper()
#    list_of_dfs.append(df_swaper)
    
    df_result = combine_dfs(list_of_dfs)
    show_results(df_result,  start_date,  end_date)

    # Get rid of download directory
