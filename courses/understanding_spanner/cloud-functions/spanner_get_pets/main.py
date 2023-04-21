from google.cloud import spanner

instance_id = 'test-spanner-instance'
database_id = 'pets-db'

client = spanner.Client()
instance = client.instance(instance_id)
database = instance.database(database_id)

def spanner_get_pets(request):
    query = """SELECT OwnerName, PetName, PetType, Breed 
         FROM Owners 
         JOIN Pets ON Owners.OwnerID = Pets.OwnerID;"""

    outputs = []
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(query)
        output = '<div>OwnerName,PetName,PetType,Breed</div>'
        outputs.append(output)
        for row in results:
            output = '<div>{},{},{},{}</div>'.format(*row)
            outputs.append(output)

    return '\n'.join(outputs)
