import locale
import pandas as pd
import xlrd

def read_excel(p2p_name,  filename):
    try:
        df = pd.read_excel(filename)
    except xlrd.biffh.XLRDError:
        print('Der heruntergeladene {0}-Kontoauszug ist beschädigt und wird daher ignoriert.'.format(p2p_name))
        return None
    except FileNotFoundError:
        print('Der heruntergeladene {0}-Kontoauszug konnte nicht gefunden werden.'.format(p2p_name))
        return None
        
    return df

def bondora():
    df = pd.read_csv('p2p_downloads/bondora_statement.csv', index_col=0)

    df.drop(['Gesamt:'], inplace=True)
    df.replace({'\.': '',  ',':'.',  '€':''},  inplace=True,  regex=True)
    df.rename_axis('Datum', inplace=True)
    df.rename(columns={'Erhaltene Zinsen - gesamt': 'Zinszahlungen', 'Investitionen (netto)': 'Investitionen', \
        'Erhaltener Kapitalbetrag - gesamt': 'Tilgungszahlungen', 'Eingesetztes Kapital (netto)': 'Einzahlungen'},  inplace=True)
    df.rename(columns={'Darlehensbetrag und erhaltene Zinsen - insgesamt': 'Gesamtzahlungen', \
        'Geplanter Kapitalbetrag - gesamt': 'Geplante Tilgungszahlungen', \
        'Geplante Zinsen - gesamt': 'Geplante Zinszahlungen', \
        'Kapitalbetrag und geplante Zinsen - gesamt': 'Geplante Gesamtzahlungen'},  inplace=True)
    df = df.astype('float64')

    df['Währung'] = 'EUR'
    df['Plattform'] = 'Bondora'
    df['Ausfälle'] = df['Tilgungszahlungen'] - df['Geplante Tilgungszahlungen']

    df.reset_index(level=0, inplace=True)
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8') #TODO: make sure locale is installed
    df['Datum'] = pd.to_datetime(df['Datum'], format='%b %Y')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df_result = df.set_index(['Plattform', 'Datum', 'Währung'])

    return df_result

