from datetime import datetime
import os
import p2p_parser
import p2p_results
import p2p_webdriver as wd
import sys

def choose_P2P():
    P2P_platforms = {
        '0': 'Alle', \
        '1': 'Mintos', \
        '2': 'Robocash',\
        '3': 'Swaper', \
        '4': 'PeerBerry', \
        '5': 'Estateguru', \
        '6': 'Iuvo', \
        '7': 'Grupeer', \
        '8': 'DoFinance', \
        '9': 'Bondora'
    }
    
    print ('Folgende Plattformen sind verfügbar:')
    for k, v in P2P_platforms.items():
        print('{0}: {1}'.format(k, v))
    
    cont = True
    
    while cont:
        try:
            platform_set = set(input('Für welche P2P-Plattformen sollen Ergebnisse heruntergeladen werden? '))
            platform_set.discard(',')
            platform_set.discard(' ')
            check_list = platform_set - set(P2P_platforms.keys())
            if len(check_list) > 0:
                print("Die Plattformen {0} sind nicht verfügbar.".format(list(check_list)))
            else:
                cont = False
        except KeyboardInterrupt:
            print('\n')
            sys.exit()

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
            target_date = datetime.strptime(input_date,'%d.%m.%Y').date()
            cont = False
        except ValueError:
            print("Ungültige Angabe. Bitte geben Sie das Datum im Format dd.mm.yyyy ein!")
            
    return target_date

if __name__=="__main__":

    p2p_choice = choose_P2P()

    # Get start and end dates for statement generation
    start_date = get_date('Startdatum')
    end_date = get_date('Enddatum')

    # Check if download directory exists, if not create it
    dl_location = './p2p_downloads'
    if not os.path.isdir(dl_location):
        os.makedirs(dl_location)

    list_of_dfs = []

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

    df_result = p2p_results.combine_dfs(list_of_dfs)
    p2p_results.show_results(df_result,  start_date,  end_date)
