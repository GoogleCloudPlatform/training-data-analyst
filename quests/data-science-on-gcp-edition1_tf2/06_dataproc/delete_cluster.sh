if [ "$#" -ne 1 ]; then
    echo "Usage: ./delete_cluster.sh region"
    exit
fi

gcloud dataproc clusters delete ch6cluster --region $1