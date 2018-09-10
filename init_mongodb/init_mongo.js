let error = true

pase = db.getSiblingDB('pase')
let res = [
  db.adminCommand('listDatabases'),
  pase.createUser({'user': 'root', 'pwd': 'example', 'roles': [{'role': 'readWrite', 'db': 'pase'}, {'role': 'dbAdmin', 'db': 'pase'}]}),
  pase.getUsers()
]

printjson(res)

print('Done initializing!')