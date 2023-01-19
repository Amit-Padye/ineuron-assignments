import os
import requests
from datetime import datetime, timedelta
import psycopg2
import os
import pandas as pd
import numpy

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36","Accept-Encoding": "identity"}

# Connection parameters
param_dic = {
    "host"      : "203.112.158.89",
    "database"  : "ratings",
    "user"      : "analytics",
    "password"  : "analytics"
}


def preprocess1(df):
    df = df.where(pd.notnull(df), None)
    desired_columns=['isin','securitytype','securitycode', 'issuename', 'issuedesc', 'issuedate', 'maturitydate', 'lastipdate', 'nextipdate', 'couponfrequency', 'lasttradeddate', 'lasttradedprice']
    df=df[['ISIN NO.','SECTYPE', 'SECURITY', 'ISSUE_NAME', 'ISSUE_DESC', 'ISSUE_DATE','MAT_DATE', 'Last IP Dt', 'Next IP Dt', 'Cpn Freq', 'Last Traded Date','Last Traded Price (in Rs.)']]
    df.columns=desired_columns
    return df


def preprocess2(df):
    required=['isin', 'tradedate', 'lasttradeprice', 'lasttradevalue', 'totaltradevalue', 'lasttradeytmannualized', 'weightedaverageprice', 'weightedaverageyield']
    df=df[['ISIN','Trade Date', 'Last Trade Price (in Rs.)','Last Trade Value (Rs. in lacs)', 'Total Trade Value (Rs. in lacs)','Last Trade Yield (YTM) (Annualized) (%)','Weighted Average Price  (Rs.)', 'Weighted Average Yield (YTM) (%)']]
    df.columns=required
    df=df.replace('-', numpy.NaN)
    return df
def preprocess3(df):
    required = ['isin', 'description', 'tradedate', 'quantity', 'nominalvalue', 'weightedaverageprice',
                'weightedaverageyield']

    df.columns = required
    return df



def add_to_database(reportid,path_of_data,params_dic):
    df = pd.read_csv(path_of_data)
    if reportid == 1:
        df = preprocess1(df)
    elif reportid == 2:
        df = preprocess2(df)
    else:
        df = preprocess3(df)

    #connecting to the data base
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params_dic)
        print("Connection successful")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(list(df.columns))
    if reportid == 1:
        table_name='wholesaledebtmarket'
        query = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)" % (
            table_name, cols)
    elif reportid == 2:
        table_name="corporatebondmarket"
        query = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)" % (
            table_name, cols)
    cursor = conn.cursor()

    try:
         cursor.executemany(query, tuples)
         # conn.commit()
         print("file added to data base")
    except (Exception, psycopg2.DatabaseError) as error:
         print("Error: %s" % error)
         conn.rollback()
         cursor.close()
         return 1
    print("execute_many() done")
    cursor.close()
    return 1


# function to download and file to database
def download_and_add_to_database(reportid,folder,fileinitial,filedateformat,part1,table_name,param_dic):
    # check file present or not

    try:
        currdate = datetime.today()
        year = currdate.strftime('%Y')
        month = currdate.strftime('%b').upper()
        todays_date = currdate.strftime(filedateformat)
        filename=fileinitial + todays_date + ".csv"
        if reportid==1:
            print('amit')
            url = part1 + year + '/' + month + '/' + filename

        else:
            url = part1 + filename

        if not os.path.isfile(folder+filename):
            response = requests.get(url,verify=False,headers=headers)
            if response.reason =="OK":
                with open(folder + filename, 'wb') as f:
                    f.write(response.content)
                    print('File downloaded')
                path_of_data = folder + filename
                add_to_database(reportid,path_of_data,param_dic)

            else:
                for day in range(1,5):
                    date = currdate - timedelta(days=day)
                    year = date.strftime('%Y')
                    month = date.strftime('%b').upper()
                    todays_date = date.strftime(filedateformat)
                    filename = fileinitial + todays_date + ".csv"
                    if not os.path.isfile(folder + filename):
                        if reportid == 1:
                            url = part1 + year + '/' + month + '/' + filename
                        else:
                            url = part1 + filename

                        response = requests.get(url,verify=False,headers=headers)
                        if response.reason == "OK":
                            with open(folder + filename, 'wb') as f:
                                f.write(response.content)
                                print('File downloaded')

                            path_of_data = folder + filename
                            add_to_database(reportid, path_of_data, param_dic)
                            break
                    else:
                        break

    except (Exception) as e:
         print("New file not available")


folder="C:/webscraping/"


part1 = 'https://archives.nseindia.com/archives/debt/cbm/'
fileinitial="cbm_trd"
filedateformat="%Y%m%d"
table_name="corporatebondmarket"
download_and_add_to_database(2,folder,fileinitial,filedateformat,part1,table_name,param_dic)

# part1 = 'https://archives.nseindia.com/archives/debt/cbm/'
# fileinitial="GSEC_SettlementOrderReport_"
# filedateformat="%d%m%Y"
# table_name="gsecsettlementorder"
# download_and_add_to_database(3,folder,fileinitial,filedateformat,part1,table_name,param_dic)


