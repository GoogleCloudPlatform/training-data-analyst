PROJECT=seldon-demos
FS=pipeline-data
ZONE=europe-west1-b    

gcloud beta filestore instances create ${FS}     --project=${PROJECT}     --zone=${ZONE}     --tier=STANDARD     --file-share=name="volumes",capacity=1TB     --network=name="default",reserved-ip-range="10.0.0.0/29"

FSADDR=$(gcloud beta filestore instances describe ${FS} --project=${PROJECT} --zone=${ZONE} --format="value(networks.ipAddresses[0])")

helm install nfs-cp stable/nfs-client-provisioner --set nfs.server=${FSADDR} --set nfs.path=/volumes --namespace=kubeflow 

kubectl rollout status  deploy/nfs-cp-nfs-client-provisioner -n kubeflow
