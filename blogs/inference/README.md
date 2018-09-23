
## Set up service account and obtain a key to access the service
* Ensure the inference API is enabled on your project by going to https://console.cloud.google.com/apis/
* In CloudShell, git clone this repository and cd to this directory
* Run ```./create_key.sh```

## GDELT
* Create dataset using ```./create_dataset.sh gdelt/create_dataset.json```
* Run ```./list_datasets.sh``` and wait for status to change to ```LOADED```
* Query dataset for items correlated with ```India``` using ```./query_dataset.sh gdelt_2018_04_data gdelt/query_india.json```
* Try out other queries in the ```gdelt``` folder

## Flights (air traffic by airport)
* Pip install apache-beam if needed: ```flights/install_packages.sh```
* Run Dataflow job to create JSON files: ```flights/create_json.sh```
* Wait for Dataflow job to finish by monitoring the [Dataflow console](https://console.cloud.google.com/dataflow)
* Combine the ten files into a single one: ```flights/compose_gcs.sh```
* Edit ```flights/create_dataset.json``` to reflect your bucket name
* Create inference API dataset: ```./create_dataset.sh flights/create_dataset.json```
* Run ```./list_datasets.sh``` and wait for status to change to ```LOADED```
* Query for the typical arrival delay on flights from DFW using ```./query_dataset.sh flights_data flights/query1.json```
* Try out other queries in the ```flights``` folder