def mintos():
    df = read_excel('Mintos', 'p2p_downloads/mintos_statement.xlsx')
    
    if df is None:
        return None
        
    mintos_dict = dict()
    mintos_dict['Interest income'] = 'Zinszahlungen'
    mintos_dict['Interest income on rebuy'] = 'Zinszahlungen aus Rückkäufen'
    mintos_dict['Delayed interest income on rebuy'] = 'Zinszahlungen aus Rückkäufen'
    mintos_dict['Investment principal rebuy'] = 'Rückkäufe'
    mintos_dict['Investment principal increase'] = 'Investitionen'
    mintos_dict['Investment principal repayment'] = 'Tilgungszahlungen'
    mintos_dict['Late payment fee income'] = 'Verzugsgebühren'
    mintos_dict['Incoming client payment'] = 'Einzahlungen'
    mintos_dict['Cashback bonus'] = 'Zinszahlungen' # treat bonus payments as normal interest payments
    mintos_dict['Reversed incoming client payment'] = 'Auszahlungen'
    
    df.rename(columns={'Date': 'Datum',  'Currency': 'Währung'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'])
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Mintos_Cashflow-Typ'], df['Loan ID'] = df['Details'].str.split(' Loan ID: ').str
    df['Mintos_Cashflow-Typ'] = df['Mintos_Cashflow-Typ'].str.split(' Rebuy purpose').str[0]
    df['Cashflow-Typ'] = df['Mintos_Cashflow-Typ'].map(mintos_dict)
    df['Plattform'] = 'Mintos'
    
    if df['Mintos_Cashflow-Typ'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Mintos: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Mintos_Cashflow-Typ'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Turnover',  index=['Plattform','Datum', 'Währung'],  columns=['Cashflow-Typ'],\
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)
    
    #TODO: Anfangs- und Endsaldo ermitteln

    return df_result

def robocash():
    df = read_excel('Robo.cash', 'p2p_downloads/robocash_statement.xls')

    if df is None:
        return None
        
    robocash_dict = dict()
    robocash_dict['Zinsenzahlung'] = 'Zinszahlungen'
    robocash_dict['Darlehenskauf'] = 'Investitionen'
    robocash_dict['Kreditrückzahlung'] = 'Tilgungszahlungen'
    robocash_dict['Die Geldauszahlung'] = 'Auszahlungen'

    df = df[df.Operation != 'Die Geldauszahlung aus dem Portfolio']
    df.rename(columns={'Datum und Laufzeit': 'Datum'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%Y-%m-%d %H:%M:%S')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Operation'].map(robocash_dict)
    df['Währung'] = 'EUR'
    df['Plattform'] = 'Robocash'

    if df['Operation'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Robocash: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Operation'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Betrag',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result
    
def swaper():
    df = read_excel('Swaper', 'p2p_downloads/swaper_statement.xlsx')
    
    if df is None:
        return None

    swaper_dict = dict()
    swaper_dict['REPAYMENT_INTEREST'] = 'Zinszahlungen'
    swaper_dict['EXTENSION_INTEREST'] = 'Zinszahlungen'
    swaper_dict['INVESTMENT'] = 'Investitionen'
    swaper_dict['REPAYMENT_PRINCIPAL'] = 'Tilgungszahlungen'
    swaper_dict['BUYBACK_INTEREST'] = 'Zinszahlungen aus Rückkäufen'
    swaper_dict['BUYBACK_PRINCIPAL'] = 'Rückkäufe'
    
    df.rename(columns={'Booking date': 'Datum'},  inplace=True)
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Transaction type'].map(swaper_dict)
    df['Währung'] = 'EUR'
    df['Plattform'] = 'Swaper'

    if df['Transaction type'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Swaper: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Transaction type'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Amount',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result
    
def peerberry():
    df = pd.read_csv('p2p_downloads/peerberry_statement.csv')
    
    if df is None:
        return None

    peerberry_dict = dict()
    peerberry_dict['Amount of interest payment received'] = 'Zinszahlungen'
    peerberry_dict['Investment'] = 'Investitionen'
    peerberry_dict['Amount of principal payment received'] = 'Tilgungszahlungen'

    df.rename(columns={'Date': 'Datum',  'Currency Id': 'Währung'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%Y-%m-%d')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Type'].map(peerberry_dict)
    df['Plattform'] = 'Peerberry'

    if df['Type'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Peerberry: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Type'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Amount',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result

def estateguru():
    df = pd.read_csv('p2p_downloads/estateguru_statement.csv')

    if df is None:
        return None 
 
    estateguru_dict = dict()
    estateguru_dict['Zins'] = 'Zinszahlungen'
    estateguru_dict['Bonus'] = 'Zinszahlungen' # treat bonus payments as normal interest payments
    estateguru_dict['Investition  (Auto Investieren)'] = 'Investitionen'
    estateguru_dict['Hauptbetrag'] = 'Tilgungszahlungen'
    estateguru_dict['Einzahlung  (Banktransfer)'] = 'Einzahlungen'
    estateguru_dict['Entschädigung'] = 'Verzugsgebühren'

    df = df[:-1] #drop last line which only contains a summary
    df.rename(columns={'Bestätigungsdatum': 'Datum',  'Cashflow-Typ': 'Estateguru_Cashflow-Typ'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y, %H:%M')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Estateguru_Cashflow-Typ'].map(estateguru_dict)
    df['Plattform'] = 'Estateguru'
    df['Währung'] = 'EUR'
    df['Betrag (€)'] = df['Betrag (€)'].apply(lambda x: x.replace('(', '-').replace(')', '').replace(',', '.'))\
        .astype('float')

    if df['Estateguru_Cashflow-Typ'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Estateguru: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Estateguru_Cashflow-Typ'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Betrag (€)',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result

def iuvo():
    df = pd.read_csv('p2p_downloads/iuvo_statement.csv', index_col=-1)

    if df is None:
        return None

    df['Zinszahlungen'] = 0
    df['Tilgungszahlungen'] = 0
    df = df.astype('float64', errors='ignore') #the date column will raise an error which can be ignored

    interest_types = ['Zins erhalten', 'Vorzeitige Zinstilgung']
    for it in interest_types:
        if it in df.columns:
            df['Zinszahlungen'] += df[it]
            del df[it]

    redemption_types = ['Vorzeitige Kreditbetragtilgung', 'Kreditbetrag erhalten']
    for rt in redemption_types:
        if rt in df.columns:
            df['Tilgungszahlungen'] += df[rt]
            del df[rt]

    df.rename(columns={'Anfangsbestand': 'Startguthaben', 'Endbestand': 'Endsaldo', 'Automatische Kapitalanlage auf dem Primärmarkt': 'Investitionen', \
        'Kreditbetrag bei Rückkauf erhalten': 'Rückkäufe', 'Verzugsstrafen erhalten': 'Verzugsgebühren'}, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Plattform'] = 'Iuvo'
    df['Währung'] = 'EUR'

    df.reset_index(level=0, inplace=True)
    df_result = df.set_index(['Plattform', 'Datum', 'Währung'])

    return df_result

def grupeer():
    df = read_excel('Grupeer', 'p2p_downloads/grupeer_statement.xlsx')

    if df is None:
        return None

    grupeer_dict = dict()
    grupeer_dict['Interest'] = 'Zinszahlungen'
    grupeer_dict['Investment'] = 'Investitionen'
    grupeer_dict['Deposit'] = 'Einzahlungen'
    grupeer_dict['Cashback'] = 'Zinszahlungen' # treat cashback as interest payment
    grupeer_dict['Principal'] = 'Tilgungszahlungen'

    df.rename(columns={'Date': 'Datum'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format="%d.%m.%Y")
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Type'].map(grupeer_dict)
    df['Plattform'] = 'Grupeer'
    df['Währung'] = 'EUR'
    df['Amount'] = df['Amount'].apply(lambda x: x.replace(',', '.')).astype('float')

    if df['Type'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Grupeer: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Type'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Amount',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result

def dofinance():
    df = read_excel('DoFinance', 'p2p_downloads/dofinance_statement.xlsx')

    if df is None:
        return None

    dofinance_dict = dict()
    dofinance_dict['Verdienter Gewinn'] = 'Zinszahlungen'
    dofinance_dict['Auszahlung auf Bankkonto'] = 'Auszahlungen'
    dofinance_dict['Abgeschlossene Investition\nRate: 12% Typ: automatisch'] = 'Tilgungszahlungen'
    dofinance_dict['Anlage\nRate: 12% Typ: automatisch'] = 'Investitionen'

    df = df[:-2] #drop the last two rows
    df.rename(columns={'Bearbeitungsdatum': 'Datum'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Art der Transaktion'].map(dofinance_dict)
    df['Plattform'] = 'DoFinance'
    df['Währung'] = 'EUR'

    if df['Art der Transaktion'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('DoFinance: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Art der Transaktion'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Betrag, €',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result

def twino():
    df = read_excel('Twino', 'p2p_downloads/twino_statement.xlsx')

    if df is None:
        return None

    twino_dict = dict()
    twino_dict['EXTENSION INTEREST'] = 'Zinszahlungen'
    twino_dict['REPAYMENT INTEREST'] = 'Zinszahlungen'
    twino_dict['SCHEDULE INTEREST'] = 'Zinszahlungen'
    twino_dict['BUYBACK INTEREST'] = 'Zinszahlungen aus Rückkäufen'
    twino_dict['REPURCHASE INTEREST'] = 'Zinszahlungen aus Rückkäufen'
    twino_dict['BUYBACK PRINCIPAL'] = 'Rückkäufe'
    twino_dict['REPURCHASE PRINCIPAL'] = 'Rückkäufe'
    twino_dict['REPAYMENT PRINCIPAL'] = 'Tilgungszahlungen'
    twino_dict['BUY_SHARES PRINCIPAL'] = 'Investitionen'

    df = df[1:] #drop first two rows
    df.columns = df.iloc[0] # the first row now contains header names
    df = df[1:]
    df.rename(columns={'Booking Date': 'Datum'},  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y %H:%M')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Twino-Cashflow'] = df['Type'] + ' ' + df['Description']
    df['Cashflow-Typ'] = df['Twino-Cashflow'].map(twino_dict)
    df['Plattform'] = 'Twino'
    df['Währung'] = 'EUR'

    if df['Twino-Cashflow'].where(df['Cashflow-Typ'].isna()).dropna().size > 0:
        print('Twino: unbekannter Cashflow-Typ wird im Ergebnis ignoriert: ',\
            set(df['Twino-Cashflow'].where(df['Cashflow-Typ'].isna()).dropna().tolist()))

    df_result = pd.pivot_table(df, values='Amount, EUR',  index=['Plattform', 'Datum', 'Währung'],  columns=['Cashflow-Typ'], \
        aggfunc=sum)
    df_result.fillna(0,  inplace=True)

    return df_result
