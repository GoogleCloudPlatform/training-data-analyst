## Command-line
* In CloudShell, or in another enviroment where the gcloud SDK is installed:
  * Run ./create_subscription.sh to create a subscription.  As new GOES files are added to the public data bucket, details about the files will populate this subscription. The messages will persist until you consume the message (to a maximum of 7 days)
  * Consume one message by ./pull_message.sh
    It is likely that the number of messages will be zero the first time. Wait a couple of minutes.
  * Once you get a objectId, you can verify that the file exists:
   ```
   objectId=ABI-L2-MCMIPF/2017/306/21/OR_ABI-L2-MCMIPF-M4_G16_s20173062105222_e20173062110034_c20173062110127.nc
   ```
   You can verify that it exists using:
   ```
   gsutil ls -l gs://gcp-public-data-goes-16/ABI-L2-MCMIPF/2017/306/21/OR_ABI-L2-MCMIPF-M4_G16_s20173062105222_e20173062110034_c20173062110127.nc
   ```
  * Delete the subscription using ./delete_subscription.sh

## Dataflow-Java (TODO)
Here is how you can write a Apache Beam pipeline to create a subscription, monitor the topic, and do some processing of the files

 
## Dataflow-Python (TODO)
Here is how you can write a Apache Beam pipeline to create a subscription, monitor the topic, and do some processing of the files
