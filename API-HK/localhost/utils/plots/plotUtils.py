# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 14:05:55 2022

@author: user
"""

import pygal
import json
import pandas as pd

from pygal.style import Style
from datetime import datetime as dt

import matplotlib.pyplot as plt
import numpy as np

import base64
from io import BytesIO


def getDataFrame(dataToReadDir):

    fileID = open(dataToReadDir, "r", encoding="utf8")

    #% Read json and unpack data structure
    jsonData = json.load(fileID) # json format: RFC-8259
    dataList = list(jsonData.values())[0] # Unpack from dict structure -> values have the data
    dataList = dataList[0] # From returned list -> Unpack data from first index
    
    #% Return Data frame
    return pd.DataFrame(dataList) # Make dataframe from the unpacked data

def sliceTimeMatrix(df, measureIndex):
    
    #% 2D data slicing
    valueList = df['VALUE']
    slicedData = [item[measureIndex] for item in valueList] # XY Matrix Data: size [1,nm]
    squareSize = np.sqrt(len(slicedData)).astype('int')
    slicedData = np.reshape(slicedData, (squareSize, squareSize)).T
    
    return slicedData
    
def getSensTimeSeries(df, sensorIndex, useIndex=True):

    #% Retrieve time series from dataframe
    if useIndex:
        sensorID = df['ID'][sensorIndex] # From Columns: A to Z and Rows: 1 to 26 in sensor grid
        thisTimeSeries = df[['T_STAMP','VALUE']][df['ID'] == sensorID].values.tolist()
    else:
        sensorID = sensorIndex # If false, interpret sensorIndex as a string tag
        thisTimeSeries = df[['T_STAMP','VALUE']][df['ID'] == sensorIndex].values.tolist()
    
    thisTstampsList = sum(thisTimeSeries[0][0], []) # Flatten nested lists: Deepth 3 Lists
    thisMeasValList = sum(thisTimeSeries[0][1], [])

    timeFormater = lambda x: dt.strptime(x,'%Y/%m/%d %H:%M:%S')
    dtList = [timeFormater(strDate) for strDate in thisTstampsList]
    dataPairs = [(t, y) for t, y in zip(dtList,thisMeasValList)]
    
    return (sensorID, dataPairs)
    
def plotTimeSeries(sensorID,dataPairs):

    # Plot Style
    custom_style = Style(label_font_size = 20, major_label_font_size = 20)
    datetimeline = pygal.DateTimeLine(
         x_label_rotation=35, truncate_label=-1, style=custom_style)
    
    datetimeline.title = 'Temperature [°C]: 24-Hours Behaviour'
    datetimeline.add(sensorID,dataPairs)
    # datetimeline.render_in_browser()
    embeded_chart_data = datetimeline.render_data_uri()
    return embeded_chart_data

def makeMultiSeries(df, sensorIDlist):

    # Plot Style
    custom_style = Style(label_font_size = 20, major_label_font_size = 20)
    datetimeline = pygal.DateTimeLine(
         x_label_rotation=35, truncate_label=-1, style=custom_style)
    datetimeline.title = 'Temperature [°C]: 24-Hours Behaviour'
    
    # Retrieve data points from df to plot
    for snrIndex in sensorIDlist:
        sensorID, dataPairs = getSensTimeSeries(df,snrIndex)
        datetimeline.add(sensorID,dataPairs)
        
    return datetimeline.render_data_uri()

def heatmap2d(dataArray):

    fig = plt.figure()
    plt.imshow(dataArray, cmap='hot', interpolation='nearest')
    plt.colorbar()

    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png', bbox_inches='tight')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    encodedString = "data:image/png;base64,{str}".format(str = encoded)
    
    return encodedString

def get2DarrayAverage(dataArray):
    return np.mean(dataArray[:])

