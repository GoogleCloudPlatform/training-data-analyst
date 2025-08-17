(0) */training/sensor_magic.sh* causes an error, specifically send_sensor_data.py from most Data Engineering Qwiklabs; 
        -> Traceback (most recent call last):
        ->   File "./send_sensor_data.py", line 22, in <module>
        ->     from google.cloud import pubsub
        -> ImportError: No module named 'google'

(1) First of all, simply try to run:
        python send_sensor_data.py --speedFactor=30 --project [PROJECT]
        Or
        (python send_sensor_data.py [-h] -- speedFactor SPEEDFACTOR --project PROJECT)
        
        Should work just fine.
        
    If this fails, look at your error.  Is it because a module could not be found
    or is it because the pubsub module has no attribute named 'Client'?

(2) If this fails because google.cloud.pubsub can not be found, then do:
        sudo pip install google-cloud-pubsub
    Then, try again

(3) If you get a failure that the module pubsub has no attribute called Client
    then you are either:
    - running into path problems because an older version of pub/sub is installed on your machine
    - trying to use a newer version of pub/sub

    The solution is to use virtualenv:

    (a) virtualenv cpb104
    (b) source cpb104/bin/activate
    (c) pip install google-cloud-pubsub==0.27.0
    (d) gcloud auth application-default login

    Then, try the send_sensor_data.py again

    To exit the virtualenv environment, type 'deactivate'
