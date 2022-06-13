#!/usr/bin/env python
# coding: utf-8

# ## airtable_tools_v2

# In[3]:


import os, logging
import numpy as np
from tqdm import tqdm
import pandas as pd
from pyairtable import Table
from dotenv import load_dotenv
from datetime import datetime
import pytz


# In[4]:


logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M:%S',level='INFO')
logger=logging.getLogger(__name__)
logger.setLevel('INFO')


# In[5]:


load_dotenv()
api_key=os.getenv('AIRTABLE_API_KEY')
base_id='appDTdyxcShkSR3oF'


# ## Logs

# In[4]:


dst_table_name='[A]Logs'


# In[5]:


logger.info('Connecting to Log and Habits table...')
log_table=Table(api_key, base_id, 'Log')
habit_table=Table(api_key, base_id, 'Habits')

logger.info('Connecting to %s table...', dst_table_name)
a=Table(api_key, base_id, dst_table_name)


# In[6]:


logger.info('Finding Log records with "Log" in the Habit name...')
res=[]
for o in tqdm(log_table.all()):
    if 'fields' not in o: continue
    if 'Habit' not in o['fields']: continue
    if len(o['fields']['Habit'])>0:
        habit=habit_table.get(o['fields']['Habit'][0])
        if 'Log' in habit['fields']['Habit']:
            res.append({'Date':o['fields']['Date'], 'Score':o['fields']['Score'], 'Log': habit['fields']['Habit'].strip('Log: ')})

logger.info('Converting to dataframe and resampling...')
df=pd.DataFrame(res)
df.index=pd.DatetimeIndex(df['Date'])

logger.info('Deleting existing %s data..', dst_table_name)
r=a.all()
ids=[o['id'] for o in r]
res=a.batch_delete(ids)

logger.info('Uploading new analytics data...')
for l in list(df['Log'].unique()):
    dfs=df[df['Log']==l]
    dfs=dfs.sort_index()
    dfr=dfs.resample('D').mean() #Resample
    
    res=[]
    for d in dfr.index:
        if np.isnan(dfr.loc[d]['Score']): continue
        res.append({'Date': str(d.date()),
                 'Score': int(dfr.loc[d]['Score']),
                 'Metric': l})
    res=a.batch_create(res)
logger.info('Completed uploading %i records. ', len(res))


# ## Health Habits

# In[7]:


dst_table_name='[A]HealthHabits'
non_weight_volume_mult=50


# In[8]:


logger.info('Connecting to Log, Habits, and Goal table...')
log_table=Table(api_key, base_id, 'Log')
habit_table=Table(api_key, base_id, 'Habits')
goal_table=Table(api_key, base_id, 'Goals')

logger.info('Connecting to %s table...', dst_table_name)
a=Table(api_key, base_id, dst_table_name)


# In[9]:


logger.info('Finding Exercise Logs')
res=[]
for o in tqdm(log_table.all()):
    if 'fields' not in o: continue
    if 'Habit' not in o['fields']: continue
    if 'Goal 2' not in o['fields']: continue
    if 'Category' not in o['fields']: continue
    if len(o['fields']['Goal 2'])>0:
        goal=goal_table.get(o['fields']['Goal 2'][0])
        habit=habit_table.get(o['fields']['Habit'][0])['fields']['Habit']
        if 'fields' not in goal: continue
        if 'Goal' not in goal['fields']: continue
        if goal['fields']['Goal']=="Health":
            if 'Reps' in o['fields'] and 'Weight' in o['fields'] and 'Sets' in o['fields']:
                volume=float(o['fields']['Reps'])*float(o['fields']['Sets'])*float(o['fields']['Weight'])
            elif 'Minutes' in o['fields']: 
                volume=non_weight_volume_mult*o['fields']['Minutes']
            else:
                volume=100
                
            if len(o['fields']['Category'])>0: category=o['fields']['Category'][0]
            else: category='Unknown'
            res.append({'Date':o['fields']['Date'], 
                        'Volume':volume, 
                        'Habit':habit,
                        'Category': category})
            
