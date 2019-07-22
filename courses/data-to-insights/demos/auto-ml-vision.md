# Video: AutoML Vision Demo
Goal: Explore how to create a custom image classification model with no code using [AutoML Vision](https://cloud.google.com/vision/automl/docs/).

## Open the demo video
* [AutoML Vision: classifying dog breeds (6min 19s)](https://youtu.be/5EntDh5Ylf4)
* Demo contains no audio. Below is a timestamp transcript of the narrative to explain:

### Narrative:
We have a [Stanford image dataset](https://www.kaggle.com/jessicali9530/stanford-dogs-dataset) of 20,000 images of 120 dog breeds. Let's see if we can classify different breeds of dogs automatically with an image recognition model.

### Introduction 
00:00 - 00:46
* We have Beagles, Walker Hounds, Bloodhounds as our three classes
* Let's try the Vision API route first (which is pretrained). Can it recognize a Walker Hound breed or will it think it's just a 'dog' image?
* Vision API: The pretrained model doesn't do well at recognizing our specific breed (it guesses too many and our Walker Hound isn't present as a label)

### Let's try AutoML
00:46 - 
* AutoML Vision let's you provide your own images and create custom classification models with no code
* AutoML also has Tables, Natural Language and other products besides Vision

1:19 -
* In the AutoML Vision UI, we need to create a dataset
* Recommended at least 100 images per class (subject to change)

1:50 - 
* We have local folder for our images of dog breeds. Let's examine the photos of Bloodhounds

### Creating an AutoML Vision Dataset
2:10 - 
* We need to provide a mapping CSV file that gives the model links to our images (training data) as well as a column for the label (which correct dog breed is it)
* 2:15 - here's what that two column CSV file looks like
* 2:27 - we confirm each of our three breeds are present in our labels
* 2:35 - we specify the CSV in AutoML and import the dataset
* 2:40 - AutoML Vision will try and autodetect duplicate images (even if they have different filenames)
* 3:08 - the left side shows the number of images per label in our dataset. You can click on a label to view the images. Let's inspect each dog breed.

### Model Training
3:32 - 
* Time to train the model
* 3:45 - did you pick up that one of our classes only had 82 instances earlier? The Walker_hound was flagged as needing more data
* 3:48 - your images will be automatically split into training, validation, and testing for you
* 4:06 - let's start training. You'll note that we'll do cloud-hosted training but you can also try Edge if you want your model to run on mobile devices etc.

### Evaluation 
4:28 - 
* Time to evaluate model performance
* AutoML Vision trained on 458 images in 3 labels 
* Overall Precision was 88%
* Overall Recall was 88% as well
* 4:45 - let's see the Full Evaluation
* In the Confusion Matrix, you quickly see where misclassifications occured. You can see here in Orange that the model often thought the image was a Beagle when in fact it was a Walker_hound.
* 5:10 - let's drill into that issue and find specific instances. Here are the true positives and the false negatives. What could you do to help the model understand the difference between Walker Hounds and Beagles better? Add more training data!

### Predictions
5:33 - 
* Time to predict on an image the model hasn't seen before
* You can upload an image or invoke your model via an API
* Let's upload three images I downloaded from the internet that weren't part of our original dataset
* 5:52 - here is the custom model's predictions for each new image. As you can see the model had no trouble with the Bloodhound or the Walker hound but was only 83% sure of the Beagle. 
* One big takeaway is to increase the number of Beagle images in our training dataset for the model to learn from












