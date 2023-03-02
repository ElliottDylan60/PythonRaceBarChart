import bar_chart_race as bcr
import pandas as pd
df = pd.read_csv('test.csv')
bcr.bar_chart_race(
    df=df,
    filename='result.gif',
    orientation='h',
    sort='desc',
    n_bars=6,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    interpolate_period=False,
    label_bars=True,
    bar_size=.95,
    perpendicular_bar_func='median',
    period_length=500,
    figsize=(5, 3),
    dpi=300,
    cmap='dark12',
    title='COVID-19 Deaths by Country',
    title_size='',
    bar_label_size=7,
    tick_label_size=7,
    scale='linear',
    writer=None,
    fig=None,
    bar_kwargs={'alpha': .7},
    filter_column_colors=False)