# Apache Beam Notebooks for Streaming NLP on Real-time Tweets

This directory contains files for a live demo using real-time tweets from Twitter to build a streaming Apache Beam pipeline to perform sentiment analysis. This demo is intended to be run in the Apache Beam Notebook environment as currently offered on Google Cloud.

To run this demo you need a [Twitter Developer account](https://developer.twitter.com/). The free version of the account will be all you need to create an application and recieve the necessary API keys. However, this is something that does need to be set up in advance for the demo. 

There are three files in this directory:

1. `TweetPipeline.ipynb`: Notebook containing the main part of the demo. In this notebook you will see information about the client gathering the tweets, build a streaming Beam pipeline using ML APIs to understand the tweets, explore the pipeline interactively using the interactive runner, and ultimately submit your pipeline as a streaming pipeline on Dataflow. The commentary in this notebook can serve as a "demo walkthrough".

2. `tweet-setup.sh`: This bash script installs the Python packages needed to run the `tweets-gatherer.py` and sets the variables needed for the script, including Twitter Developer API keys. The keys will need to be added manually before running the script.

3. `tweet-gatherer.py`: A python script using the `tweepy` API to gather tweets from Twitter meeting the search term "pizza" and publish them to Pub/Sub. This script is not a focus of the demo and is not explored beyond its usage.

**Note:** As of writing, occasionally the `ib.show()` method in the notebook fails to run stating "Transform node not replaced as expected". If this occurs, then restart the kernel and run cells other than `ib.show()` cells until you return to the same point in the notebook.