gcloud spanner instances create test-spanner-instance --config=regional-us-central1 --description="test-spanner-instance" --processing-units=100

gcloud spanner databases create pets-db --instance=test-spanner-instance --database-dialect=GOOGLE_STANDARD_SQL --ddl-file=./pets-db-schema.sql