logger.info('Converting to dataframe and resampling...')
df=pd.DataFrame(res)
df.index=pd.DatetimeIndex(df['Date'])

logger.info('Deleting existing %s data..', dst_table_name)
r=a.all()
ids=[o['id'] for o in r]
res=a.batch_delete(ids)


# In[10]:


df.head()


# In[11]:


df=df.sort_index()
dfr=df.resample('D').sum() #Resample


# In[12]:


# dfr.loc[pd.datetime.strptime('2021-4-20', '%Y-%m-%d')]=0 #Working test case
end_date=pd.datetime.now()
if end_date not in dfr.index: #Do we have data from today?
    dfr.loc[end_date]=0 #Add 0s at todays date
    dfr=dfr.resample('D').sum()


# In[13]:


logger.info('Computing cumulative sums by type...')

for s in df['Category'].unique(): dfr['Volume_'+s]=df[df['Category']==s]['Volume'].resample('D').sum()
dfr=dfr.replace(np.NaN, 0)
for s in df['Category'].unique(): dfr['Volume_Cumulative_'+s]=dfr['Volume_'+s].cumsum()


# In[14]:


dfr


# In[15]:


logger.info('Deleting old Analytics data..')
r=a.all()
ids=[o['id'] for o in r]
res=a.batch_delete(ids)


# In[16]:


logger.info('Uploading new analytics data...')
l=[]
for s in df['Category'].unique():
    for d in dfr.index:
        l.append({'Date': str(d.date()),
                 'Exercise Volume': dfr.loc[d]['Volume_Cumulative_'+s],
                 'Category': s})
res=a.batch_create(l)


# ## General Actions Bro

# In[17]:


dst_table_name='[A]Actions'
logger.info('Deleting existing %s data..', dst_table_name)

logger.info('Connecting to %s table...', dst_table_name)
a=Table(api_key, base_id, dst_table_name)
r=a.all()
ids=[o['id'] for o in r]
res=a.batch_delete(ids)


# In[18]:


logger.info('Connecting to Log, Habits, and Goal table...')
log_table=Table(api_key, base_id, 'Log')
habit_table=Table(api_key, base_id, 'Habits')
goal_table=Table(api_key, base_id, 'Goals')


# In[19]:


res=[]
for o in tqdm(log_table.all()):
    if 'fields' not in o: continue
    if 'Action' not in o['fields']: continue
    if 'Goal' not in o['fields']: continue
    res.append({'Date': o['fields']['Date'], 
                'Action': o['fields']['Action'],
                'Goal': o['fields']['Goal']})

logger.info('Converting to dataframe and resampling...')
df=pd.DataFrame(res)
df.index=pd.DatetimeIndex(df['Date'])
df=df.sort_index()


# In[20]:


for g in df['Goal'].unique():
    df['Goal_'+g]=(df['Goal']==g)
dfr=df.resample('D').sum()
dfr=dfr.replace(np.NaN, 0)
for s in df['Goal'].unique(): dfr['Goal_Cumulative_'+s]=dfr['Goal_'+s].cumsum()


# In[21]:


dfr.head()


# In[22]:


logger.info('Uploading new actions data...')
l=[]
for s in df['Goal'].unique():
    for d in dfr.index:
        l.append({'Date': str(d.date()),
                  'Actions Completed': int(dfr.loc[d]['Goal_'+s]),
                  'Actions Completed Cumulative': int(dfr.loc[d]['Goal_Cumulative_'+s]),
                  'Goal': s})
res=a.batch_create(l)


# ## Goal/Habit Tracking
# - Can I make this super general so I can visualize any goal over time?
# - Pausing here for now -> key pieces are deployed, can contineue to improve over time, but let's get this thing live!!

# In[44]:


dst_table_name='[A]Habits'


# In[45]:


