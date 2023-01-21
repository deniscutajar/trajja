import logging
from datetime import datetime
from enum import Enum
from typing import Union

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas
import pandas as pd
import seaborn as sns
from dateutil.rrule import rrule, MONTHLY

sns.set_theme(style="whitegrid")

logging.basicConfig(level=logging.INFO)


# todo - jupyter notebook

class Field(Enum):
    DATETIME = 'Date & time'
    PURPOSE = 'Purpose'
    AMOUNT = 'Amount'
    YEAR = 'Year'
    MONTH = 'Month'


def str_to_date(date_str: Union[str, None]):
    if not date_str:
        return datetime.now()

    return datetime.strptime(date_str, '%Y-%m-%d')


def get_month_transactions(df: pandas.DataFrame, month: int, year: int):
    return df[(df[Field.DATETIME.value].dt.year == year) & (df[Field.DATETIME.value].dt.month == month)]


def load_settleup_transactions(filepath: str, date_from: datetime, date_to: datetime):
    df = pd.read_csv(filepath)
    df[Field.DATETIME.value] = pd.to_datetime(df[Field.DATETIME.value])
    df[Field.AMOUNT.value] = pd.to_numeric(df[Field.AMOUNT.value], errors='coerce')
    df[Field.PURPOSE.value] = df[Field.PURPOSE.value].str.lower().str.strip()

    return df.loc[(df[Field.DATETIME.value] > date_from) & (df[Field.DATETIME.value] < date_to)]


def filter_df_groceries(df: pandas.DataFrame, on_column: str, keywords: list, keywords_ignore: list,
                        keywords_remove: list):
    df = df[~df[on_column].isnull()]
    pattern = '|'.join([k.lower() for k in keywords])
    filtered_df = df.loc[df[on_column].str.contains(pattern)]

    pattern = '|'.join([k.lower() for k in keywords_ignore])

    filtered_df = filtered_df.loc[~filtered_df[on_column].str.contains(pattern)]

    # Remove redundant terms
    keywords_remove = '|'.join(keywords_remove)
    filtered_df[on_column] = filtered_df[on_column].str.replace(keywords_remove, "").str.strip()

    logging.info(f"Found {len(filtered_df)} entries for groceries from {len(df)} entries")

    return filtered_df


def coeliac_adjustment(df: pandas.DataFrame, c_adj_date: datetime, c_adj_amount: float, date_to: datetime):
    if not date_to:
        date_to = datetime.today()

    # Celiac adjustment date should be in the past
    assert c_adj_date < date_to

    # Compile new dummy dates
    new_dates = [dt for dt in rrule(MONTHLY, dtstart=c_adj_date, until=date_to)]

    # Add dates to dataframe
    for new_date in new_dates:
        df.loc[len(df)] = {
            Field.PURPOSE.value: 'COELIAC VOUCHER',
            Field.AMOUNT.value: c_adj_amount,
            Field.DATETIME.value: new_date
        }

    logging.info(
        f"Added {len(new_dates)} new entries representing {len(new_dates)} months with Coeliac Government Voucher")

    return df


def agg_monthly_expenses(df: pandas.DataFrame):
    agg_df = df.groupby([df[Field.DATETIME.value].dt.year, df[Field.DATETIME.value].dt.month])[Field.AMOUNT.value].agg(
        ['sum', 'mean', 'std']).reset_index(allow_duplicates=True)

    agg_df.columns = [Field.YEAR.value, Field.MONTH.value, Field.AMOUNT.value, 'daily_mean', 'daily_std']

    return agg_df


def agg_yearly_expenses(df: pandas.DataFrame) -> pandas.DataFrame:
    agg_df = df.groupby([df[Field.DATETIME.value].dt.year])[Field.AMOUNT.value].sum().rename_axis(
        [Field.YEAR.value]).reset_index()

    return agg_df


def display_df(df: pd.DataFrame, title: str):
    print(f'\n{title}')
    print(df)


def viz_agg_monthly_expenses(agg_df: pandas.DataFrame, budget: float, title: str):
    ax = sns.lineplot(data=agg_df, x=Field.MONTH.value, y=Field.AMOUNT.value, palette="tab10",
                      hue=Field.YEAR.value, linewidth=2.5)
    ax.set(title=title)

    plt.axhline(budget, color='gray', linestyle='--')

    display_df(agg_df, title)


def viz_agg_expenditure_breakdown(df: pandas.DataFrame, title: str, top: int = 10, year: int = None):
    """
    Where are you spending your money?
    :return:
    """
    # Filter by a single year
    if year:
        df = df[df[Field.DATETIME.value].dt.year == year]

    # Group by purpose
    agg_df = df.groupby([df[Field.PURPOSE.value]])[Field.AMOUNT.value].sum().rename_axis(
        [Field.PURPOSE.value]).reset_index()

    # Display only the top 10 expenditures
    agg_df = agg_df.sort_values(by=Field.AMOUNT.value, ascending=False)[:top]

    # New figure
    plt.figure()
    ax = sns.barplot(y=Field.PURPOSE.value, x=Field.AMOUNT.value, data=agg_df, palette='plasma')
    ax.set(ylabel=None, title=title)

    ax.bar_label(ax.containers[0], label_type='center', fmt='%1.0f', color='w')

    plt.tight_layout()

    display_df(agg_df, title)


