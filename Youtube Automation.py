#!/usr/bin/env python
# coding: utf-8

# In[1]:
# Import the required packages

#!pip install apiclient
#!pip install freeze
#!pip install oauth2client
#!pip install google-cloud
#!pip install google
#!pip install google-cloud-language
#!pip install youtube-data-api
#!pip install google-api-python-client
#!pip install youtube_transcript_api
#!pip install youtube-python
#!pip install mtranslate
#!pip install langdetect
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.tools import argparser
import pandas as pd
import pprint 
import matplotlib.pyplot as pd
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from oauth2client.tools import argparser
import pandas as pd
import pprint 
import matplotlib.pyplot as matplot
import mtranslate
import langdetect
import re


# In[2]:
# Use the API key generated in the below step

DEVELOPER_KEY = <Insert your API Key>
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
from youtube_transcript_api import YouTubeTranscriptApi


# In[3]:
# This is a standard function to retireve the videos from you-tube

def youtube_search(q, max_results=49,order="relevance", token=None, location=None, location_radius=None):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=DEVELOPER_KEY)
    search_response = youtube.search().list(
    q=q,
    type="video",
    pageToken=token,
    order = order,
    part="id,snippet", 
    maxResults=max_results,
    location=location,
    locationRadius=location_radius).execute()
    title = []
    channelId = []
    channelTitle = []
    categoryId = []
    videoId = []
    viewCount = []
    likeCount = []
    dislikeCount = []
    commentCount = []
    favoriteCount = []
    category = []
    tags = []
    videos = []
    channelSub = []
    for search_result in search_response.get("items", []):
        
        if ((search_result["id"]["kind"] == "youtube#video") or (search_result["id"]["kind"] == "youtube#channel")):

            title.append(search_result['snippet']['title']) 
            videoId.append(search_result['id']['videoId'])
            response = youtube.videos().list(part='statistics, snippet',id=search_result['id']['videoId']).execute()
            channelId.append(response['items'][0]['snippet']['channelId'])
            channelTitle.append(response['items'][0]['snippet']['channelTitle'])
            categoryId.append(response['items'][0]['snippet']['categoryId'])
            favoriteCount.append(response['items'][0]['statistics']['favoriteCount'])
            viewCount.append(response['items'][0]['statistics']['viewCount'])
 
        try:
            commentCount.append(response['items'][0]['statistics']['commentCount'])
        except:
            commentCount.append(0)
                
        if 'tags' in response['items'][0]['snippet'].keys():
            tags.append(response['items'][0]['snippet']['tags'])
        else:
            tags.append([])
        
        try:
                likeCount.append(response['items'][0]['statistics']['likeCount'])
        except:
                likeCount.append(0)
        try:
                dislikeCount.append(response['items'][0]['statistics']['dislikeCount'])
        except:
                dislikeCount.append(0)
            
    for i in channelId:
        search_response2 = youtube.channels().list(part="snippet,statistics", id=i).execute()
        for search_result in search_response2.get("items", []):
            channelSub.append(search_response2['items'][0]['statistics']['subscriberCount'])
            
    youtube_dict = {'videoId':videoId,'tags':tags,'channelId': channelId,'channelTitle': channelTitle,'categoryId':categoryId,'title':title,'videoId':videoId,'viewCount':viewCount,'likeCount':likeCount,'dislikeCount':dislikeCount,'commentCount':commentCount,'favoriteCount':favoriteCount,'channelSubCount':channelSub}

    return youtube_dict

# In[14]:

import os
os.chdir("C:/Users/antony.morais/Desktop/Amalraj/Youtube Automation Blog")

# In[15]:

# The required keyword (for which the search results have to be fetched) needs to be given below in youtube_search function
df=pd.DataFrame(youtube_search("Redmi Note 8 pro", max_results=49))

# In[16]:

df1 = df[['title','videoId','viewCount','channelTitle','channelSubCount','commentCount','likeCount','dislikeCount','tags','favoriteCount','channelId','categoryId']]
df1.columns = ['Title','VideoId','ViewCount','ChannelTitle','ChannelSubCount','CommentCount','likeCount','dislikeCount','tags','favoriteCount','channelId','categoryId']
df1.shape

# In[21]:

#Remove Tutorial Videos
df1=df1[[not i for i in df1.Title.str.contains("how to","tutorial")]]

#Retain only one video per channel (channelID column) based on highest value of Views, Likes and Comments.
#This is to overcome redundant information.
df1.sort_values(['ViewCount','likeCount','CommentCount'], ascending=[False,False,False],inplace=True)
df1.reset_index(drop=True,inplace=True)
df1_dup=pd.DataFrame(df1.duplicated(subset='channelId', keep='first'))
df1_dup.columns=["Dup"]
df_red=df1[df1_dup['Dup']==False]
df_red.reset_index(drop=True,inplace=True)
df_red.shape

# In[23]:

df_red.loc[:,"emv_video"] = df_red.apply(lambda row: int(row.ViewCount)*0.14+int(row.CommentCount)*8.20+int(row.likeCount)*0.72, axis=1)

# In[24]:

videoid = list(df_red['VideoId'])
x = YouTubeTranscriptApi.get_transcripts(videoid, continue_after_error=True)
vids_with_sub = x[0]
vids_without_sub = x[1]
df_trans = pd.DataFrame(list(vids_with_sub.keys()), columns=['VideoId'])

# In[25]:

result2= []
for i in range(0,len(vids_with_sub)):
    print(i)
    result1 = []
    list_con = list(vids_with_sub.values())[i]
    for j in list_con:
        text_proc=j['text']
        if(re.findall('[a-zA-Z]',text_proc)==[]) :
            text_proc_fin=text_proc
            #print(text_proc_fin)
        else :
            txt_lan=langdetect.detect(text_proc)
            if(txt_lan!='en'):
                try :
                    #print("Translating !!!!!!!!!")
                    text_proc_fin=mtranslate.translate(text_proc,"en","auto")
                except :
                    text_proc_fin=text_proc
                #print(text_proc_fin)
            else :
                text_proc_fin=text_proc
                #print(text_proc_fin)
        result1.append(text_proc_fin)
    result2.append(' '.join(result1))


# In[26]:

# Store the results in a seperate column in the dataframe
df_trans['Transcripts'] = result2

# In[27]:

fin_df = pd.merge(df_red, df_trans, how='left', left_on='VideoId', right_on='VideoId')

# Drop unnecessary columns (Those which are not needed for the EMV Calculation
fin_df=fin_df.drop(['categoryId','channelId','ChannelTitle','VideoId','Title','VideoId','tags','favoriteCount'], axis = 1) 

# Store the results back in a CSV
fin_df.reset_index(drop=True).to_csv("redmi_note_8_pro_final.csv", sep=',', encoding='utf-8',index=False)
