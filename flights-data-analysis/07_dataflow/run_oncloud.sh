~/apache-maven-3.3.9/bin/mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.dataanalyst.flights.CreateTrainingDataset \
      -Dexec.args="--project=cloud-training-demos \
      --stagingLocation=gs://cloud-training-demos/staging/ \
      --input=gs://cloud-training-demos/flights/201501.csv \
      --output=gs://cloud-training-demos/flights/chapter07 \
      --runner=BlockingDataflowPipelineRunner"
