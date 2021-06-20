#!/usr/bin/env python
# coding: utf-8

# In[1]:


# https://k3no.medium.com/how-to-query-in-graphql-6ebb3f7085dc
# https://github.com/sushiswap/sushiswap-subgraph


# In[82]:


from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
import dataframe_image as dfi
import os

quickswap = 'https://api.thegraph.com/subgraphs/name/sameepsi/quickswap02'
quickswap_daily = 'https://api.thegraph.com/subgraphs/name/moonster-bsc/quickswap-daypairdataslim'


# ## Quickswap

# In[3]:


sample_transport=RequestsHTTPTransport(
    url=quickswap,
    verify=True,
    retries=3,
)

client = Client(transport=sample_transport)


# In[4]:


query = gql('''
query {
  uniswapFactories {
    pairCount
  }
}
''')

response = client.execute(query)
number_of_pairs = int(response['uniswapFactories'][0]['pairCount'])
print(number_of_pairs)


# In[5]:


df = pd.DataFrame([])
response_dict = {}
response_list = []


for i in range(number_of_pairs):
    if i % 100 == 0:
        querystring = '''
              query {
              pairs(first: '''+str(100)+' skip: '+str(i)+''' where: {volumeUSD_gt:0}){
                      token0 {symbol}
                      token1 {symbol}
                      id
                  }
                }
                '''
        try:
            response = client.execute(gql(querystring))
            df = df.append(pd.DataFrame.from_dict(response['pairs']))
    #         for row in response['pairs']:
    #             response_list.append(row['token0']['symbol'] + '-' + row['token1']['symbol'])
            print(len(df))
        except:
            pass

df


# In[6]:


df['token0'] = df['token0'].astype(str).str.replace("{'symbol': ",'', regex= True)                                           .replace("}",'', regex= True)                                           .replace("'",'', regex= True)
df['token1'] = df['token1'].astype(str).str.replace("{'symbol': ",'', regex= True)                                           .replace("}",'', regex= True)                                           .replace("'",'', regex= True)
df['Pair'] = df['token0'] + '-' + df['token1']
df.columns = ['id','Token 0', 'Token 1', 'Pair']
df = df[['id','Pair', 'Token 0', 'Token 1']]
df.head(2)


# In[7]:


# interesting_tokens = ['YFI', 'WOOFY', 'CRV', 'ILV', 'WBTC', 'WMATIC', 'MATIC', 'AAVE', 'WETH', 'ETH', 'SUSHI', 'UNI', 'SNX', 'LINK', 'DAI', 'USDC', 'USDT', 'FRAX']
# interesting_tokens = ['USDC', 'USDT', 'DAI', 'FRAX', 'IRON']
interesting_tokens = ['MATIC', 'DAI', 'USDC', 'USDT', 'WBTC', 'WETH', 'FRAX', 'WMATIC']

criteria = df['Token 0'].isin(interesting_tokens) &            df['Token 1'].isin(interesting_tokens)

df_filtered = df.loc[criteria,:]
df_filtered.head()


# In[56]:


df4 = pd.DataFrame([])
lenid = len(df_filtered['id'])

sample_transport=RequestsHTTPTransport(
    url=quickswap_daily,
    verify=True,
    retries=3,
)

client = Client(transport=sample_transport)

for count, id in enumerate(df_filtered['id']):
    print(f'{count+1:2} / {lenid} pair: {id}')
        
    querystring = '''
              query {
  pairDayDatas(where: {pairAddress:"''' + id + '''"} orderBy: date, orderDirection: desc first: 7) {
    date
    dailyVolumeUSD
    reserveUSD
  }
}'''
    response = client.execute(gql(querystring))
    response
    
    df1 = pd.DataFrame.from_dict(response['pairDayDatas'])
    df1['id'] = id
    df4 = df4.append(df1)


# In[57]:


df5 = df4.merge(df_filtered,
                left_on = 'id',
                right_on = 'id',
                how = 'left',
                validate = 'many_to_one')
df5[['dailyVolumeUSD','reserveUSD']] = df5[['dailyVolumeUSD','reserveUSD']].astype(float)
df5['date'] = pd.to_datetime(df5['date'], unit='s')
df5['fee'] = round(df5['dailyVolumeUSD'] * 0.003,6)
df5['1y APR for 100 invested'] = round((100/df5['reserveUSD']) * df5['fee'] * 365,3)
df5['Pair'] = '[Quickswap] ' + df5['Pair']
df5.style.format({'reserveUSD': "{:0<4,.10f}"})


# In[87]:


criteria1 = df5['reserveUSD'] > 1
criteria2 = df5['date'] == df5['date'].max()

latest_results = df5.loc[(criteria1 & criteria2), :].sort_values(by = 'date',
                                 ascending = False)\
                    .drop_duplicates(subset = ['Pair'])\
                    .sort_values(by = '1y APR for 100 invested',
                                 ascending = False)\
                    .reset_index(drop = True)\
                    .drop(columns = ['id', 'Token 0', 'Token 1'])\
                    .reset_index(drop = True)[['date', 'Pair', '1y APR for 100 invested',  'reserveUSD', 'dailyVolumeUSD', 'fee']]

df_styled  = latest_results.style.format({'reserveUSD': "{:0<4,.2f}",
                             'dailyVolumeUSD': "{:0<4,.2f}",
                             'fee': "{:0<4,.2f}",
                             '1y APR for 100 invested': "{:0<4,.2f}"})\
              .set_properties(subset=["Pair"], **{'text-align': 'left'})

df_styled


# In[83]:


dfi.export(df_styled, 'df_styled.png')
os.startfile('df_styled.png')

