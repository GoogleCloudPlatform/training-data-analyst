owner_uuid=$(cat /proc/sys/kernel/random/uuid)
pet_uuid=$(cat /proc/sys/kernel/random/uuid)

echo $owner_uuid
echo $pet_uuid


gcloud spanner rows insert --table=Owners --database=pets-db --instance=test-spanner-instance --data=OwnerID=$owner_uuid,OwnerName=Doug

gcloud spanner rows insert --table=Pets --database=pets-db --instance=test-spanner-instance --data=PetID=$pet_uuid,OwnerID=$owner_uuid,PetName='Noir',PetType='Dog',Breed='Schnoodle'

gcloud spanner rows insert --table=Pets --database=pets-db --instance=test-spanner-instance --data=PetID=$(cat /proc/sys/kernel/random/uuid),OwnerID=$owner_uuid,PetName='Bree',PetType='Dog',Breed='Mutt'

gcloud spanner rows insert --table=Pets --database=pets-db --instance=test-spanner-instance --data=PetID=$(cat /proc/sys/kernel/random/uuid),OwnerID=$owner_uuid,PetName='Gigi',PetType='Dog',Breed='Retriever'
