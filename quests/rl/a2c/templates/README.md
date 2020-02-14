# Actor-Critic Deploy to Docker

This readme is a set of instructions on how to incoporate the actor-critic templates in this folder into the docker environment set up in the rl/dqn folder.

To start, run the following code in a terminal to copy over the needed files and replace the dqn files with their respective actor-critic templates.

    [ -e policy_gradients ] && rm -r policy_gradients
    cp -r ../../dqn policy_gradients
    rm policy_gradients/dqns_on_gcp.ipynb
    rm -r policy_gradients/images
    cp hyperparam.yaml policy_gradients/hyperparam.yaml
    cp model.py policy_gradients/trainer/model.py
    cp trainer.py policy_gradients/trainer/trainer.py

Run the below cell to build the docker container and store it on Goolge Cloud. Replace the PROJECT and BUCKET variables with your respective Google Cloud Project and Bucket IDs.

    PROJECT=your-project-id
    BUCKET=your-bucket-id
    JOB_NAME=a2c_on_gcp$(date -u +%y%m%d_%H%M%S)
    REGION='us-central1'
    IMAGE_URI=gcr.io/$PROJECT/a2c_on_gcp

    docker build -f policy_gradients/Dockerfile -t $IMAGE_URI ./
    docker push $IMAGE_URI
    
Hyperparameter tuning can then be deployed with the following:

    gcloud ai-platform jobs submit training $JOB_NAME \
        --staging-bucket=gs://$BUCKET  \
        --region=$REGION  \
        --master-image-uri=$IMAGE_URI \
        --scale-tier=BASIC_GPU\
        --job-dir=gs://$BUCKET/$JOB_NAME \
        --config=hyperparam.yaml