def viz_agg_yearly_expenses(df: pandas.DataFrame, title: str) -> None:
    y_df = agg_yearly_expenses(df)
    c_y_df = agg_yearly_expenses(df[df[Field.PURPOSE.value] == 'COELIAC VOUCHER'])

    plt.figure()

    agg_df = y_df.merge(c_y_df, on='Year', how='left', suffixes=('_expense', '_coeliac'))
    _ = sns.barplot(y='Amount_expense', x=Field.YEAR.value, data=agg_df, color='lightgray')
    ax = sns.barplot(y='Amount_coeliac', x=Field.YEAR.value, data=agg_df, color='darkgray')
    ax.set(ylabel='Total (€)', xlabel=None, title=title)

    top_bar = mpatches.Patch(color='lightgray', label='Expenses')
    bottom_bar = mpatches.Patch(color='darkgray', label='Coeliac Voucher ')
    plt.legend(handles=[top_bar, bottom_bar])

    display_df(agg_df, title)


def viz_mean_monthly_expense(df: pd.DataFrame, title: str):
    # Monthly mean expenditure on groceries
    m_agg_df = df.groupby([df[Field.DATETIME.value].dt.year, df[Field.DATETIME.value].dt.month])[
        'Amount'].sum().groupby(
        level=0).agg(['mean', 'std']).reset_index()

    m_agg_df.columns = [Field.YEAR.value, 'Monthly_mean', 'Monthly_std']
    m_agg_df['Change'] = m_agg_df['Monthly_mean'].diff() / m_agg_df['Monthly_mean']
    plt.figure()

    ax = sns.barplot(y='Monthly_mean', x=Field.YEAR.value, data=m_agg_df, yerr=m_agg_df['Monthly_std'],
                     color='lightgray', ecolor='gray')
    ax.set(title=title, xlabel=None, ylabel='Expense (€)')

    height = m_agg_df['Monthly_mean'].min() * 0.5
    for change, rect in zip(m_agg_df['Change'], ax.patches):
        color = 'red'
        if pd.isnull(change):
            change = ''
        else:
            if change > 0:
                color = 'green'
            change = f'{change * 100:1.0f}%'

        ax.text(rect.get_x() + rect.get_width() / 2.0, height, change, ha='center', va='bottom', color=color,
                weight='bold')

    display_df(m_agg_df, 'Monthly mean expenditure')


def viz_mean_daily_expense(agg_df: pd.DataFrame, title: str):
    plt.figure()
    ax = sns.lineplot(data=agg_df, x=Field.MONTH.value, y='daily_mean', palette="tab10",
                      hue=Field.YEAR.value, linewidth=2.5)
    ax.set(title=title)
    d_mean = agg_df['daily_mean'].mean()
    plt.axhline(d_mean, color='lightgray', linestyle='--')

    print(f'Average daily expense is: €{d_mean:2.2f}')


if __name__ == '__main__':
    DATE_FROM: str = '2020-12-04'
    DATE_TO: Union[str, None] = '2022-12-31'
    COELIAC_DATE: str = '2022-11-01'
    COELIAC_ADJ_AMOUNT: float = 65
    MONTHLY_BUDGET: float = 350
    FILEPATH: str = 'data/transactions_10.01.2023.csv'
    KEYWORDS_GROCERIES: list = [
        'haxix', 'pavi', 'lidl', 'crunchy', 'cherries', 'laham', 'kerubin', 'dave', 'master',
        'groceries', 'food', 'maypole', 'boucheri', 'emelda', 'convenience', 'miracle',
        'bacon', 'greens', 'mgarr', 'towers', 'spar', 'smart', 'Toiletries', 'bee'
    ]

    KEYWORDS_IGNORE: list = ['chairs']
    KEYWORDS_REMOVE: list = [' xirja', ' groceries', 'groceries \w', 'supermarket', ' luqa', ' qormi', ' \+ chinese']

    data_df = load_settleup_transactions(filepath=FILEPATH, date_from=str_to_date(DATE_FROM),
                                         date_to=str_to_date(DATE_TO))

    f_df = filter_df_groceries(data_df, on_column='Purpose', keywords=KEYWORDS_GROCERIES,
                               keywords_ignore=KEYWORDS_IGNORE, keywords_remove=KEYWORDS_REMOVE)

    f_df = coeliac_adjustment(f_df, str_to_date(COELIAC_DATE), c_adj_amount=COELIAC_ADJ_AMOUNT,
                              date_to=str_to_date(DATE_TO))

    # m_df = get_month_transactions(f_df, 10, 2021)

    agg_m_df = agg_monthly_expenses(f_df)

    agg_y_df = agg_yearly_expenses(f_df)

    # viz_agg_monthly_expenses(agg_m_df, budget=MONTHLY_BUDGET, title='Monthly expenditure on Groceries')

    viz_agg_expenditure_breakdown(f_df, title='Top 10: Groceries for 2022', top=10, year=2022)

    # viz_agg_yearly_expenses(f_df, 'Yearly total expense (€)')

    # viz_mean_monthly_expense(f_df, 'Mean monthly expense (€)')

    # viz_mean_daily_expense(agg_m_df, 'Mean daily expense (€)')

    plt.show()
