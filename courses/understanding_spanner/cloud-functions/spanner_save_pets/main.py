from google.cloud import spanner
import base64
import uuid
import json

instance_id = 'test-spanner-instance'
database_id = 'pets-db'

client = spanner.Client()
instance = client.instance(instance_id)
database = instance.database(database_id)

def spanner_save_pets(event, context):
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)

    # Check to see if the Owner already exists
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
            params = { "owner_id": owner_id,
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
                    """INSERT Owners (OwnerID, OwnerName) VALUES (@owner_id, @owner_name)""",
                    params=params,
                    param_types=param_types,)

                # Add the pet
            row_ct += transaction.execute_update(
                """INSERT Pets (PetID, OwnerID, PetName, PetType, Breed) VALUES (@pet_id, @owner_id, @pet_name, @pet_type, @breed)
                """,
                params=params,
                param_types=param_types,)
        except:
            row_ct = 0

        return row_ct

    row_ct = database.run_in_transaction(insert_owner_pet, data, owner_exists)

    print("{} record(s) inserted.".format(row_ct))
