gsutil rm -r gs://cloud-training-demos/flights/pigoutput
gcloud beta dataproc jobs submit pig --cluster cluster-1 --file bayes_final.pig
