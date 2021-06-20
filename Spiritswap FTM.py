#!/usr/bin/env python
# coding: utf-8

# In[1]:


# https://k3no.medium.com/how-to-query-in-graphql-6ebb3f7085dc
# https://github.com/sushiswap/sushiswap-subgraph


# In[3]:


from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
import dataframe_image as dfi
import os

fantom = 'https://api.thegraph.com/subgraphs/name/layer3org/spiritswap-analytics'
# https://thegraph.com/explorer/subgraph/eerieeight/spooky-swap-exchange


# ## Fantom

# In[5]:


sample_transport=RequestsHTTPTransport(
    url=fantom,
    verify=True,
    retries=3,
)

client = Client(transport=sample_transport)

query = gql('''
query {
  spiritswapFactories{
    pairCount
  }
}
''')

response = client.execute(query)
number_of_pairs = int(response['spiritswapFactories'][0]['pairCount'])
print(number_of_pairs)


# In[7]:


token0list = []
token1list = []
id_list = []

for i in range(number_of_pairs):
    if i % 100 == 0:
        querystring = '''
              query {
              pairs(first: '''+str(100)+' skip: '+str(i)+''' where: {volumeUSD_gt:0}){
                      token0{symbol}
                      token1{symbol}
                      id
                  }
                }
                '''
        response = client.execute(gql(querystring))
        for row in response['pairs']:
            token0list.append(row['token0']['symbol'])
            token1list.append(row['token1']['symbol'])
            id_list.append(row['id'])    

df_spirit = pd.DataFrame.from_dict(list(zip(token0list,token1list,id_list)))
df_spirit.columns = ['Token 0', 'Token 1', 'id']
df_spirit['Pair'] = df_spirit['Token 0'] + '-' + df_spirit['Token 1']
df_spirit = df_spirit[['Pair', 'id', 'Token 0', 'Token 1']]
df_spirit


# In[8]:


cream_borrowing_tokens = ['USDC', 'WFTM', 'DAI', 'ETH', 'BTC', 'LINK', 'SUSHI','YFI',
'SNX',
'BAND',
'AAVE',
'COVER',
'CREAM',
'HEGIC']

interesting_tokens = ['WFTM', 'USDC', 'DAI', 'FUSD', 'ETH', 'fUSDT', 'FETH', 'WBTC']
combined_tokens = cream_borrowing_tokens + interesting_tokens
combined_tokens


# In[9]:


criteria = df_spirit['Token 0'].isin(combined_tokens) &            df_spirit['Token 1'].isin(combined_tokens)

df_spirit_filtered = df_spirit.loc[criteria,:]
df_spirit_filtered.columns = ['Pair', 'id', 'Token 0', 'Token 1']
df_spirit_filtered


# In[10]:


df4 = pd.DataFrame([])
lenid = len(df_spirit_filtered['id'])

client = Client(transport=sample_transport)

for count, id in enumerate(df_spirit_filtered['id']):
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
    
df4


# In[12]:


df5 = df4.merge(df_spirit_filtered,
                left_on = 'id',
                right_on = 'id',
                how = 'left',
                validate = 'many_to_one')
df5[['dailyVolumeUSD','reserveUSD']] = df5[['dailyVolumeUSD','reserveUSD']].astype(float)
df5['date'] = pd.to_datetime(df5['date'], unit='s')
df5['fee'] = round(df5['dailyVolumeUSD'] * 0.003,6)
df5['1y APR for 100 invested'] = round((100/df5['reserveUSD']) * df5['fee'] * 365,3)
df5['Pair'] = '[Spirit FTM] ' + df5['Pair']
df5.style.format({'reserveUSD': "{:0<4,.10f}"})


# In[13]:


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


# In[33]:


dfi.export(df_styled, 'df_styled_spooky_fantom.png')
os.startfile('df_styled_spooky_fantom.png')

