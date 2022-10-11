# CRUD From URL
from firebase import firebase  
firebase = firebase.FirebaseApplication('https://xxxxx.firebaseio.com/', None)  

# CREATE
data =  {
    'Name': 'Vivek',
    'RollNo': 1,
    'Percentage': 76.02
}
result = firebase.post('/python-sample-ed7f7/Students/',data)
print(result)

# result prints {'name': '-LAgstkF0DT5l0IRucvm'} last entry 

curl -X PUT -d '{
 "eantoni": {
   "name": "Erika Antoni",
   "state": "California",
   "emails": {
     "primary": "eantoni@example.com",
     "secondary": "erika@work.com"
   }
 }' 'https://{db-name}.firebaseio.com/users.json'


# READ
result = firebase.get('/python-sample-ed7f7/Students/', '')
print(result)

curl 'https://{db-name}.firebaseio.com/users/eantoni.json?print=pretty'
curl 'https://{db-name}.firebaseio.com/users.json?orderBy="state"&print=pretty' 


# UPDATE
firebase.put('/python-sample-ed7f7/Students/-LAgstkF0DT5l0IRucvm','Percentage',79)
print('updated')

curl -X PATCH -d '{
 "address": "123 1st St., San Francisco, CA"}' \
'https://{db-name}.firebaseio.com/users/eantoni.json'

curl -X PATCH -d '{
 "eantoni/address": "123 1st St., San Francisco, CA"}' \
 'https://{db-name}.firebaseio.com/users.json'


# DELETE
firebase.delete('/python-sample-ed7f7/Students/', '-LAgt5rGRlPovwNhOsWK')
print('deleted')


curl -X DELETE 'https://{db-name}.firebaseio.com/users/eantoni.json' 
curl -X DELETE 'https://{db-name}.firebaseio.com/users/eantoni/emails/work.json' 


# RULES
# SET
curl -X PUT -d '{ "rules": { ".read": true, ".write": false } }' 
 'https://{db-name}.firebaseio.com/.settings/rules.json?
   access_token={access-token}'

# GET
curl 'https://{db-name}.firebaseio.com/.settings/rules.json?access_token={access-token}'

# AUTHENTIFICATION
curl -X GET 'https://{db-name}.firebaseio.com/users/eantoni.json?auth={cred}' 


