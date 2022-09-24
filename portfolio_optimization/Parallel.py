import yfinance as yf
import pandas as pd
import numpy as np
import os
from os import walk
from multiprocessing import Pool
import json

#in_ can be a text file or a list of assets
#out_ can be a parquet file or None. If it is a file it will write the results to out file, other the results are returned
def descargar(in_,out_):
    if type(in_) is str:
        x=open(in_, "r")
        s=x.read().splitlines()[1:]
    else:
        s=in_
    data = yf.download(
        tickers = s,
        interval = '1d',prepost=False
    )
    prices = data['Adj Close'].sort_index()
    prices.drop(prices.tail(1).index,inplace=True)
    s=prices[prices.notnull()].count()
    l=s.where(s==0).dropna().index
    t=prices.drop(l,axis=1)
    if type(out_) is str:
        t.sort_index().to_parquet(out_)
        return 0
    else:
        return t.sort_index()
#in_ can be a text file or a pandas table returned by descargar
#out_ can be a parquet file or None. If it is a file it will write the results to out file, other the results are returned
def rends(in_,out_):
    if type(in_) is str:
        prices=pd.read_parquet(in_)
    else:
        prices=in_    
    rend=np.log(prices/prices.shift(1))
    rend.replace(np.inf, np.nan)
    if type(out_) is str:
        rend.to_parquet(out_)
        return 0
    else:
        return rend
#in_ can be a text file or a pandas table returned by descargar or rends
#out_ can be a parquet file or None. If it is a file it will write the results to out file, other the results are returned
#alpha is the decay factor
def EWM(in_,out_,alpha):
    if type(in_) is str:
        df=pd.read_parquet(in_)
    else:
        df=in_
    
    df1=pd.DataFrame(index=df.index,columns=df.columns)
    for c in df.columns:
        d=np.array(df[c])
        t=np.full(len(d),np.nan)
        for i in range(1,len(d)):
            if(np.isnan(t[i-1] )):
                t[i]=d[i-1]
            elif(np.isnan(d[i-1])):
                t[i]=t[i-1]
            else:
                t[i]=alpha*d[i-1]+(1-alpha)*t[i-1]
        df1[c]=t
    if type(out_) is str:
        df1.to_parquet(out_)
        return 0
    else:
        return df1
#in_ can be a text file or a pandas table returned by descargar or rends
#out_ can be a parquet file or None. If it is a file it will write the results to out file, other the results are returned    
def cov(in_,out_):
    if type(in_) is str:
        df=pd.read_parquet(in_).sort_index()
    else:
        df=in_
    if type(out_) is str:
        df.cov().to_parquet(out_)
        return 0
    else:
        return df.cov()
    
    
    
def prepare_tree():
    if os.path.isdir('Data/') == False:
        os.mkdir('Data')
    if os.path.isdir('Data/Parquet/') == False:
        os.mkdir('Data/Parquet')
    if os.path.isdir('Data/Rends/') == False:
        os.mkdir('Data/Rends')
    if os.path.isdir('Data/Covs/') == False:
        os.mkdir('Data/Covs')
    if os.path.isdir('Data/EWM/') == False:
        os.mkdir('Data/EWM')
def get_dataset(dataset,alpha):
    path_in='Data/Text/'+dataset+'.txt'
    path_parquet='Data/Parquet/'+dataset
    path_rends='Data/Rends/'+dataset
    path_cov='Data/Covs/'+dataset
    path_ewm='Data/EWM/'+dataset
    descargar(path_in,path_parquet)
    rends(path_parquet,path_rends)
    cov(path_rends,path_cov)
    EWM(path_rends,path_ewm,alpha)
    
def generateJSON(dataset,date,budget):
    path='./Data/'
    df=pd.read_parquet(path+'EWM/'+dataset)
    data={}
    data['rends']=list(np.array(df.loc[[date]])[0])
    data['current']=list(np.zeros(len(data['rends'])))
    data['cost']=list(np.zeros(len(data['rends'])))
    data['cov']=pd.read_parquet(path+'Covs/'+dataset).values.tolist()
    data['budget']=budget
    df2=pd.read_parquet(path+'Parquet/'+dataset)
    data['prices']=list(np.array(df2.loc[[date]])[0])
    data['tickers']=list(df.columns)
    d={}
    d['data']=data
    return json.dumps(d,indent=4)