logger.info('Connecting to Log, Habits, and Goal table...')
log_table=Table(api_key, base_id, 'Log')
habit_table=Table(api_key, base_id, 'Habits')
goal_table=Table(api_key, base_id, 'Goals')

logger.info('Connecting to %s table...', dst_table_name)
a=Table(api_key, base_id, dst_table_name)


# In[54]:


logger.info('Finding Personal Development Logs without "Log" in name')
res=[]
for o in tqdm(log_table.all()):
    if 'fields' not in o: continue
    if 'Habit' not in o['fields']: continue
    if 'Goal 2' not in o['fields']: continue
    if len(o['fields']['Goal 2'])>0:
        goal=goal_table.get(o['fields']['Goal 2'][0])
        habit=habit_table.get(o['fields']['Habit'][0])
        if 'fields' not in goal: continue
        if 'Goal' not in goal['fields']: continue
        if 'Log' in habit['fields']['Habit']: continue
        d={'Date':o['fields']['Date'], 'Habit': habit['fields']['Habit'], 'Goal':goal['fields']['Goal']}
        if 'Minutes' in o['fields']: d['Minutes']=o['fields']['Minutes']
        res.append(d)


# In[55]:


logger.info('Converting to dataframe and resampling...')
df=pd.DataFrame(res)
df.index=pd.DatetimeIndex(df['Date'])
df=df.sort_index()
dfr=df.resample('D').sum() #Resample

logger.info('Deleting existing %s data..', dst_table_name)
r=a.all()
ids=[o['id'] for o in r]
res=a.batch_delete(ids)


# In[56]:


end_date=pd.datetime.now()
if end_date not in dfr.index: #Do we have data from today?
    dfr.loc[end_date]=0 #Add 0s at todays date
    dfr=dfr.resample('D').sum()


# In[57]:


logger.info('Computing cumulative sums by type...')

for s in df['Habit'].unique(): dfr['Minutes_'+s]=df[df['Habit']==s]['Minutes'].resample('D').sum()
dfr=dfr.replace(np.NaN, 0)
for s in df['Habit'].unique(): dfr['Minutes_Cumulative_'+s]=dfr['Minutes_'+s].cumsum()


# In[67]:


logger.info('Uploading new analytics data...')
l=[]
for s in df['Habit'].unique():
    for d in dfr.index:
        l.append({'Date': str(d.date()),
                  'Goal': df[df['Habit']==s]['Goal'].iloc[0],
                  'Minutes': dfr.loc[d]['Minutes_'+s],
                  'Minutes Cumulative': dfr.loc[d]['Minutes_Cumulative_'+s],
                  'Habit': s})
res=a.batch_create(l)


# ## References

# In[146]:


dst_table_name='[A]References'


# In[147]:


logger.info('Connecting to Log, Habits, and Goal table...')
references_table=Table(api_key, base_id, 'References')

logger.info('Connecting to %s table...', dst_table_name)
a=Table(api_key, base_id, dst_table_name)


# In[148]:


logger.info('Deleting existing %s data..', dst_table_name)
r=a.all()
ids=[o['id'] for o in r]
res=a.batch_delete(ids)


# In[149]:


logger.info('Finding references data...')
res=[]
for o in tqdm(references_table.all()):
    res.append({'Date':o['createdTime'], 'Refs':1})


# In[150]:


df=pd.DataFrame(res)
df.index=pd.DatetimeIndex(df['Date'])
df=df.sort_index()
dfr=df.resample('D').sum() #Resample


# In[151]:


end_date=pd.datetime.now(tz=pytz.timezone('UTC'))
if end_date not in dfr.index: #Do we have data from today?
    dfr.loc[end_date]=0 #Add 0s at todays date
    dfr=dfr.resample('D').sum()


# In[152]:


dfr['Refs Cumulative']=dfr['Refs'].cumsum()
dfr['Date']=[str(dfr.index[i].date()) for i in range(len(dfr))]


# In[153]:


res=a.batch_create(dfr.to_dict(orient='Records'))


# In[ ]:




