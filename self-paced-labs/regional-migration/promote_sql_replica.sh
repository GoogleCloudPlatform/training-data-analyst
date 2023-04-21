#start time of deployment
start=`date +%s`

# read Property File
FILE_NAME=$1
# Key in Property File
key="Name"
# Variable to hold the Property Value
prop_value=""
getProperty()
{
    prop_key=$1
	prop_value=`cat ${FILE_NAME} | grep ${prop_key} | cut -d'=' -f2`
}

getProperty replicaName
echo "Key = replicaName ; Value = " ${prop_value}
replicaName=${prop_value}

getProperty newReplicaName
echo "Key = newReplicaName ; Value = " ${prop_value}
newReplicaName=${prop_value}

getProperty masterInstanceName
echo "Key = masterInstanceName ; Value = " ${prop_value}
masterInstanceName=${prop_value}

getProperty targetRegion
echo "Key = targetRegion ; Value = " ${prop_value}
targetRegion=${prop_value}

getProperty project
echo "Key = project ; Value = " ${prop_value}
project=${prop_value}

getProperty env
echo "Key = env ; Value = " ${prop_value}
env=${prop_value}

getProperty network
echo "Key = network ; Value = " ${prop_value}
network=${prop_value}

getProperty dnsName
echo "Key = dnsName ; Value = " ${prop_value}
dnsName=${prop_value}

getProperty dnsZoneName
echo "Key = dnsZoneName ; Value = " ${prop_value}
dnsZoneName=${prop_value}

gcloud config set project $project

#Make the primary instance unavailable

## remove the cross-region read replica from the primary
gcloud sql instances patch $replicaName --no-enable-database-replication
gcloud sql instances patch $masterInstanceName --activation-policy NEVER

#promote the cross-region read replica
gcloud sql instances promote-replica $replicaName --quiet

#start new primary instance
gcloud sql instances patch $replicaName --activation-policy ALWAYS

#Update Cloud DNS with name "mysql.test.local." to point to promoted Cloud SQL instance
gcloud dns --project=$project record-sets update $dnsName --type="A" --zone=$dnsZoneName --rrdatas=$(gcloud sql instances describe $replicaName --project $project --format 'value(ipAddresses.ipAddress)' --project $project ) --ttl="5" --quiet

echo "gcloud beta sql instances create $newReplicaName --project=$project --master-instance-name=$replicaName --network=$network --no-assign-ip --region=$targetRegion --labels env=$env"
gcloud beta sql instances create $newReplicaName --project=$project --master-instance-name=$replicaName --network=$network --no-assign-ip --region $targetRegion --labels env=$env --quiet

end=`date +%s`

runtime=$((end - start))
echo "Deployment total execution time is $runtime second/seconds with primary primary Cloud SQL instance $replicaName "
