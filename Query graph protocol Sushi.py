#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# https://k3no.medium.com/how-to-query-in-graphql-6ebb3f7085dc
# https://github.com/sushiswap/sushiswap-subgraph


# In[57]:


from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd

mainnet = 'https://api.thegraph.com/subgraphs/name/jiro-ono/sushiswap-exchange'
fantom = 'https://api.thegraph.com/subgraphs/name/sushiswap/fantom-exchange'
matic = 'https://api.thegraph.com/subgraphs/name/sushiswap/matic-exchange'


# ## Matic

# In[78]:


sample_transport=RequestsHTTPTransport(
    url=matic,
    verify=True,
    retries=3,
)

client = Client(transport=sample_transport)


# In[79]:


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


# In[80]:


df = pd.DataFrame([])
response_dict = {}
response_list = []


for i in range(number_of_pairs):
    if i % 100 == 0:
        querystring = '''
              query {
              pairs(first: '''+str(100)+' skip: '+str(i)+''' where: {volumeUSD_gt:0}){
                      name
                  }
                }
                '''
        response = client.execute(gql(querystring))
        for row in response['pairs']:
            response_list.append(row['name'])    

df = pd.DataFrame.from_dict(response_list).drop_duplicates()
df[['Token 0', 'Token 1']] = df[0].str.split('-', expand = True, n = 1)
df.value_counts()


# In[81]:


interesting_tokens = ['YFI', 'WOOFY', 'CRV', 'ILV', 'WBTC', 'WMATIC', 'MATIC', 'AAVE', 'WETH', 'ETH', 'SUSHI', 'UNI', 'SNX', 'LINK', 'DAI', 'USDC', 'USDT', 'FRAX']
# interesting_tokens = ['USDC', 'USDT', 'DAI', 'FRAX', 'IRON']
# interesting_tokens = ['MATIC', 'DAI', 'USDC', 'USDT', 'WBTC', 'WETH', 'WMATIC']

criteria = df['Token 0'].isin(interesting_tokens) &            df['Token 1'].isin(interesting_tokens)

df_filtered = df.loc[criteria,:]
df_filtered.columns = ['Pair', 'Token 0', 'Token 1']
df_filtered.head()


# In[82]:


# make a list of strings with double quotes

stringtest = "["

for i in df_filtered['Pair'].values.tolist():
    stringtest += '"'+ i + '",'
    
stringtest[:-1]+"]"


# In[83]:


querystring = '''
              query {
  pairs(where: {name_in: ''' + stringtest[:-1]+"]" + '''}){
    name
    dayData{
      date
      reserveUSD
      volumeUSD
      txCount
    }
  }
}
                '''
response = client.execute(gql(querystring))
response


# In[84]:


df4 = pd.DataFrame([])

for pair_no in range(len(response['pairs'])):
    df3 = pd.DataFrame.from_dict(response['pairs'][pair_no])
    df3[['date', 'reserveUSD', 'txCount', 'volumeUSD']] = df3['dayData'].apply(pd.Series)
    df3 = df3.drop(columns = ['dayData'])
    df4 = df4.append(df3)
    
df4[['date','reserveUSD','volumeUSD']] = df4[['date','reserveUSD','volumeUSD']].astype(float)
df4['txCount'] = df4['txCount'].astype(int)
df4['date'] = pd.to_datetime(df4['date'], unit='s')
df4['fee'] = round(df4['volumeUSD'] * 0.003,6)
df4['1y APR for 100 invested'] = round((100/df4['reserveUSD']) * df4['fee'] * 365,3)
df4['name'] = '[Matic] ' + df4['name']
df4.head(1)


# In[85]:


latest_results = df4.drop_duplicates(subset = ['name'], keep = 'last')                    .sort_values(by = '1y APR for 100 invested',
                                 ascending = False)\
                    .reset_index(drop = True)
latest_results.style.format({'reserveUSD': "{:0<4,.2f}"})


# In[87]:


df_horizontal = df4.pivot(index = 'name',
                          columns = 'date',
                          values = '1y APR for 100 invested')
# .style.format("{:0<4,.2f}")

# drop last day as it is incomplete
df_horizontal = df_horizontal.drop(columns = df_horizontal.columns[-1])
df_horizontal


