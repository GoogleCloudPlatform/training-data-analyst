~/apache-maven-3.3.9/bin/mvn compile exec:java \
 -Dexec.mainClass=com.google.cloud.training.dataanalyst.flights.PredictRealtime \
      -Dexec.args="--project=cloud-training-demos \
      --stagingLocation=gs://cloud-training-demos/staging/ \
      --input=gs://cloud-training-demos/flights/2015*.csv \
      --output=gs://cloud-training-demos/flights/chapter09/ \
      --runner=BlockingDataflowPipelineRunner"
