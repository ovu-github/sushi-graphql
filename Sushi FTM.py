#!/usr/bin/env python
# coding: utf-8

# In[1]:


# https://k3no.medium.com/how-to-query-in-graphql-6ebb3f7085dc
# https://github.com/sushiswap/sushiswap-subgraph


# In[13]:


from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
import dataframe_image as dfi
import os

fantom = 'https://api.thegraph.com/subgraphs/name/sushiswap/fantom-exchange'


# ## Fantom

# In[14]:


sample_transport=RequestsHTTPTransport(
    url=fantom,
    verify=True,
    retries=3,
)

client = Client(transport=sample_transport)

query = gql('''
query {
  factories(where: {liquidityUSD_gt:0}) {
    pairCount
  }
}
''')

response = client.execute(query)
number_of_pairs = int(response['factories'][0]['pairCount'])
print(number_of_pairs)


# In[15]:


response_list = []
id_list = []

for i in range(number_of_pairs):
    if i % 100 == 0:
        querystring = '''
              query {
              pairs(first: '''+str(100)+' skip: '+str(i)+''' where: {volumeUSD_gt:0}){
                      name
                      id
                  }
                }
                '''
        response = client.execute(gql(querystring))
        for row in response['pairs']:
            response_list.append(row['name'])
            id_list.append(row['id'])    

df_fantom = pd.DataFrame.from_dict(list(zip(response_list,id_list)))
df_fantom[['Token 0', 'Token 1']] = df_fantom[0].str.split('-', expand = True, n = 1)
df_fantom


# In[16]:


interesting_tokens = ['WFTM', 'USDC', 'DAI', 'FUSD', 'ETH', 'fUSDT', 'FETH', 'WBTC']
cream_borrowing_tokens = ['USDC', 'WFTM', 'DAI', 'ETH', 'BTC', 'LINK', 'SUSHI','YFI',
'SNX',
'BAND',
'AAVE',
'COVER',
'CREAM',
'HEGIC']

interesting_tokens = ['WFTM', 'USDC', 'DAI', 'FUSD', 'ETH', 'fUSDT', 'FETH', 'WBTC']
combined_tokens = cream_borrowing_tokens + interesting_tokens


criteria = df_fantom['Token 0'].isin(combined_tokens) &            df_fantom['Token 1'].isin(combined_tokens)

df_fantom_filtered = df_fantom.loc[criteria,:]
df_fantom_filtered.columns = ['Pair', 'id', 'Token 0', 'Token 1']
df_fantom_filtered


# In[17]:


df_fantom_filtered


# In[18]:


df4 = pd.DataFrame([])
lenid = len(df_fantom_filtered['id'])

client = Client(transport=sample_transport)

for count, id in enumerate(df_fantom_filtered['id']):
    print(f'{count+1:2} / {lenid} pair: {id}')
        
    querystring = '''
              query {
  pairDayDatas(where: {pair:"''' + id + '''"} orderBy: date, orderDirection: desc first: 7) {
    date
    volumeUSD
    reserveUSD
  }
}'''
    response = client.execute(gql(querystring))
    response
    
    df1 = pd.DataFrame.from_dict(response['pairDayDatas'])
    df1['id'] = id
    df4 = df4.append(df1)
    
df4


# In[19]:


df5 = df4.merge(df_fantom_filtered,
                left_on = 'id',
                right_on = 'id',
                how = 'left',
                validate = 'many_to_one')
df5[['volumeUSD','reserveUSD']] = df5[['volumeUSD','reserveUSD']].astype(float)
df5['date'] = pd.to_datetime(df5['date'], unit='s')
df5['fee'] = round(df5['volumeUSD'] * 0.003,6)
df5['1y APR for 100 invested'] = round((100/df5['reserveUSD']) * df5['fee'] * 365,3)
df5['Pair'] = '[Sushi Fantom] ' + df5['Pair']
df5.style.format({'reserveUSD': "{:0<4,.10f}"})


# In[20]:


criteria1 = df5['reserveUSD'] > 1
criteria2 = df5['date'] == df5['date'].max()

latest_results = df5.loc[(criteria1 & criteria2), :].sort_values(by = 'date',
                                 ascending = False)\
                    .drop_duplicates(subset = ['Pair'])\
                    .sort_values(by = '1y APR for 100 invested',
                                 ascending = False)\
                    .reset_index(drop = True)\
                    .drop(columns = ['id', 'Token 0', 'Token 1'])\
                    .reset_index(drop = True)[['date', 'Pair', '1y APR for 100 invested',  'reserveUSD', 'volumeUSD', 'fee']]

df_styled  = latest_results.style.format({'reserveUSD': "{:0<4,.2f}",
                             'volumeUSD': "{:0<4,.2f}",
                             'fee': "{:0<4,.2f}",
                             '1y APR for 100 invested': "{:0<4,.2f}"})\
              .set_properties(subset=["Pair"], **{'text-align': 'left'})

df_styled


# In[21]:


dfi.export(df_styled, 'df_styled_sushi_fantom.png')
os.startfile('df_styled_sushi_fantom.png')

