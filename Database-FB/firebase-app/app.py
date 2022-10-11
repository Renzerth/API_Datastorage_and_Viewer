"""
"""
import os
from datetime import datetime

from flask import Flask, request, jsonify, render_template, make_response, abort
from firebase_admin import credentials, firestore, initialize_app

# Initialize Flask App
app = Flask(__name__)


# Check project environment to set Firebase Client
if os.getenv('GAE_ENV', '').startswith('standard'):
    localEnv = False
    # production
    db = firestore.client()
else:
    localEnv = True
    # localhost environments
    projectID ="test"
    os.environ["FIRESTORE_DATASET"] = projectID
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    os.environ["FIRESTORE_EMULATOR_HOST_PATH"] = "localhost:8080/firestore"
    os.environ["FIRESTORE_HOST"] = "http://localhost:8080"
    os.environ["FIRESTORE_PROJECT_ID"] = projectID
    os.environ["GCLOUD_PROJECT"] = projectID

    # local authentification
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

    # new credential instance
    cred = credentials.ApplicationDefault() # set credentials when "GOOGLE_APPLICATION_CREDENTIALS" envvar is previously set

    # Initialize Firestore DB
    firebase_app = initialize_app(cred)
    # db = firestore.Client(project="test", credentials=cred) # with options = options -> ONLY WORKS WITH google-auth-crendentials
    db = firestore.client()


# Initial setups
dBroot = 'sensors'
sensDb = db.collection(dBroot) # Set reference collection - All data goes to sensor readings db
validDocs = ['temperature', 'humidity']

temperatRef = sensDb.document('temperature') # documents
humidityRef = sensDb.document('humidity')


# if localEnv
    # loadDummyData('./static/data/Dummy.json')


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)


# Aux functions
def readAllEntries(db_ref, orderChild=None):
    """
    """
    # get all messages from the Firestore
    
    if orderChild:
        db_gen = db_ref.order_by_child(orderChild).stream()
    else:
        db_gen = db_ref.stream()

    allEntriesList = []
    for entries in db_gen:
        entries_dict = entries.to_dict()  # converting DocumentSnapshot into a dictionary
        entries_dict["id"] = entries.id
        allEntriesList.append(entries_dict)  # appending the dict to the reading list
    
    return allEntriesList

def delete_collection(coll_ref, batch_size):
    """
        https://firebase.google.com/docs/firestore/manage-data/delete-data#collections
    """
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

def loadDummyData(sensDb, jsonFilename):
    """
    """
    import json

    # Load local file to database 
    with open(jsonFilename, "r") as f:
        file_contents = json.load(f)
    sensDb.reference("/").set(file_contents) # Set reference to root and  content
    
    return None

def extractSubCollections(doc, orderChild=None):
    """
    """
    #collection = fs.collection("my-collection")
    #doc = collection.document("id")
    sub_collections = doc.collections()
    *_, last = sub_collections

    # subDocsList = []
    # sub_docs = last.stream()
    # for docs in sub_docs:
        # entries.id
        # subDocsList.append(docs.to_dict())

    subDocsList = readAllEntries(last, orderChild=None)
        
    return subDocsList


# ROOT Response
@app.route("/", methods=["GET"])
def index():

    # Render todays readings if exist
    todayKey = datetime.now().strftime("%d_%m_%Y")
    
    todayTempRef = temperatRef.collection(todayKey) # subcollection
    todayHumdRef = humidityRef.collection(todayKey)
    
    # Test first sensor document if in DB
    if not todayTempRef.document('A-1').get().exists:
        return 'No entries available today'
    else:
        readings = readAllEntries(todayTempRef)
        return render_template("index.html",
            readingsTemp=readAllEntries(todayTempRef),
            readingsHumd=readAllEntries(todayHumdRef)
        )