df_horizontal['Median APR last 3 days'] = df_horizontal[df_horizontal.columns[-3:]].median(axis = 1)
df_horizontal['Median APR last 7 days'] = df_horizontal[df_horizontal.columns[-7:]].median(axis = 1)
df_horizontal['Median APR last 14 days'] = df_horizontal[df_horizontal.columns[-14:]].median(axis = 1)
df_horizontal[['Median APR last 3 days', 'Median APR last 7 days', 'Median APR last 14 days']].sort_values(by = 'Median APR last 3 days', ascending = False)


# ## Fantom

# In[90]:


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



response_list = []

for i in range(number_of_pairs):
    if i % 100 == 0:
        querystring = '''
              query {
              pairs(first: '''+str(100)+' skip: '+str(i)+''' where: {volumeUSD_gt:0}){
                      name
                  }
                }
                '''
        response = client.execute(gql(querystring))
        for row in response['pairs']:
            response_list.append(row['name'])    

df_fantom = pd.DataFrame.from_dict(response_list).drop_duplicates()
df_fantom[['Token 0', 'Token 1']] = df_fantom[0].str.split('-', expand = True, n = 1)
df_fantom.value_counts()

criteria = df_fantom['Token 0'].isin(interesting_tokens) &            df_fantom['Token 1'].isin(interesting_tokens)

df_fantom_filtered = df_fantom.loc[criteria,:]
df_fantom_filtered.columns = ['Pair', 'Token 0', 'Token 1']

# make a list of strings with double quotes
stringtest = "["

for i in df_filtered['Pair'].values.tolist():
    stringtest += '"'+ i + '",'

# find the daily returns
querystring = '''
              query {
  pairs(where: {name_in: ''' + stringtest[:-1]+"]" + '''}){
    name
    dayData{
      date
      reserveUSD
      volumeUSD
      txCount
    }
  }
}
                '''
response = client.execute(gql(querystring))


# turn the daily returns into a dataframe
df4_fantom = pd.DataFrame([])

for pair_no in range(len(response['pairs'])):
    df3_fantom = pd.DataFrame.from_dict(response['pairs'][pair_no])
    df3_fantom[['date', 'reserveUSD', 'txCount', 'volumeUSD']] = df3_fantom['dayData'].apply(pd.Series)
    df3_fantom = df3_fantom.drop(columns = ['dayData'])
    df4_fantom = df4_fantom.append(df3_fantom)
    
df4_fantom[['date','reserveUSD','volumeUSD']] = df4_fantom[['date','reserveUSD','volumeUSD']].astype(float)
df4_fantom['txCount'] = df4_fantom['txCount'].astype(int)
df4_fantom['date'] = pd.to_datetime(df4_fantom['date'], unit='s')
df4_fantom['fee'] = round(df4_fantom['volumeUSD'] * 0.003,6)
df4_fantom['1y APR for 100 invested'] = round((100/df4_fantom['reserveUSD']) * df4_fantom['fee'] * 365,3)
df4_fantom['name'] = '[Fantom] ' + df4_fantom['name']


df_horizontal_fantom = df4_fantom.pivot(index = 'name',
                          columns = 'date',
                          values = '1y APR for 100 invested')
# .style.format("{:0<4,.2f}")

# drop last day as it is incomplete
df_horizontal_fantom = df_horizontal_fantom.drop(columns = df_horizontal_fantom.columns[-1])
df_horizontal_fantom


df_horizontal_fantom['Median APR last 3 days'] = df_horizontal_fantom[df_horizontal_fantom.columns[-3:]].median(axis = 1)
df_horizontal_fantom['Median APR last 7 days'] = df_horizontal_fantom[df_horizontal_fantom.columns[-7:]].median(axis = 1)
df_horizontal_fantom['Median APR last 14 days'] = df_horizontal_fantom[df_horizontal_fantom.columns[-14:]].median(axis = 1)
df_horizontal_fantom[['Median APR last 3 days', 'Median APR last 7 days', 'Median APR last 14 days']].sort_values(by = 'Median APR last 3 days', ascending = False)


# In[92]:


df_horizontal.append(df_horizontal_fantom)[['Median APR last 3 days', 'Median APR last 7 days', 'Median APR last 14 days']].sort_values(by = 'Median APR last 3 days', ascending = False)


# In[94]:


print(df_horizontal.append(df_horizontal_fantom)[['Median APR last 3 days', 'Median APR last 7 days', 'Median APR last 14 days']].sort_values(by = 'Median APR last 3 days', ascending = False).to_string())


