import pandas as pd

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

    target_columns = ['Startguthaben', 'Endsaldo', 'Investitionen', 'Tilgungszahlungen', 'Zinszahlungen', 'Verzugsgebühren',\
        'Rückkäufe', 'Zinszahlungen aus Rückkäufen', 'Ausfälle']
    show_columns = [col for col in df.columns if col in target_columns]

    df.reset_index(level=['Datum', 'Währung'],  inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y')
    df['Monat'] = pd.to_datetime(df['Datum'],  format='%d.%m.%Y').dt.to_period('M')

    #Make sure we only show results between start and end date
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    df = df[(df['Datum'] >= start_date) & (df['Datum'] <= end_date)]

    #print monthly results to screen
    print('Monatsergebnisse für den Zeitraum {0}-{1} pro Plattform:\n'.format(start_date.strftime('%d.%m.%Y'),\
        end_date.strftime('%d.%m.%Y')))
    month_pivot_table = pd.pivot_table(df, values=show_columns,  index=['Plattform',  'Währung', 'Monat'],  aggfunc=sum)
    print(month_pivot_table)

    #print monthly results to file
    output_file = 'P2P_Ergebnisse_{0}-{1}.xlsx'.format(start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
    writer = pd.ExcelWriter(output_file)
    month_pivot_table.to_excel(writer, 'Monatsergebnisse')

    #print total results to screen
    print('Gesamtergebnis für den Zeitraum {0}-{1} pro Plattform:\n'.format(start_date.strftime('%d.%m.%Y'),\
        end_date.strftime('%d.%m.%Y')))
    totals_pivot_table = pd.pivot_table(df, values=show_columns,  index=['Plattform',  'Währung'],  aggfunc=sum)

    if 'Startguthaben' in totals_pivot_table.columns:
        for pl in month_pivot_table.index.levels[0]:
            start_balance = month_pivot_table.loc[pl]['Startguthaben'][0]
            totals_pivot_table.loc[pl]['Startguthaben'] = start_balance
    if 'Endsaldo' in totals_pivot_table.columns:
        for pl in month_pivot_table.index.levels[0]:
            end_balance = month_pivot_table.loc[pl]['Endsaldo'][0]
            totals_pivot_table.loc[pl]['Endsaldo'] = end_balance

    print(totals_pivot_table)

    #print total results to file
    totals_pivot_table.to_excel(writer, 'Gesamtergebnis')
    writer.save()

    return 0
