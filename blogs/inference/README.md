
## Set up service account
* Go to https://console.cloud.google.com/apis/credentials/serviceaccountkey
* Create a new service account with role project/owner
* download JSON key
* save as a file with the name .access_key (note the dot, so that you don't mistakenly check it into source control) in this directory

## GDELT
* Create dataset using ```./create_dataset.sh gdelt/create_dataset.json```
* Make sure creation is finished using ```./list_datasets.sh```
* Query dataset for items correlated with ```India``` using ```./query_dataset.sh gdelt_2018_04_data gdelt/query_india.json```

## 
