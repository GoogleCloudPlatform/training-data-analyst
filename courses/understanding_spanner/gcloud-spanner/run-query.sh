gcloud spanner databases execute-sql pets-db --instance=test-spanner-instance --sql='SELECT o.OwnerName, p.PetName, p.PetType, p.Breed FROM Owners as o JOIN Pets AS p ON o.OwnerID = p.OwnerID' 
