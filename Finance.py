import yfinance as yf
import pandas as pd
import csv
import warnings
import time
import os
import tkinter as tk
import tkinter.font as font
from threading import Thread
from requests import exceptions
from PIL import ImageTk, Image
import mplfinance as mplf
from tempfile import NamedTemporaryFile
import shutil
import sec_api as sapi
from fredapi import Fred

class InfiniteLoopError(Exception): pass
class KillException(Exception): pass
class ExtractionError(Exception): pass
class NoData(Exception): pass

def reconnect():
    name_of_router = 'BHNTG1682G03A2'
    os.system(f'''cmd /c "netsh wlan connect name={name_of_router}"''')

def getData(var, row, col, op=0):
    if type(row) == int:
        return(var.iloc[row][col])
    else:
        if len(var[var.Date == row.strftime('%Y-%m-%d')][col].tolist()) != 0:
            return(var[var.Date == row.strftime('%Y-%m-%d')][col].tolist()[0])
        else:
            cntr = 0
            while len(var[var.Date == row.strftime('%Y-%m-%d')][col].tolist()) == 0:
                if op==0:
                    row = row - pd.Timedelta(days=1)
                elif op == 1:
                    row = row + pd.Timedelta(days=1)
                else:
                    raise NoData 
                cntr += 1
                if cntr == 10:
                    raise InfiniteLoopError('Loop ran too long.')
            return(var[var.Date == row.strftime('%Y-%m-%d')][col].tolist()[0])

def getFredData():
    today = pd.Timestamp.today() - pd.Timedelta(days = 1)
    global fgdp
    global fcpi
    global fer
    global fuer
    global ftbi
    global fisr
    global fppi
    fred = Fred(api_key='8a97da7c44f4237c0e2d9090d5712211')
    fgdp = fred.get_series_as_of_date('GDP', today)
    fcpi = fred.get_series_as_of_date('CORESTICKM159SFRBATL', today)
    fer = fred.get_series_as_of_date('LREM64TTUSM156S', today)
    fuer = fred.get_series_as_of_date('UNRATE', today)
    ftbi = fred.get_series_as_of_date('BUSINV', today)
    fisr = fred.get_series_as_of_date('ISRATIO', today)
    fppi = fred.get_series_as_of_date('PPIACO', today)
            
