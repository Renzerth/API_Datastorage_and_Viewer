from flask import Flask, jsonify, abort, render_template
from flask import make_response, request, session, url_for

import json
from utils.plots import plotUtils as plu
from random import randint

app = Flask(__name__, static_url_path = "")

# Local JSON reading
targetFolder = './static/Data/'
fileName = '1_JSON_data_24-Sep-2022_20-14-46.json'
dataToReadDir = f'{targetFolder}\{fileName}'

# Local Datafram
df = plu.getDataFrame(dataToReadDir)

# API Route
apiInfo = {"name" : "dataviewer",
           "apiName" : "api",
           "version" : "v0.1",
           "techReading" : "sensors",
           "parameter" : "temperature"
}

endpointA = "".join(["/" + routes for routes in apiInfo.values()]) + "/" # Return JSONs
endpointB = endpointA + "/plot/series/" # Plot time series
endpointC = endpointA + "/plot/heat/" # Plot heatmaps

@app.route('/')
def index():
    try:
        sensorIndex = 0;
        dataframeLength = len(df)
        sensorID, dataPairs = plu.getSensTimeSeries(df,sensorIndex)
        char_data = plu.plotTimeSeries(sensorID,dataPairs)
        
        randomSensorsIndices = sorted([randint(0,len(df)-1) for sensors in range(0,8)])
        multi_char_data = plu.makeMultiSeries(df, randomSensorsIndices)
        
        timeIndx = randint(1,23) # 24 Hours -> 24 readings
        slicedMatrix = plu.sliceTimeMatrix(df, timeIndx)
        embededFigure = plu.heatmap2d(slicedMatrix)
        
        tempAverage="{:.2f}".format(plu.get2DarrayAverage(slicedMatrix)*100)
        
        return render_template("index.html",char_data=char_data,
                                multi_char_data=multi_char_data,
                                heatmap2d=embededFigure,
                                tempAverage=tempAverage,
                                timeStamp=df['T_STAMP'][0][0][timeIndx],
                                availableSensors=dataframeLength,
                                totalRegisters=dataframeLength*25
        )
        
    except Exception as e:
        return f"An Error Occured: {e}"

# Endpoint A for specific Sensors
@app.route(f'{endpointA}<sensorID>', methods = ['GET'])
def get_sensor(sensorID):
    validSensor = df[df['ID']== sensorID]
    if len(validSensor) == 0:
        abort(404)
    return validSensor.to_json()
    

# Endpoint A for all Sensors
@app.route(f'{endpointA}', methods = ['GET'])
def get_all_sensors():
    return df.to_json()
    

# Endpoint B for plotting specific graph
@app.route(f'{endpointB}<sensorID>', methods = ['GET'])
def plotSpecSensor(sensorID):
    try:
        dataframeLength = len(df)
        _, dataPairs = plu.getSensTimeSeries(df,sensorID,useIndex=False)
        char_data = plu.plotTimeSeries(sensorID,dataPairs)
        
        return render_template("time_series_plot.html",char_data=char_data,
                                sensorID=sensorID,
        )
        
    except Exception as e:
        return f"An Error Occured: {e}"

# Endpoint C for plotting specific time heatmap
@app.route(f'{endpointC}<int:timeIndx>', methods = ['GET'])
def plotHourHeatmap(timeIndx):
    try:
        slicedMatrix = plu.sliceTimeMatrix(df, timeIndx)
        embededFigure = plu.heatmap2d(slicedMatrix)
        
        return render_template("heatmap_plot.html",heatmap2d=embededFigure,
                                timeStamp=df['T_STAMP'][0][0][timeIndx]
        )
        
    except Exception as e:
        return f"An Error Occured: {e}"


# def read():
    # """
        # read() : Fetches documents from Firestore collection as JSON
        # todo : Return document that matches query ID
        # all_todos : Return all documents
    # """
    # try:
        # # Check if ID was passed to URL query
        # todo_id = request.args.get('id')    
        # if todo_id:
            # todo = todo_ref.document(todo_id).get()
            # return jsonify(todo.to_dict()), 200
        # else:
            # all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            # return jsonify(all_todos), 200
    # except Exception as e:
        # return f"An Error Occured: {e}"

if __name__ == '__main__':
    print(__package__)
    app.run(debug=True, host='0.0.0.0', port=5000) 

