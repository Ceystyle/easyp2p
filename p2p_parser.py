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

def bondora(start_date,  end_date,  df_bondora,  df_result):
    try:
        df_bondora.replace({'\.': '',  ',':'.',  '€':''},  inplace=True,  regex=True)
        df_data = df_bondora.loc['Okt 2018'].astype(float)
        df_result.loc['Bondora']['Anfangssaldo '+str(start_date)] = df_data['Startguthaben']
        df_result.loc['Bondora']['Investitionen'] = df_data['Investitionen (netto)']
        df_result.loc['Bondora']['Tilgungszahlungen'] = df_data['Erhaltener Kapitalbetrag - gesamt']
        df_result.loc['Bondora']['Zinszahlungen'] = df_data['Erhaltene Zinsen - gesamt']
        df_result.loc['Bondora']['Verzugsgebühren'] = 0 #Bondora doesn't show late fees separately
        df_result.loc['Bondora']['Ausfälle'] = \
            round(df_data['Geplanter Kapitalbetrag - gesamt'] - df_data['Erhaltener Kapitalbetrag - gesamt'],  2)
        df_result.loc['Bondora']['Rückkäufe'] = 0 # Bondora doesn't provide a buyback service
        df_result.loc['Bondora']['Zinszahlungen aus Rückkäufen'] = 0 # Bondora doesn't provide a buyback service
        df_result.loc['Bondora']['Zinszahlungen (gesamt)'] = df_data['Erhaltene Zinsen - gesamt']
        df_result.loc['Bondora']['Endsaldo '+str(end_date)] = df_data['Endsaldo']
        df_result.loc['Bondora'] = df_result.loc['Bondora'].astype(str) + '€'
        df_result.loc['Bondora'].replace('\.', ',',  inplace=True,  regex=True)
    except:
        print("Der Bondora-Kontoauszug konnte nicht verarbeitet werden!")

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
    #df = pd.read_csv('p2p_downloads/estateguru_statement.csv',  index_col=1)
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
