
# coding: utf-8

# In[305]:

import pandas as pd
import datetime
import pyodbc

server = 'quesqlsrv.database.windows.net'
database = 'GEUDB'
username = 'volmodadmin'
password = 'S@nd50fT!m3!'
driver= '{SQL Server}'
cnxn = pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1443;DATABASE={database};UID={username};PWD={password}')
cursor = cnxn.cursor()


# In[306]:

def generate_time_series(time_adder):
    dt = datetime.datetime(2039,1,1, 0,0,0)
    end = datetime.datetime(2044,1,1, 1,0,0)
    step = datetime.timedelta(hours= time_adder)

    time_series = []
    while dt < end:
        time_series.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
        dt += step

    return time_series


# In[340]:

# get hourly prices,
hourly_price_df = pd.read_csv("GenOn_hourly_prices_2038_input for extension - mid CLCPA.csv")
hourly_price_columns = hourly_price_df.columns
hub_names = hourly_price_columns[2:]


# In[341]:

unpiv_hourly_price_df = pd.melt(hourly_price_df, id_vars=['MonthD','Hour'], value_vars=hub_names)
unpiv_hourly_price_df['MonthD'] = pd.to_datetime(unpiv_hourly_price_df['MonthD'])
unpiv_hourly_price_df['Hour'] = unpiv_hourly_price_df.MonthD.dt.hour
unpiv_hourly_price_df['DOW']  = unpiv_hourly_price_df.MonthD.dt.dayofweek


# In[342]:

sql_statement_hour_logic = str("SELECT Case When [Hour_Type] in (1,3) then 'Off' else 'On' end as Hour_Type, Case When Day_of_Week = 1 then 6 When Day_of_Week = 2 then 0When Day_of_Week = 3 then 1 When Day_of_Week = 4 then 2 When Day_of_Week = 5 then 3 When Day_of_Week = 6 then 4 When Day_of_Week = 7 then 5 else 9 end as DOW ,[Day_Of_Week] ,[Hour_Ending] FROM [PA_Utilities].[ISO_Hour_Logic] Where ISO_Name = 'New York ISO'")
hour_logic_df = pd.read_sql(sql_statement_hour_logic, cnxn)


# In[343]:

final_df = pd.merge(unpiv_hourly_price_df,hour_logic_df,left_on=['DOW','Hour'],right_on=['DOW','Hour_Ending'])


# In[344]:

final_df['date']  = final_df.MonthD.dt.date
final_df['date'] = final_df['date'].values.astype('datetime64[M]')
final_df['date'] = pd.to_datetime(final_df['date'])


# In[345]:

monthly_values = pd.read_csv("GenOn_monthly forecasts_input for extension.csv")


# In[346]:

final_df['hub_on_off'] = final_df['variable'] + " " + final_df['Hour_Type']


# In[347]:

unpiv_monthly_price_df = pd.melt(monthly_values, id_vars=['MonthD'], value_vars=monthly_values.columns[1:])


# In[348]:

unpiv_monthly_price_df['MonthD'] = pd.to_datetime(unpiv_monthly_price_df['MonthD'])
unpiv_monthly_price_df['date']  = unpiv_monthly_price_df.MonthD.dt.date


# In[349]:

final_full_df = pd.merge(final_df,unpiv_monthly_price_df,left_on=['hub_on_off','date'],right_on=['variable','MonthD'])


# In[ ]:




# In[350]:

final_full_df['hourly_ratio'] = final_full_df['value_x'] / final_full_df['value_y']


# In[351]:

df_to_use_for_cals = final_full_df[['MonthD_y','Hour','DOW','Hour_Type','Hour_Ending','hub_on_off','value_y','hourly_ratio']]


# In[352]:

averages_df = df_to_use_for_cals.groupby(['MonthD_y','Hour','DOW','Hour_Type','Hour_Ending','hub_on_off','value_y'],as_index=False)['hourly_ratio'].mean()


# In[353]:

full_time_series = generate_time_series(1)
full_dates_df = pd.DataFrame({'Hourly_TS': full_time_series})
full_dates_df['Hourly_TS'] = pd.to_datetime(full_dates_df['Hourly_TS'])


# In[354]:

full_dates_df['Hour'] = full_dates_df.Hourly_TS.dt.hour
full_dates_df['DOW']  = full_dates_df.Hourly_TS.dt.dayofweek
full_dates_df['date']  = full_dates_df.Hourly_TS.dt.date
full_dates_df['date'] = full_dates_df['date'].values.astype('datetime64[M]')
full_dates_df['month']  = full_dates_df.Hourly_TS.dt.month
averages_df['month'] = averages_df.MonthD_y.dt.month


# In[355]:

test_df = pd.merge(full_dates_df,averages_df, left_on=['DOW','Hour','month'],right_on=['DOW','Hour_Ending','month'])


# In[ ]:




# In[356]:

final_full = pd.merge(test_df,unpiv_monthly_price_df, left_on =['date','hub_on_off'],right_on=['MonthD','variable'])


# In[357]:

final_full.variable.unique()


# In[358]:

final_full['Price'] = final_full['value'] * final_full['hourly_ratio']


# In[359]:

final_full.head()


# In[360]:

final_full_averages = final_full.groupby(['hub_on_off','date_y','value'],as_index=False)['Price'].mean()


# In[361]:

final_full_averages


# In[362]:

final_full_averages['shift_ratio'] = final_full_averages['value']/final_full_averages['Price']


# In[363]:

final_full_averages.hub_on_off.unique()


# In[364]:

hourly_final_df = pd.merge(final_full, final_full_averages, left_on=['date_y','hub_on_off'], right_on=['date_y','hub_on_off'])


# In[365]:

hourly_final_df.head()


# In[366]:

hourly_final_df['Final_Price'] = hourly_final_df['Price_x'] * hourly_final_df['shift_ratio']


# In[367]:

hourly_final_df.head()


# In[372]:

to_export = hourly_final_df[['Hourly_TS','hub_on_off','Final_Price']]


# In[378]:

to_export.groupby(['hub_on_off']).agg(['count'])


# In[375]:

to_export.to_csv('GenOn_test_hourlies.csv')


# In[ ]:
