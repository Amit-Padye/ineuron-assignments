import requests
import pandas as pd
import io,sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import AppConfig
sys.path.insert(0, AppConfig.commonclass)
import ErrorLogger
from CommonClass import clsCommonClass

# user_agent = 'Mozilla/5.0 (Macintosh; Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36","Accept-Encoding": "identity"}
#
cc=clsCommonClass()
conn = cc.dbconnect('ratings')

links = 'https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69?api-key=579b464db66ec23bdd000001797e50c7f0f04b1b6da4b9a75cbd4755&format=csv&limit=9999'
#links = 'https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69?api-key=579b464db66ec23bdd000001797e50c7f0f04b1b6da4b9a75cbd4755&format=csv'
urlData = requests.get(links, verify=False, headers=headers).content
df = pd.read_csv(io.StringIO(urlData.decode('utf-8')))
print(df)
df = df.drop(['id', 'country'], axis=1)
df['last_update'] = pd.to_datetime(df['last_update'], yearfirst=True)
dates = df['last_update'][0]
dates = str(dates)

df.columns = ['state', 'city', 'station', 'date', 'pollutant_id',
              'pollutant_minimum', 'pollutant_maximum', 'pollutant_average',
              'pollutant_unit']

query = "SELECT * FROM tblairqualityindex where date = '" + dates + "'"
data = pd.read_sql_query(query, con=conn)
try:
    if data.empty:
        cursor = conn.cursor()
        tuples = [tuple(x) for x in df.to_numpy()]
        cols = ','.join(list(df.columns))
        table_name = 'tblairqualityindex'
        query = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)" % (
            table_name, cols)

        cursor.executemany(query, tuples)
        # conn.commit()
        #print("Data Added", dates)
        ErrorLogger.logger.error('Data Added on {}'.format(dates))
except Exception as e:
    ErrorLogger.logger.error('Process  error: {}'.format(e.args[0]))
