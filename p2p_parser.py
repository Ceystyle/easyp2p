# -*- coding: utf-8 -*-

"""
Module for parsing output files of P2P platforms and printing combined results.

    Each P2P platform has a unique format for presenting investment results.
    The purpose of this module is to provide parser methods to transform them
    into a single output format. The combined output is aggregated and
    written to an Excel file.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""
from datetime import date, datetime
import locale
from pathlib import Path
from typing import List, Sequence, Tuple

import pandas as pd

import p2p_helper

# Define all necessary payment types
INTEREST_PAYMENT = 'Zinszahlungen'
BUYBACK_INTEREST_PAYMENT = 'Zinszahlungen aus Rückkäufen'
BUYBACK_PAYMENT = 'Rückkäufe'
INVESTMENT_PAYMENT = 'Investitionen'
REDEMPTION_PAYMENT = 'Tilgungszahlungen'
LATE_FEE_PAYMENT = 'Verzugsgebühren'
INCOMING_PAYMENT = 'Einzahlungen'
OUTGOING_PAYMENT = 'Auszahlungen'
DEFAULT_PAYMENT = 'Ausfälle'
START_BALANCE_NAME = 'Startguthaben'
END_BALANCE_NAME = 'Endsaldo'
TOTAL_INCOME = 'Gesamteinnahmen'
DATE = 'Datum'
PLATFORM = 'Plattform'
CURRENCY = 'Währung'

# TARGET_COLUMNS are the columns which will be shown in the final result file
TARGET_COLUMNS = [
    DATE,
    PLATFORM,
    CURRENCY,
    START_BALANCE_NAME,
    END_BALANCE_NAME,
    TOTAL_INCOME,
    INTEREST_PAYMENT,
    INVESTMENT_PAYMENT,
    REDEMPTION_PAYMENT,
    BUYBACK_PAYMENT,
    BUYBACK_INTEREST_PAYMENT,
    LATE_FEE_PAYMENT,
    DEFAULT_PAYMENT,
]


def _check_unknown_cf_types(
        df: pd.DataFrame, orig_cf_type_name: str) -> str:
    """
    Helper function to identify any unknown cash flow types.

    Args:
        df (pandas.DataFrame): data frame which contains the results for this
        P2P platform
        orig_cf_type_name (str): name of data frame column which contains the
        cash flow types as reported by the P2P platform

    Returns:
        str: string consisting of all unknown cash flow types

    """
    unknown_cf_types = set(df[orig_cf_type_name].where(
        df['Cashflow-Typ'].isna()).dropna().tolist())
    return ', '.join(sorted(unknown_cf_types))


def get_missing_months(df: pd.DataFrame, date_range: Tuple[date, date]) \
        -> List[Tuple[date, date]]:
    """
    Get list of months in date_range which do not contain at least one cashflow.

    This function will identify all months in date_range which do not contain
    at least one cashflow in the provided DataFrame. A list of those months
    is returned.

    Args:
        df (pd.DataFrame): a DataFrame containing all cashflows in date_range
            for the current P2P platform
        date_range (tuple(date, date)): date range (start_date, end_date)
            for which the results must be generated.

    Returns:
        List[Tuple[date, date]]: list of tuples (start_of_month, end_of_month)
            which do not contain a cashflow.

    """
    list_of_months = p2p_helper.get_list_of_months(date_range)

    # If there were no cashflows all months are missing
    if df.empty:
        return list_of_months

    # Get all cashflow dates in date format from the DataFrame
    df[DATE] = pd.to_datetime(df[DATE], format='%d.%m.%Y')
    cf_date_list = []
    for elem in df[DATE].tolist():
        cf_date_list.append(date(elem.year, elem.month, elem.day))

    # Remove all months for which there is at least one cashflow
    for cf_date in cf_date_list:
        for month in list_of_months:
            if month[0] <= cf_date <= month[1]:
                list_of_months.remove(month)

    return list_of_months


def add_missing_months(
        df: pd.DataFrame, missing_months: List[Tuple[date, date]]) \
        -> pd.DataFrame:
    """
    Create a zero entry in df for all missing_months.

    This function will create a new row in the DataFrame df for each month in
    missing_months. This will ensure that months without cashflows are shown
    in the final result file.

    Args:
        df (pd.DataFrame): a DataFrame containing all cashflows in date_range
            for the current P2P platform
        date_range (List[Tuple[date, date]]): list of months
            (start_of_month, end_of_month) which do not contain a cashflow.

    Returns:
        pd.DataFrame: the original DataFrame df with one zero line appended for
            each month in missing_months

    """
    # Create list with new cashflow dates set to the first of each missing month
    new_cf_dates = []
    for month in missing_months:
        new_cf_dates.append(datetime(
            month[0].year, month[0].month, month[0].day))

    # Set all columns of the new df to zero, except for the DATE column
    content = dict()
    zeroes = [0.] * len(new_cf_dates)
    for column in TARGET_COLUMNS:
        content[column] = zeroes
    content[DATE] = new_cf_dates

    # Create the new DataFrame and append it to the old one
    df_new = pd.DataFrame(data=content, columns=TARGET_COLUMNS)
    if df.empty:
        df = df_new
    else:
        df = df.append(df_new, sort=False)
    df.fillna(0., inplace=True)
    df.sort_values(by=[DATE], inplace = True)

    return df


def get_df_from_file(input_file):
    """
    Read a pandas.DataFrame from input_file.

    Args:
        input_file (str): file name including path

    Returns:
        pandas.DataFrame: data frame which was read from the file

    Throws:
        RuntimeError: if input_file does not exist, cannot be read or if the
            file format is neither csv or xlsx

    """

    file_format = Path(input_file).suffix

    try:
        if file_format == '.csv':
            df = pd.read_csv(input_file)
        elif file_format == '.xlsx':
            df = pd.read_excel(input_file)
        else:
            raise RuntimeError(
                'Unbekanntes Dateiformat im Parser: ', input_file)
    except FileNotFoundError:
        raise RuntimeError(
            '{0} konnte nicht gefunden werden!'.format(input_file))

    return df


def _create_df_result(df, value_column):
    """
    Helper method to aggregate results by platform, date and currency.

    Args:
        df (pd.DataFrame): data frame which contains the data to be aggregated
        value_column (str): name of the data frame column which contains the
            data to be aggregated

    Returns:
        pd.DataFrame: data frame with the aggregated results

    """
    df_result = pd.pivot_table(
        df, values=value_column, index=['Plattform', 'Datum', 'Währung'],
        columns=['Cashflow-Typ'], aggfunc=sum)
    df_result.fillna(0, inplace=True)
    df_result.reset_index(inplace=True)
    df_result[DATE] = pd.to_datetime(df[DATE], format='%d.%m.%Y')

    return df_result


def _combine_dfs(list_of_dfs: Sequence[pd.DataFrame]) -> pd.DataFrame:
    """
    Helper method for combining pandas data frames.

    Args:
        list_of_dfs (list[pd.DataFrame]): a list of data frames which need
            to be combined

    Returns:
        pd.DataFrame: the combined data frame

    """
    df_result = None
    for df in list_of_dfs:
        if df_result is not None:
            df_result = df_result.append(df, sort=False).fillna(0)
        else:
            df_result = df

    return df_result


def bondora(
    date_range: Tuple[date, date],
    input_file: str = 'p2p_downloads/bondora_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Bondora.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Bondora web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    df = get_df_from_file(input_file)

    if not df.empty:
        df.set_index('Zeitraum', inplace=True)
        df.drop(['Gesamt:'], inplace=True)
        df.replace({r'\.': '', ',': '.', '€': ''}, inplace=True, regex=True)
        df.rename_axis(DATE, inplace=True)
        df.rename(
            columns={
                'Eingesetztes Kapital (netto)': INCOMING_PAYMENT,
                'Erhaltene Zinsen - gesamt': INTEREST_PAYMENT,
                'Erhaltener Kapitalbetrag - gesamt': REDEMPTION_PAYMENT,
                'Investitionen (netto)': INVESTMENT_PAYMENT,
            },
            inplace=True
        )
        # The following columns will not be shown in the final result (at least
        # for now). The other P2P platforms do not report them. We rename them
        # to shorter names anyway.
        df.rename(
            columns={
                'Darlehensbetrag und erhaltene Zinsen - insgesamt':
                    'Gesamtzahlungen',
                'Geplante Zinsen - gesamt': 'Geplante Zinszahlungen',
                'Geplanter Kapitalbetrag - gesamt':
                    'Geplante Tilgungszahlungen',
                'Kapitalbetrag und geplante Zinsen - gesamt':
                    'Geplante Gesamtzahlungen'
            },
            inplace=True
        )
        df = df.astype('float64')

        df[DEFAULT_PAYMENT] = (
            df['Tilgungszahlungen'] - df['Geplante Tilgungszahlungen'])

        df.reset_index(level=0, inplace=True)
        # TODO: make sure locale is installed
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
        df[DATE] = pd.to_datetime(df[DATE], format='%b %Y')
        df[DATE] = df[DATE].dt.strftime('%d.%m.%Y')

    # Check if there are months in date_range with no cashflows. If yes, add
    # a zero line for those months
    missing_months = get_missing_months(df, date_range)
    if missing_months:
        df = add_missing_months(df, missing_months)

    df[CURRENCY] = 'EUR'
    df[PLATFORM] = 'Bondora'
    df.set_index([PLATFORM, DATE, CURRENCY], inplace=True)

    # Since we define the column names, Bondora cannot have unknown CF types
    return (df, '')


def mintos(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/mintos_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Mintos.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Mintos web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    df = get_df_from_file(input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if df.empty:
        missing_months = get_missing_months(df, date_range)
        df = add_missing_months(df, missing_months)
        df[PLATFORM] = 'Mintos'
        df[CURRENCY] = 'EUR'
        df.set_index(['Plattform', 'Datum', 'Währung'], inplace=True)
        return (df, '')

    mintos_dict = dict()
    mintos_dict['Interest income'] = INTEREST_PAYMENT
    mintos_dict['Interest income on rebuy'] = BUYBACK_INTEREST_PAYMENT
    mintos_dict['Delayed interest income on rebuy'] = BUYBACK_INTEREST_PAYMENT
    mintos_dict['Investment principal rebuy'] = BUYBACK_PAYMENT
    mintos_dict['Investment principal increase'] = INVESTMENT_PAYMENT
    mintos_dict['Investment principal repayment'] = REDEMPTION_PAYMENT
    mintos_dict['Late payment fee income'] = LATE_FEE_PAYMENT
    mintos_dict['Incoming client payment'] = INCOMING_PAYMENT
    # Treat bonus/cashback payments as normal interest payments
    mintos_dict['Cashback bonus'] = INTEREST_PAYMENT
    mintos_dict['Reversed incoming client payment'] = OUTGOING_PAYMENT

    df.rename(columns={'Date': DATE, 'Currency': CURRENCY}, inplace=True)
    df[DATE] = pd.to_datetime(df[DATE], format='%Y-%m-%d %H:%M:%S')
    df[DATE] = df[DATE].dt.strftime('%d.%m.%Y')
    df['Mintos_Cashflow-Typ'], df['Loan ID'] = df['Details'].str.split(
        ' Loan ID: ').str
    df['Mintos_Cashflow-Typ'] = df['Mintos_Cashflow-Typ'].str.split(
        ' Rebuy purpose').str[0]
    df['Cashflow-Typ'] = df['Mintos_Cashflow-Typ'].map(mintos_dict)
    df[PLATFORM] = 'Mintos'

    unknown_cf_types = _check_unknown_cf_types(df, 'Mintos_Cashflow-Typ')
    df_result = _create_df_result(df, 'Turnover')

    # Add rows for months in date_range without cashflows
    missing_months = get_missing_months(df, date_range)
    if missing_months:
        df_result = add_missing_months(df_result, missing_months)

    df_result.set_index([PLATFORM, DATE, CURRENCY], inplace=True)
    # TODO: get start and end balance

    return (df_result, unknown_cf_types)


def robocash(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/robocash_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Robocash.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Robocash web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    robocash_dict = dict()
    robocash_dict['Zinsenzahlung'] = INTEREST_PAYMENT
    robocash_dict['Darlehenskauf'] = INVESTMENT_PAYMENT
    robocash_dict['Kreditrückzahlung'] = REDEMPTION_PAYMENT
    robocash_dict['Die Geldauszahlung'] = OUTGOING_PAYMENT
    robocash_dict['Geldeinzahlung'] = INCOMING_PAYMENT

    df = df[df.Operation != 'Die Geldauszahlung aus dem Portfolio']
    df = df[df.Operation != 'Portfolio auffüllen']
    df.rename(columns={'Datum und Laufzeit': 'Datum'}, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d %H:%M:%S')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Operation'].map(robocash_dict)
    df['Währung'] = 'EUR'
    df['Plattform'] = 'Robocash'

    unknown_cf_types = _check_unknown_cf_types(df, 'Operation')
    df_result = _create_df_result(df, 'Betrag')

    return (df_result, unknown_cf_types)


def swaper(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/swaper_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Swaper.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Swaper web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    swaper_dict = dict()
    swaper_dict['REPAYMENT_INTEREST'] = INTEREST_PAYMENT
    swaper_dict['EXTENSION_INTEREST'] = INTEREST_PAYMENT
    swaper_dict['INVESTMENT'] = INVESTMENT_PAYMENT
    swaper_dict['REPAYMENT_PRINCIPAL'] = REDEMPTION_PAYMENT
    swaper_dict['BUYBACK_INTEREST'] = BUYBACK_INTEREST_PAYMENT
    swaper_dict['BUYBACK_PRINCIPAL'] = BUYBACK_PAYMENT

    try:
        df.rename(columns={'Booking date': 'Datum'}, inplace=True)
        df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
        df['Cashflow-Typ'] = df['Transaction type'].map(swaper_dict)
        df['Währung'] = 'EUR'
        df['Plattform'] = 'Swaper'
    except KeyError as err:
        raise RuntimeError(
            'Swaper: unbekannte Spalte im Parser: ' + str(err))
    except AttributeError as err:
        if df.shape[0] == 0:
            # TODO: add rows with zeros instead of erroring out
            raise RuntimeError(
                'Swaper: keine Zahlungen im angeforderten Zeitraum vorhanden!')
        else:
            raise AttributeError(err)

    unknown_cf_types = _check_unknown_cf_types(df, 'Transaction type')
    df_result = _create_df_result(df, 'Amount')

    return (df_result, unknown_cf_types)


def peerberry(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/peerberry_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Peerberry.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the PeerBerry web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    peerberry_dict = dict()
    peerberry_dict['Amount of interest payment received'] = INTEREST_PAYMENT
    peerberry_dict['Investment'] = INVESTMENT_PAYMENT
    peerberry_dict['Amount of principal payment received'] = REDEMPTION_PAYMENT

    df.rename(
        columns={'Date': 'Datum', 'Currency Id': 'Währung'}, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Type'].map(peerberry_dict)
    df['Plattform'] = 'Peerberry'

    unknown_cf_types = _check_unknown_cf_types(df, 'Type')
    df_result = _create_df_result(df, 'Amount')

    return (df_result, unknown_cf_types)


def estateguru(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/estateguru_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Estateguru.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Estateguru web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    estateguru_dict = dict()
    estateguru_dict['Zins'] = INTEREST_PAYMENT
    # Treat bonus payments as normal interest payments
    estateguru_dict['Bonus'] = INTEREST_PAYMENT
    estateguru_dict['Investition(Auto Investieren)'] = INVESTMENT_PAYMENT
    estateguru_dict['Hauptbetrag'] = REDEMPTION_PAYMENT
    estateguru_dict['Einzahlung(Banktransfer)'] = INCOMING_PAYMENT
    estateguru_dict['Entschädigung'] = LATE_FEE_PAYMENT

    df = df[:-1]  # Drop last line which only contains a summary
    df.rename(
        columns={
            'Zahlungsdatum': 'Datum',
            'Cashflow-Typ': 'Estateguru_Cashflow-Typ',
        }, inplace=True)

    df['Datum'] = pd.to_datetime(df['Datum'], format='%d/%m/%Y %H:%M')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Estateguru_Cashflow-Typ'].map(estateguru_dict)
    df['Plattform'] = 'Estateguru'
    df['Währung'] = 'EUR'
    df['Betrag'] = df['Betrag'].astype('float')

    unknown_cf_types = _check_unknown_cf_types(df, 'Estateguru_Cashflow-Typ')
    df_result = _create_df_result(df, 'Betrag')

    return (df_result, unknown_cf_types)


def iuvo(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/iuvo_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Iuvo.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Iuvo web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    # Interest and redemption payments are reported in two columns by Iuvo.
    # For our purposes this is not necessary, so we will add them.
    df[INTEREST_PAYMENT] = 0
    df[REDEMPTION_PAYMENT] = 0

    # Date column will raise an error which can be ignored:
    df = df.astype('float64', errors='ignore')

    interest_types = ['erhaltene Zinsen', 'vorfristige erhaltene Zinsen']
    for elem in interest_types:
        if elem in df.columns:
            df[INTEREST_PAYMENT] += df[elem]
            del df[elem]

    redemption_types = [
        'vorfristiger erhaltener Grundbetrag', 'erhaltener Grundbetrag']
    for elem in redemption_types:
        if elem in df.columns:
            df[REDEMPTION_PAYMENT] += df[elem]
            del df[elem]

    df.rename(
        columns={
            'Anfangsbestand': START_BALANCE_NAME,
            'Investitionen auf dem Primärmarkt mit Autoinvest':
                INVESTMENT_PAYMENT,
            'Endbestand': END_BALANCE_NAME,
            'erhaltener Rückkaufgrundbetrag': BUYBACK_PAYMENT,
            'erhaltene Verspätungsgebühren': LATE_FEE_PAYMENT},
        inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Plattform'] = 'Iuvo'
    df['Währung'] = 'EUR'

    df.reset_index(level=0, inplace=True)
    df_result = df.set_index(['Plattform', 'Datum', 'Währung'])

    # Since we set the column names, there cannot be unknown CF types
    return (df_result, '')


def grupeer(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/grupeer_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Grupeer.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Grupeer web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    grupeer_dict = dict()
    grupeer_dict['Interest'] = INTEREST_PAYMENT
    grupeer_dict['Investment'] = INVESTMENT_PAYMENT
    grupeer_dict['Deposit'] = INCOMING_PAYMENT
    # Treat cashback as interest payment:
    grupeer_dict['Cashback'] = INTEREST_PAYMENT
    grupeer_dict['Principal'] = REDEMPTION_PAYMENT

    df.rename(columns={'Date': 'Datum'}, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format="%d.%m.%Y")
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Type'].map(grupeer_dict)
    df['Plattform'] = 'Grupeer'
    df['Währung'] = 'EUR'
    df['Amount'] = df['Amount'].apply(lambda x: x.replace(',', '.')).astype(
        'float')

    unknown_cf_types = _check_unknown_cf_types(df, 'Type')
    df_result = _create_df_result(df, 'Amount')

    return (df_result, unknown_cf_types)


def dofinance(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/dofinance_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for DoFinance.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the DoFinance web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    dofinance_dict = dict()
    dofinance_dict['Verdienter Gewinn'] = INTEREST_PAYMENT
    dofinance_dict['Auszahlung auf Bankkonto'] = OUTGOING_PAYMENT
    dofinance_dict[
        'Abgeschlossene Investition\nRate: 12% Typ: automatisch'] = \
        REDEMPTION_PAYMENT
    dofinance_dict['Anlage\nRate: 12% Typ: automatisch'] = INVESTMENT_PAYMENT

    # The last two rows only contain a summary, drop them
    df = df[:-2]
    df.rename(columns={'Bearbeitungsdatum': 'Datum'}, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Cashflow-Typ'] = df['Art der Transaktion'].map(dofinance_dict)
    df['Plattform'] = 'DoFinance'
    df['Währung'] = 'EUR'

    unknown_cf_types = _check_unknown_cf_types(df, 'Art der Transaktion')
    df_result = _create_df_result(df, 'Betrag, €')

    return (df_result, unknown_cf_types)


def twino(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/twino_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Twino.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Twino web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    #TODO: treat missing months / no cashflows
    df = get_df_from_file(input_file)

    twino_dict = dict()
    twino_dict['EXTENSION INTEREST'] = INTEREST_PAYMENT
    twino_dict['REPAYMENT INTEREST'] = INTEREST_PAYMENT
    twino_dict['SCHEDULE INTEREST'] = INTEREST_PAYMENT
    twino_dict['BUYBACK INTEREST'] = BUYBACK_INTEREST_PAYMENT
    twino_dict['REPURCHASE INTEREST'] = BUYBACK_INTEREST_PAYMENT
    twino_dict['BUYBACK PRINCIPAL'] = BUYBACK_PAYMENT
    twino_dict['REPURCHASE PRINCIPAL'] = BUYBACK_PAYMENT
    twino_dict['REPAYMENT PRINCIPAL'] = REDEMPTION_PAYMENT
    twino_dict['BUY_SHARES PRINCIPAL'] = INVESTMENT_PAYMENT

    df = df[1:]  # The first row only contains a generic header
    new_header = df.iloc[0] # Get the new first row as header
    df = df[1:] # Remove the header row
    df.columns = new_header # Set the header row as the df header

    df.rename(columns={'Processing Date': 'Datum'}, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y %H:%M')
    df['Datum'] = df['Datum'].dt.strftime('%d.%m.%Y')
    df['Twino_Cashflow-Typ'] = df['Type'] + ' ' + df['Description']
    df['Cashflow-Typ'] = df['Twino_Cashflow-Typ'].map(twino_dict)
    df['Plattform'] = 'Twino'
    df['Währung'] = 'EUR'

    unknown_cf_types = _check_unknown_cf_types(df, 'Twino_Cashflow-Typ')
    df_result = _create_df_result(df, 'Amount, EUR')

    return (df_result, unknown_cf_types)


def show_results(
        list_of_dfs: Sequence[pd.DataFrame],
        date_range: Tuple[date, date],
        output_file: str) -> bool:
    """
    Sum up the results contained in data frames and write them to an Excel file.

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
        bool: True on success, False on failure

    """
    df = _combine_dfs(list_of_dfs)

    if df is None:
        return False

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
    show_columns = [col for col in df.columns if col in TARGET_COLUMNS]

    df.reset_index(level=['Datum', 'Währung'], inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y')
    df['Monat'] = pd.to_datetime(
        df['Datum'], format='%d.%m.%Y').dt.to_period('M')
    df = df.round(2)

    # Make sure we only show results between start and end date
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])
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
        for index in month_pivot_table.index.levels[0]:
            start_balance = month_pivot_table.loc[index]['Startguthaben'][0]
            totals_pivot_table.loc[index]['Startguthaben'] = start_balance
    if 'Endsaldo' in totals_pivot_table.columns:
        for index in month_pivot_table.index.levels[0]:
            end_balance = month_pivot_table.loc[index]['Endsaldo'][0]
            totals_pivot_table.loc[index]['Endsaldo'] = end_balance

    # Write total results to file
    totals_pivot_table.to_excel(writer, 'Gesamtergebnis')
    writer.save()

    return True
