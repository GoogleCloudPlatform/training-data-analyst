echo "Creating Spanner Instance..."
gcloud spanner instances create challenge-lab-instance --config=regional-$1 --description="challenge-lab-instance" --processing-units=100

echo "Creating Spanner Database..."
gcloud spanner databases create orders-db --instance=challenge-lab-instance --database-dialect=GOOGLE_STANDARD_SQL --ddl-file=./orders-db-schema.sql


echo "Installing Apache Beam Prerequities..."
pip install apache-beam[gcp]==2.42.0
pip install apache-beam[dataframe]


echo "Import customers table..."
python import-customers-to-spanner.py

echo "Import orders table..."
python import-orders-to-spanner.py

echo "Import details table..."
python import-details-to-spanner.py

echo "Import products table..."
python import-products-to-spanner.py