# CRUD Responses
@app.route('/add', methods = ['GET','POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        
        GET: Renders 'add' page to create an entry from a web form
        POST: Create an entry based upon url request with arg1:val1&arg2:val2 struct
    """
    try:
        # Make entry with a web form - makes Post thereafter
        if request.method == 'GET':
            return render_template("add.html", entry = {})
        
        # Make entry from request
        if request.method == 'POST':
        
            # Form entry
            if request.form: # Get form data if POST-ed through web form
            
                recvRequest = request.form
                readingType = recvRequest['reading']
                sensorID = recvRequest['sensorID']
                valReading = recvRequest['valReading']
                
            # URL entry
            else:
                # Check request parameters
                recvRequest = request.args
                if None in list(recvRequest.values()): # request.args returns a dictionary
                    abort(400) # Missing values in request
                
                # Check for valid collection
                readingType = recvRequest.get('reading')
                if not readingType in validDocs: # Only 2 types of valid documents
                    abort(400) # Not a valid measurement name
                
                # Get values to make new document
                sensorID = recvRequest.get('sensorID') # IF json is used instead: request.json['sensorID']
                valReading = recvRequest.get('val')
                
            # Create DB entry
            readingDb_ref = sensDb.document(readingType) # First hierarchy
            currentKey = datetime.now().strftime("%d_%m_%Y")
            thisSensor_ref = readingDb_ref.collection(currentKey).document(sensorID) # Second hierarchy - PUSH generates an unique entry key
            thisSensor_ref.set({
                u'VALUE': u'{}'.format(valReading),
                u'T_STAMP': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            })
             
            # CollectionReference has add().
            # DocumentReference has set(), update() and delete().
             
            return jsonify({"Success": True, "Received": recvRequest}), 200
        
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON
        
        if two URL argument are passed, return corresponding JSON entry
        if none are passed, return all sensor entries
    """
    try:
        # If two args are passed from request
        readingType = request.args.get('reading')
        readingDate = request.args.get('date')
        sensorID = request.args.get('sensorID')
        
        if readingType and readingDate and sensorID:
            
            sensorRoute = u'{root}/{reading}/{date}/{id}'.format(root=dBroot,reading=readingType,date=readingDate,id=sensorID)
            sensorEntry = db.document(sensorRoute).get().to_dict()
            sensorEntry["sensorID"] = sensorID

        # If no args are passed, return all Entries ordered by child 'sensorID'.
        else:

            temperatEntryList = extractSubCollections(temperatRef,orderChild='sensorID') # Pass temperature document reference
            humidityEntryList = extractSubCollections(humidityRef,orderChild='sensorID') # Pass humidity document reference
            
            sensorEntry = {
                'temperature': temperatEntryList,
                'humidity' : humidityEntryList,
            }
            
        if len(sensorEntry) == 0:
            abort(404)
        else:
            return jsonify(sensorEntry), 200
        
    except Exception as e:
        return f"An Error Occured: {e}"
        

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body
        Requires 'readingType' and 'sensorID'.
    """
    try:
    
        # Check request parameters
        if None in request.args.values(): #
            abort(400) # Missing values in request
        
        readingType = request.args.get('reading')
        sensorID = request.args.get('sensorID')
        readingDate = request.args.get('date')
        valToUpdate = request.args.get('updateVal')
        
        sensorRoute = u'{root}/{reading}/{date}/{id}'.format(root=dBroot,reading=readingType,date=readingDate,id=sensorID)
        sensorRef = sensDb.document(sensorRoute)
        sensorRef.child(u'VALUE').update(valToUpdate)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document or all subcollections
        if 'DELETE_ALL' url request passed, delete sensor collection
        if 'readingType' and 'sensorID' are passed, delete corresponding collection
    """
    try:
        
        # Check request parameters
        if None in request.args.values(): #
            abort(400) # Missing values in request
        
        # Check for DELETE_ALL in URL query
        DELETE_ALL = request.args.get('DELETE_ALL')
        
        # Deletes all readings of the 'reading type'
        if DELETE_ALL:
            sensorRef = sensDb.collection()
            delete_collection(sensorRef, batch_size=2) # batch_size=2 -> Delete up to hierarchy 1
            
        # Deletes only sensor ID of the 'reading type'
        else: 
        
            readingType = request.args.get('reading')
            sensorID = request.args.get('sensorID')
            
            DBrefRoute = u'/{document}/{subcoll}'.format(document=readingType,subcoll=sensorID)
            sensorRef = sensDb.collection(DBrefRoute)
            
            if len(sensorRef.items()) == 0:
                abort(404) # Requested reference is missing
            else: 
                delete_collection(sensorRef, batch_size=1) # batch_size=1 -> Delete up to hierarchy 2
                
        return jsonify({"success": True}), 200
        
    except Exception as e:
        return f"An Error Occured: {e}"


if __name__ == '__main__':
    if os.getenv('GAE_ENV', '').startswith('standard'):
        app.run()  # production
    else:
        port = int(os.environ.get('PORT', 5000)) # Get port from environment. If not set, use 5000 instead.
        app.run(threaded=False, port=port, host="localhost", debug=True)  # localhost test

