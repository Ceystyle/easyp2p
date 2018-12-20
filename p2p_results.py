# -*- coding: utf-8 -*-

"""
    p2p_results provides two public functions for combining and presenting the
    investment results of the various P2P platforms.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

import pandas as pd


def combine_dfs(list_of_dfs):
    """
    Helper method for combining pandas data frames.

    Args:
        list_of_dfs (list(pandas.DataFrame)): a list of data frames which need
            to be combined

    Returns:
        pandas.DataFrame: the combined data frame

    """
    df_result = None
    for df in list_of_dfs:
        if df_result is not None:
            df_result = df_result.append(df,  sort=False).fillna(0)
        else:
            df_result = df

    return df_result


def show_results(df,  start_date,  end_date, output_file):
    """
    Sums up the results and writes them to an Excel file.

    The results are presented in two ways: on a monthly basis (in the Excel tab
    'Monatsergebnisse') and the total sums (in tab 'Gesamtergebnis') for the
    period between start and end date.

    Args:
        df (pandas.DataFrame): data frame containing the combined data from
            the P2P platforms
        start_date (datetime.date): start of the evaluation period
        end_date (datetime.date): end of the evaluation period
        output_file (str): absolute path to the output file

    Returns:
        int: 0 on success

    """
    if df is None:
        print('Keine Ergebnisse vorhanden')
        return -1

    # Calculate total income for each row
    income_columns = [
        'Zinszahlungen',
        'Verzugsgebühren',
        'Zinszahlungen aus Rückkäufen',
        'Ausfälle'
    ]
    df['Gesamteinnahmen'] = 0
    for col in [col for col in df.columns if col in income_columns]:
        df['Gesamteinnahmen'] += df[col]

    # Show only existing columns
    target_columns = [
        'Startguthaben',
        'Endsaldo',
        'Investitionen',
        'Tilgungszahlungen',
        'Zinszahlungen',
        'Verzugsgebühren',
        'Rückkäufe',
        'Zinszahlungen aus Rückkäufen',
        'Ausfälle',
        'Gesamteinnahmen',
    ]
    show_columns = [col for col in df.columns if col in target_columns]

    df.reset_index(level=['Datum', 'Währung'], inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
    df['Monat'] = pd.to_datetime(
        df['Datum'], format='%d.%m.%Y').dt.to_period('M')
    df.round(2)

    # Make sure we only show results between start and end date
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    df = df[(df['Datum'] >= start_date) & (df['Datum'] <= end_date)]

    # Write monthly results to file
    writer = pd.ExcelWriter(output_file)
    month_pivot_table = pd.pivot_table(
        df, values=show_columns,
        index=['Plattform', 'Währung', 'Monat'], aggfunc=sum)
    month_pivot_table.to_excel(writer, 'Monatsergebnisse')

    totals_pivot_table = pd.pivot_table(
        df, values=show_columns,
        index=['Plattform', 'Währung'], aggfunc=sum)

    if 'Startguthaben' in totals_pivot_table.columns:
        for pl in month_pivot_table.index.levels[0]:
            start_balance = month_pivot_table.loc[pl]['Startguthaben'][0]
            totals_pivot_table.loc[pl]['Startguthaben'] = start_balance
    if 'Endsaldo' in totals_pivot_table.columns:
        for pl in month_pivot_table.index.levels[0]:
            end_balance = month_pivot_table.loc[pl]['Endsaldo'][0]
            totals_pivot_table.loc[pl]['Endsaldo'] = end_balance

    # Write total results to file
    totals_pivot_table.to_excel(writer, 'Gesamtergebnis')
    writer.save()

    return 0