class Sorter():
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=UserWarning)

    global sortStop
    sortStop = False

    delta1D = pd.Timedelta(days=1)
    delta2D = pd.Timedelta(days=2)
    delta1W = pd.Timedelta(days=7)
    delta13W = pd.Timedelta(days=91)
    delta1M = pd.Timedelta(days=28)
    delta2Y = pd.Timedelta(days=364)
    today = pd.Timestamp.today()
    latest = today - delta2Y
    histories = {}
    infos = {}
    lastTckr = ''
    tckrRtrns = 0

    def __init__(self):
                
        def tFilter(tckr):
            hst = self.histories[tckr]
            info = self.infos[tckr]
            if len(hst) == 0:
                return(False)
            elif getData(hst, 0, 'Date') > self.latest:
                return(False)        
            elif getRecom(tckr) != True:
                return(False)
            elif getPAD(hst) != True:
                return(False)
            elif getInfo(info) != True:
                return(False)  
            elif getReturns(hst) != True:
                return(False)
            else:
                return(True)
            
        def getInfo(info):
            cntr = 0
            try:
                if info['profitMargins'] > .12:
                    cntr += 1
            except TypeError:
                pass
            try:
                if info['operatingMargins'] > .15:
                    cntr += 1
            except TypeError:
                pass
            try:
                if info['ebitdaMargins'] > .15:
                    cntr += 1
            except TypeError:
                pass
            try:
                if info['returnOnAssets'] >= .15:
                    cntr += 1
            except TypeError:
                pass
            try:
                if info['marketCap'] >= 2000000000:
                    cntr += 1
            except TypeError:
                pass
            if cntr >= 3:
                return(True)
            else:
                return(False)
                
        def getReturns(hst):
            global tckrRtrns
            dates = []
            dt1 = self.latest
            dt2 = self.latest + self.delta13W
            while dt2 < self.today:
                dates.append([dt1, dt2])
                dt1 = dt2 + self.delta1D
                dt2 = dt1 + self.delta13W
            dates.append([dt1, self.today])
            returns = []
            for i in range(len(dates)):
                dt1 = dates[i][0]
                dt2 = dates[i][1]
                frst = getData(hst, dt1, 'Open', 1)
                scnd = getData(hst, dt2, 'Close')
                diff = scnd - frst
                returns.append((diff/frst)*100)
            rtrns = sum(returns)/len(returns)
            if rtrns >= 10.0:
                tckrRtrns = str(rtrns)
                return(True)
            else:
                return(False)

        def getRecom(tckr):
            recoms = tckr.recommendations
            if recoms is not None:
                recoms.reset_index(inplace = True)
                if getData(recoms, (len(recoms) - 1), 'Date') > (self.today - self.delta1M):
                    recom = getData(recoms, (len(recoms) - 1), 'To Grade')
                    if 'Buy' in recom or recom == 'Overweight':
                        return(True)
                    else:
                        return(False)
                else:
                    return(False)
            else:
                return(False)

        def getPAD(hst):
            if hst['Close'].mad(0)/hst['Close'].mean(0) > .40:
                return(False)
            else:
                return(True)

        #def reconnect():
        #    name_of_router = 'BHNTG1682G03A2'
        #    os.system(f'''cmd /c "netsh wlan connect name={name_of_router}"''')

        def resort():
            time.sleep(30)
            tf = NamedTemporaryFile('a+', newline='', encoding='utf-8', delete=False)
            writer = csv.writer(tf)
            while (tl.is_alive() or len(self.histories) != 0) and sortStop != True:
                try:
                    tckr = list(self.histories)[0]
                    hst = self.histories[tckr]
                    info = self.infos[tckr]
                    infoPassorNot = getInfo(self.infos[tckr])
                    getReturns(hst)
                    recom = getRecom(tckr)
                    writer.writerow([info['symbol'], tckrRtrns, recom])
                    hst = hst.set_index('Date')
                    mplf.plot(hst, type='line', style='nightclouds', savefig='graphs\\'+info['symbol']+'.png')
                    tSymbols[info['symbol']].graph = ImageTk.PhotoImage(Image.open('graphs\\'+info['symbol']+'.png'))
                    self.histories.pop(tckr)
                except KeyError:
                    time.sleep(60)
                    continue
                except exceptions.ConnectionError:
                    time.sleep(60)
                    reconnect()
                    continue
                except exceptions.ChunkedEncodingError:
                    time.sleep(60)
                    reconnect()
                    continue
            tf.close()
            shutil.move(tf.name, 'symbols.csv')
            raise KillException('Sorting has stopped.')
                    
                    
        def sort():
            time.sleep(30)
            while (tl.is_alive() or len(self.histories) != 0) and sortStop != True:
                try:
                    tckr = list(self.histories)[0]
                    info = self.infos[tckr]
                    if info['symbol'] not in tckrSymbols and tFilter(tckr) == True:
                        with open('symbols.csv', 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([info['symbol'],tckrRtrns, True])
                            hst = hst.set_index('Date')
                            mplf.plot(hst, type='line', style='nightclouds', savefig='graphs\\'+info['symbol']+'.png')
                        tckrSymbols.append(info['symbol'])
                        tSymbols[info['symbol']] = Symbol(info['symbol'])
                        tckrList.insert('end', tk.StringVar(info['symbol']))
                    self.histories.pop(tckr)
                    self.lastTckr = info['symbol']
                    with open('lastTicker.txt', 'w') as ft:
                        ft.write(self.lastTckr)
                except KeyError:
                    time.sleep(60)
                    continue
                except exceptions.ConnectionError:
                    time.sleep(60)
                    reconnect()
                    continue
                except exceptions.ChunkedEncodingError:
                    time.sleep(60)
                    reconnect()
                    continue
            raise KillException('Sorting has stopped.')

        def load():
            if self.latest.isoweekday() == 6:
                self.latest = self.latest - self.delta1D
            elif self.latest.isoweekday() == 7:
                self.latest = self.latest - self.delta2D
            if self.today.isoweekday() == 6:
                self.today = self.today - self.delta1D
            elif self.today.isoweekday() == 7:
                self.today = self.today - self.delta2D
            reader = csv.reader(loadFile)
            ln = reader.__next__()
            if loadFile.name != 'symbols.csv':
                with open('lastTicker.txt', 'r') as ft:
                    self.lastTckr = ft.readline()
                if self.lastTckr == '':
                    ln = reader.__next__()
                else:
                    while self.lastTckr not in ln:
                        ln = reader.__next__()
            while sortStop != True:
                try:
                    tsymb = ln[0]
                    tckr = yf.Ticker(tsymb)
                    hst = tckr.history(start=self.latest.strftime('%Y-%m-%d'))
                    hst.reset_index(inplace=True)
                    self.histories[tckr] = hst
                    info = tckr.info
                    self.infos[tckr] = info
                    ln = reader.__next__()
                except StopIteration:
                    raise KillException('Loading has stopped.')
                except exceptions.ConnectionError:
                    time.sleep(60)
                    reconnect()
                    continue
                except exceptions.ChunkedEncodingError:
                    time.sleep(60)
                    reconnect()
                    continue

        global tl
        loadFile = open(loadFileName, 'r')
        tl = Thread(target=load, args=())
        if loadFile.name == 'symbols.csv':
            ts = Thread(target=resort, args=())
        else:
            ts = Thread(target=sort, args=())
        tl.start()
        ts.start()

class Microanalysis:
    delta1D = pd.Timedelta(days=1)
    delta13W = pd.Timedelta(days=91)
    #delta14W = pd.Timedelta(days=98)
    #delta1Y = pd.Timedelta(days=364)
    delta1Y1W = pd.Timedelta(days=371)
    delta5Y = pd.Timedelta(days=1820)
    today = pd.Timestamp.today() - delta1D

    def __init__(self, tsymb):
        tckr = yf.Ticker(tsymb)
        hst = tckr.history(period='max')
        hst.reset_index(inplace=True)
        info = tckr.info

        def orderPeriods():
            dates = []
            dt1 = getData(hst, 0, 'Date', op=1)
            dt2 = dt1 + self.delta13W
            while dt2 < self.today:
                dates.append([dt1, dt2])
                dt1 = dt2 + self.delta1D
                dt2 = dt1 + self.delta13W
            dates.append([dt1, getData(hst, len(hst)-1, 'Date')])

            temp = []
            for i in range(len(dates)):
                dt1 = dates[i][0]
                dt2 = dates[i][1]
                date = dt1
                total = 0
                cntr = 0
                while date < dt2:
                    try:
                        frst = getData(hst, date, 'Open')
                        scnd = getData(hst, date+self.delta1D, 'Close', 3)
                        total += (scnd - frst) / frst
                        cntr += 1
                        date += self.delta1D
                    except NoData:
                        date += self.delta1D
                        continue
                    except ZeroDivisionError:
                        date += self.delta1D
                        continue
                try:
                    avg = total / cntr
                except ZeroDivisionError:
                    continue
                temp.append([dt1, dt2, avg])

            periodsGrowth = []
            periodsSustained = []
            periodsDecreased = []
            for i in range(len(temp)):
                if temp[i][2] >= .00105:
                    periodsGrowth.append(temp[i])
                elif .00105 > temp[i][2] >= 0:
                    periodsSustained.append(temp[i])
                else:
                    periodsDecreased.append(temp[i])

            periods = [periodsGrowth, periodsSustained, periodsDecreased]
            
            return(periods)

        # convert XBRL-JSON of income statement to pandas dataframe
        def getStatements(xbrl_json):
            statement_store = {}

            sectionsToSearch = ['StatementsOfIncome', 'BalanceSheets', 'StatementsOfCashFlows', 'StatementsOfShareholdersEquity']
            for x in xbrl_json:
                if x in sectionsToSearch:
            # iterate over each US GAAP item in the income statement
                    for usGaapItem in xbrl_json[x]:
                        values = []
                        indicies = []

                        for fact in xbrl_json[x][usGaapItem]:
                            # only consider items without segment. not required for our analysis.
                            if 'segment' not in fact:
                                try:
                                    index = pd.Timestamp(fact['period']['endDate'])
                                except KeyError: 
                                    index = pd.Timestamp(fact['period']['instant'])
                                except TypeError:
                                    continue
                                # ensure no index duplicates are created
                                if index not in indicies:
                                    try:
                                        values.append(float(fact['value']))
                                        indicies.append(index)
                                    except KeyError:
                                        continue                    

                        statement_store[usGaapItem] = pd.Series(values, index=indicies) 

            income_statement = pd.DataFrame(statement_store)
            # switch columns and rows so that US GAAP items are rows and each column header represents a date range
            return income_statement.T 
                
        def extract10Q():
            try:
                periods = orderPeriods()
            except IndexError:
                raise ExtractionError
            extractedGrowth = []
            extractedSustained = []
            extractedDecreased = []
            for i in periods:
                for p in i:
                    qapi = sapi.QueryApi(api_key='c87550c43b2a4bebba0394193f67e3fbc487a5a8a444370e0749c83c5c22b9dd')
                    query = {
                        "query": { "query_string": { 
                            "query": "ticker:" + tsymb +  " AND filedAt:{"+(p[0]).strftime('%Y-%m-%d')+" TO "+p[1].strftime('%Y-%m-%d')+"} AND formType:\"10-Q\"" 
                            } },
                        "from": "0",
                        "size": "1",
                        "sort": [{ "filedAt": { "order": "desc" } }]
                        }
                    filings10Q = qapi.get_filings(query)

                    if filings10Q['total']['value'] == 0:
                        continue
                    else:
                        accessionNo = filings10Q['filings'][0]['accessionNo']
                        xapi = sapi.XbrlApi(api_key='c87550c43b2a4bebba0394193f67e3fbc487a5a8a444370e0749c83c5c22b9dd')
                        x2j = xapi.xbrl_to_json(accession_no=accessionNo)


                    df = getStatements(x2j)
                    filedAt = filings10Q['filings'][0]['filedAt']
                    if df.empty:
                        continue
                    elif i == periods[0]:
                        extractedGrowth.append([df, filedAt])
                    elif i == periods[1]:
                        extractedSustained.append([df, filedAt])
                    elif i == periods[2]:
                        extractedDecreased.append([df, filedAt])

            extracted = [extractedGrowth, extractedSustained, extractedDecreased]
            return(extracted)

        def analyze(df):

            try:
                p2B = []
                for i in df.columns:
                    assets = df.loc['Assets'][i]
                    liabilities = df.loc['Liabilities'][i]
                    book = assets - liabilities
                    try:
                        sharesOutstanding = df.loc['WeightedAverageNumberOfSharesOutstandingBasic'][i]
                    except KeyError:
                        sharesOutstanding = df.loc['SharesOutstanding'][i]
                    bookValue = book / sharesOutstanding
                    price = getData(hst, pd.Timestamp(i), 'Close', op=1)
                    p2B.append(price / bookValue)
                df.loc['PriceToBookRatio'] = p2B
            except KeyError:
                pass
            except InfiniteLoopError:
                pass
            
            try:
                p2E = []
                for i in df.columns:
                    earnings = df.loc['EarningsPerShareBasic'][i]
                    price = getData(hst, pd.Timestamp(i), 'Close', op=1)
                    p2E.append(price / earnings)
                df.loc['PriceToQuarterlyEarningsRatio'] = p2E
            except KeyError:
                pass
            except InfiniteLoopError:
                pass

            try:
                d2E = []
                for i in df.columns:
                    liabilities = df.loc['Liabilities'][i]
                    equity = df.loc['StockholdersEquity'][i]
                    d2E.append(liabilities / equity)
                df.loc['DebtToEquityRatio'] = d2E
            except KeyError:
                pass

            gdp = []
            cpi = []
            er = []
            uer = []
            tbi = []
            isr = []
            ppi = []
            for d in df.columns:
                date = d

                try:
                    i = 0
                    while not (fgdp.iloc[i]['date'] <= pd.Timestamp(date) < fgdp.iloc[i+1]['date']): i+=1
                    gdp.append(fgdp.iloc[i]['value'])
                except IndexError:
                    gdp.append(fgdp.iloc[len(fgdp)-1]['value'])

                try:
                    i = 0
                    while not (fcpi.iloc[i]['date'] <= pd.Timestamp(date) < fcpi.iloc[i+1]['date']): i+=1
                    cpi.append(fcpi.iloc[i]['value'])
                except IndexError:
                    cpi.append(fcpi.iloc[len(fcpi)-1]['value'])

                try:
                    i = 0
                    while not (fer.iloc[i]['date'] <= pd.Timestamp(date) < fer.iloc[i+1]['date']): i+=1
                    er.append(fer.iloc[i]['value'])
                except IndexError:
                    er.append(fer.iloc[len(fer)-1]['value'])

                try:
                    i = 0
                    while not (fuer.iloc[i]['date'] <= pd.Timestamp(date) < fuer.iloc[i+1]['date']): i+=1
                    uer.append(fuer.iloc[i]['value'])
                except IndexError:
                    uer.append(fuer.iloc[len(fuer)-1]['value'])

                try:
                    i = 0
                    while not (ftbi.iloc[i]['date'] <= pd.Timestamp(date) < ftbi.iloc[i+1]['date']): i+=1
                    tbi.append(ftbi.iloc[i]['value'])
                except IndexError:
                    tbi.append(ftbi.iloc[len(ftbi)-1]['value'])

                try:
                    i = 0
                    while not (fisr.iloc[i]['date'] <= pd.Timestamp(date) < fisr.iloc[i+1]['date']): i+=1
                    isr.append(fisr.iloc[i]['value'])
                except IndexError:
                    isr.append(fisr.iloc[len(fisr)-1]['value'])

                try:
                    i = 0
                    while not (fppi.iloc[i]['date'] <= pd.Timestamp(date) < fppi.iloc[i+1]['date']): i+=1
                    ppi.append(fppi.iloc[i]['value'])
                except IndexError:
                    ppi.append(fppi.iloc[len(fppi)-1]['value'])

            df.loc['GDP'] = gdp
            df.loc['CPI'] = cpi
            df.loc['EmploymentRate'] = er
            df.loc['UnemploymentRate'] = uer
            df.loc['TotalBusinessInventories'] = tbi
            df.loc['InventoriesToSalesRatio'] = isr
            df.loc['PPI'] = ppi

            avg = df.mean(1)
            avgDev = df.mad(1)
            df = df.assign(Average = avg)
            df = df.assign(AverageDeviation = avgDev)
            df = df.assign(PercentDeviation = df['AverageDeviation']/df['Average'])

            return(df)

        def writeCSVs(extracted):
            try: os.mkdir('predict_data\\'+info['sector'])
            except FileExistsError:
                pass
            try:
                os.mkdir('predict_data\\'+info['sector']+'\\'+tsymb)
            except FileExistsError:
                pass
            try:
                os.mkdir('predict_data\\'+info['sector']+'\\'+tsymb+'\\Growth')
            except FileExistsError:
                pass
            try:
                os.mkdir('predict_data\\'+info['sector']+'\\'+tsymb+'\\Sustained')
            except FileExistsError:
                pass
            try:
                os.mkdir('predict_data\\'+info['sector']+'\\'+tsymb+'\\Decreased')
            except FileExistsError:
                pass
                
            for e in extracted:
                for df in e:
                    try:
                        if e == extracted[0]:
                            df[0].to_csv('predict_data\\'+info['sector']+'\\'+tsymb+'\\Growth\\'+df[1][0:10]+'.csv', encoding='utf-8')
                        elif e == extracted[1]:
                            df[0].to_csv('predict_data\\'+info['sector']+'\\'+tsymb+'\\Sustained\\'+df[1][0:10]+'.csv', encoding='utf-8')
                        else:
                            df[0].to_csv('predict_data\\'+info['sector']+'\\'+tsymb+'\\Decreased\\'+df[1][0:10]+'.csv', encoding='utf-8')
                    except ValueError:
                        continue

        try:
            print('Extracting...')
            extracted = extract10Q()
            temp = [[],[],[]]
            for e in range(3):
                for i in range(len(extracted[e])):
                    print('Analyzing...')         
                    temp[e].append([analyze(extracted[e][i][0]),extracted[e][i][1]])
            extracted = temp
            print('Writing...')
            try:
                writeCSVs(extracted)
            except KeyError:
                pass
        except ExtractionError:
            pass
                        
class Symbol:
    def __init__(self, name):
        self.name = name
        self.graph = ImageTk.PhotoImage(Image.open('graphs\\'+name+'.png'))
    

class GUI:
    def __init__(self):
        def beginSort():
            startButton.place_forget()
            stopButton.place(rely=1.0, relx=1.0, x=0, y=0, anchor='se', relwidth=.125, relheight=.05)
            s = Sorter()
        
        def stopSort():
            global sortStop
            stopButton.place_forget()
            startButton.place(rely=1.0, relx=1.0, x=0, y=0, anchor='se', relwidth=.125, relheight=.05)
            sortStop = True

        def getSymbols():
            symbols = []
            with open('symbols.csv', 'r') as f:
                reader = csv.reader(f)
                try:
                    while True:
                        symbols.append(reader.__next__()[0])
                except StopIteration:
                    pass
            return(symbols)

        def displayInfo(event):
            tckr = tSymbols[tckrList.get(tckrList.curselection())]
            graph = tckr.graph
            graphLabel.config(image=graph)

        def setAction(event):
            global loadFileName
            if actionList.get(actionList.curselection()) == 'Stocks':
                loadFileName = 'stocks.csv'
            else:
                loadFileName = 'symbols.csv'
            print(loadFileName)
        
        window = tk.Tk(
            )
        window.state('zoomed')
        window.config(
            bg = 'black')

        graphLabel = tk.Label(
            window,
            bg='black'
        )
            

        arial = font.Font(
            size=14
        )

        global tckrSymbols
        global tSymbols
        global tckrList
        tckrSymbols = getSymbols()
        tSymbols = {}
        for s in tckrSymbols:
            tSymbols[s] = Symbol(s)
        tckrSymbolsList = tk.StringVar(value=tckrSymbols)
        tckrList = tk.Listbox(
            window,
            listvariable=tckrSymbolsList,
            bg='black',
            fg='white',
        )
        tckrList.bind('<<ListboxSelect>>', displayInfo)

        actions = tk.StringVar(value=['Stocks','Check Symbols'])
        actionList = tk.Listbox(
            window,
            listvariable=actions,
            bg='black',
            fg='white',
        )
        actionList.bind('<<ListboxSelect>>', setAction)
        
        startButton = tk.Button(
            window,
            text='Begin Sort',
            font = arial,
            bg='black',
            fg='white',
            command=beginSort
        )

        stopButton = tk.Button(
            window,
            text='Stop Sort',
            font = arial,
            bg='black',
            fg='white',
            command=stopSort
        )
        
        startButton.place(rely=1.0, relx=1.0, x=0, y=0, anchor='se', relwidth=.125, relheight=.05)
        graphLabel.place(rely=0.0, relx=0.0, x=0, y=0, anchor='nw', width=800, height=575)
        tckrList.place(rely=0.0, relx=1.0, x=0, y=0, anchor='ne', relwidth=.125, relheight=.85)
        actionList.place(rely=.85, relx=1.0, x=0, y=0, anchor='ne', relwidth=.125, relheight=.10)
        window.mainloop()
        
def scrape():
    getFredData()
    with open('stocks.csv', mode='r') as f:
        reader = csv.reader(f)
        ln = reader.__next__()
        with open('last_tckr_predict.txt') as ft:
            lastTicker = ft.readline()
        if lastTicker == '':
            ln = reader.__next__()
        else:
            while ln[0] != lastTicker:
                ln = reader.__next__()
        while True:
            try:
                ln = reader.__next__()
                tsymb = ln[0]
                print('Scraping...')
                micro = Microanalysis(tsymb)
                with open('last_tckr_predict.txt', mode='w') as fw:
                    fw.write(tsymb)
            except StopIteration:
                break

def main():
    g = GUI()
    #scrape()

def createSymbols():
    symbols = []
    with open('symbols.csv', 'r') as f:
        reader = csv.reader(f)
        try:
            while True:
                symbols.append(reader.__next__()[0])
        except StopIteration:
            pass
    for s in symbols:
        tckr = yf.Ticker(s)
        hst = tckr.history(period='2y')
        mplf.plot(hst, type='line', style='nightclouds', savefig='graphs\\'+s+'.png')
        

if __name__ == '__main__':
    main()
