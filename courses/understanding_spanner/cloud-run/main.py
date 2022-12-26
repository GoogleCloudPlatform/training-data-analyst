from google.cloud import spanner
from flask import Flask, request
from flask_restful import Resource, Api
from flask import jsonify
import uuid
import os
 
# Get the Instance ID and database ID from environment variables
# Use the emulator if the env variables are not set.
# Requires the start-spanner-emulator.sh script be run. 
if "INSTANCE_ID" in os.environ:
    instance_id = os.environ["INSTANCE_ID"]
else:
    instance_id = 'emulator-instance'

if "DATABASE_ID" in os.environ:
    database_id = os.environ["DATABASE_ID"]
else:
    database_id = 'pets-db'

client = spanner.Client()
instance = client.instance(instance_id)
database = instance.database(database_id)

app = Flask(__name__)
api = Api(app)

class PetsList(Resource):
    def get(self):
        query = """SELECT Owners.OwnerID, OwnerName,
                   PetID, PetName, PetType, Breed
                   FROM Owners
                   JOIN Pets ON Owners.OwnerID = Pets.OwnerID;"""

        pets = []
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(query)
            for row in results:
                pet = {'OwnerID': row[0],
                       'OwnerName': row[1],
                       'PetID': row[2],
                       'PetName': row[3],
                       'PetType': row[4],
                       'Breed': row[5], }
                pets.append(pet)
            return pets, 200

    def post(self):
        # Check to see if the Owner already exists
        data = request.get_json(True)
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql("""
               SELECT OwnerID FROM OWNERS 
               WHERE OwnerName = @owner_name""", 
               params={"owner_name": data["OwnerName"]},
               param_types={"owner_name": spanner.param_types.STRING})

        row = results.one_or_none()
        if row != None:
            owner_exists = True
            owner_id = row[0]
        else:
            owner_exists = False
            owner_id = str(uuid.uuid4())

        # Need a UUID for the new pet
        pet_id = str(uuid.uuid4())
        
        def insert_owner_pet(transaction, data, owner_exists):
            try:
                row_ct = 0
                params = {"owner_id": owner_id,
                          "owner_name": data["OwnerName"],
                          "pet_id": pet_id,
                          "pet_name": data["PetName"],
                          "pet_type": data["PetType"],
                          "breed": data["Breed"],
                         }

                param_types = { "owner_id": spanner.param_types.STRING,
                                "owner_name": spanner.param_types.STRING,
                                "pet_id": spanner.param_types.STRING,
                                "pet_name": spanner.param_types.STRING,
                                "pet_type": spanner.param_types.STRING,
                                "breed": spanner.param_types.STRING,
                              }

                # Only add the Owner if they don't exist already
                if not owner_exists:
                    row_ct = transaction.execute_update(
                    """INSERT Owners (OwnerID, OwnerName)
                       VALUES (@owner_id, @owner_name)""",
                    params=params,
                    param_types=param_types,)

                # Add the pet
                row_ct += transaction.execute_update(
                    """INSERT Pets (PetID, OwnerID, PetName, PetType, Breed)
                        VALUES (@pet_id, @owner_id, @pet_name, @pet_type, @breed)""",
                    params=params,
                    param_types=param_types,)

            except:
                row_ct = 0

            return row_ct

        row_ct = database.run_in_transaction(insert_owner_pet, data, owner_exists)

        return "{} record(s) inserted.".format(row_ct), 201

    def delete(self):

        # This delete all the Owners and Pets
        # Uses Cascading Delete on interleaved Pets table
        def delete_owners(transaction):
            row_ct = transaction.execute_update(
            "DELETE FROM Owners WHERE true = true")

            return row_ct


        row_ct = database.run_in_transaction(delete_owners)
        return "{} record(s) deleted.".format(row_ct), 201
        
class Pet(Resource):
    def get(self, pet_id):

        params = {"pet_id": pet_id}
        param_types = {
            "pet_id": spanner.param_types.STRING,
        }

        query = """SELECT Owners.OwnerID, OwnerName,
                   PetID, PetName, PetType, Breed
                   FROM Owners
                   JOIN Pets ON Owners.OwnerID = Pets.OwnerID
                   WHERE PetID = @pet_id; """

        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                    query, params=params, param_types=param_types,)
            
            pet = None
            for row in results:
                pet = {'OwnerID': row[0],
                       'OwnerName': row[1],
                       'PetID': row[2],
                       'PetName': row[3],
                       'PetType': row[4],
                       'Breed': row[5], }
            
            if pet:
                return pet, 200
            else:
                return "Not found", 404


    def patch(self, pet_id):
        # This woud be for an Update
        return "Not Implemented", 500

    def delete(self, pet_id):
        # This woud be for a Delete
        return "Not Implemented", 500


api.add_resource(PetsList, '/pets')
api.add_resource(Pet, '/pets/<pet_id>')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return 'An internal error occurred.', 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
