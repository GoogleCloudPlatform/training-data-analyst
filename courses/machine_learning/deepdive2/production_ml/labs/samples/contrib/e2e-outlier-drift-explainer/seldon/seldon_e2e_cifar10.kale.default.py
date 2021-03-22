import kfp.dsl as dsl
import json
import kfp.components as comp
from collections import OrderedDict
from kubernetes import client as k8s_client


def setup(MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    minioClient = get_minio()
    buckets = minioClient.list_buckets()
    for bucket in buckets:
        print(bucket.name, bucket.creation_date)
    '''

    block4 = '''
    if not minioClient.bucket_exists(MINIO_MODEL_BUCKET):
        minioClient.make_bucket(MINIO_MODEL_BUCKET)
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/setup.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('setup')

    _kale_mlmd_utils.call("mark_execution_complete")


def train_model_and_explainer(CIFAR10_MODEL_PATH: str, EXPLAINER_MODEL_PATH: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    CIFAR10_MODEL_PATH = "{}"
    EXPLAINER_MODEL_PATH = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(CIFAR10_MODEL_PATH, EXPLAINER_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    model = fetch_tf_model('cifar10', 'resnet32')
    '''

    block4 = '''
    train, test = tf.keras.datasets.cifar10.load_data()
    X_train, y_train = train
    X_test, y_test = test

    X_train = X_train.astype('float32') / 255
    X_test = X_test.astype('float32') / 255
    print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)
    '''

    block5 = '''
    class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer',
                   'dog', 'frog', 'horse', 'ship', 'truck']
    '''

    block6 = '''
    idx = 1
    X = X_test[idx].reshape(1, 32, 32, 3)
    plt.imshow(X.reshape(32, 32, 3))
    plt.axis('off')
    plt.show()
    print("class:",class_names[y_test[idx][0]])
    print("prediction:",class_names[model.predict(X_test[idx:idx+1])[0].argmax()])
    '''

    block7 = '''
    modelfilepath="resnet"
    tf.saved_model.save(model, modelfilepath)
    '''

    block8 = '''
    from os import listdir
    from os.path import isfile, join

    model_filepath="resnet"
    print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{CIFAR10_MODEL_PATH}/1/saved_model.pb", modelfilepath+"/saved_model.pb"))
    variable_filepath = modelfilepath+"/variables"
    onlyfiles = [f for f in listdir(variable_filepath) if isfile(join(variable_filepath, f))]
    for filename in onlyfiles:
        print(filename)
        print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{CIFAR10_MODEL_PATH}/1/variables/{filename}", join(variable_filepath, filename)))
    '''

    block9 = '''
    def predict_fn(x):
        return model.predict(x)
    '''

    block10 = '''
    
    image_shape = (32, 32, 3)
    segmentation_fn = 'slic'
    kwargs = {'n_segments': 5, 'compactness': 20, 'sigma': .5}
    explainer = AnchorImage(predict_fn, image_shape, segmentation_fn=segmentation_fn, 
                            segmentation_kwargs=kwargs, images_background=None)
    '''

    block11 = '''
    idx=0
    image = X_test[0]
    np.random.seed(0)
    explanation = explainer.explain(image, threshold=.95, p_sample=.5, tau=0.25)
    '''

    block12 = '''
    X = X_test[idx].reshape(1, 32, 32, 3)
    plt.imshow(X.reshape(32, 32, 3))
    plt.axis('off')
    plt.show()
    print("class:",class_names[y_test[idx][0]])
    print("prediction:",class_names[model.predict(X_test[idx:idx+1])[0].argmax()])
    '''

    block13 = '''
    plt.imshow(explanation["anchor"])
    '''

    block14 = '''
    with open("explainer.dill", "wb") as dill_file:
        dill.dump(explainer, dill_file)    
        dill_file.close()
    print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{EXPLAINER_MODEL_PATH}/explainer.dill", 'explainer.dill'))
    '''

    data_saving_block = '''
    # -----------------------DATA SAVING START---------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.save(X_test, "X_test")
    _kale_marshal_utils.save(X_train, "X_train")
    _kale_marshal_utils.save(class_names, "class_names")
    _kale_marshal_utils.save(y_test, "y_test")
    _kale_marshal_utils.save(y_train, "y_train")
    # -----------------------DATA SAVING END-----------------------------------
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              block6,
              block7,
              block8,
              block9,
              block10,
              block11,
              block12,
              block13,
              block14,
              data_saving_block)
    html_artifact = _kale_run_code(blocks)
    with open("/train_model_and_explainer.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('train_model_and_explainer')

    _kale_mlmd_utils.call("mark_execution_complete")


def deploy_model(CIFAR10_MODEL_PATH: str, DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    CIFAR10_MODEL_PATH = "{}"
    DEPLOY_NAMESPACE = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(CIFAR10_MODEL_PATH, DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_test = _kale_marshal_utils.load("X_test")
    class_names = _kale_marshal_utils.load("class_names")
    y_test = _kale_marshal_utils.load("y_test")
    # -----------------------DATA LOADING END----------------------------------
    '''

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    secret = f"""apiVersion: v1
    kind: Secret
    metadata:
      name: seldon-init-container-secret
      namespace: {DEPLOY_NAMESPACE}
    type: Opaque
    stringData:
      AWS_ACCESS_KEY_ID: {MINIO_ACCESS_KEY}
      AWS_SECRET_ACCESS_KEY: {MINIO_SECRET_KEY}
      AWS_ENDPOINT_URL: http://{MINIO_HOST}
      USE_SSL: "false"
    """
    with open("secret.yaml","w") as f:
        f.write(secret)
    run("cat secret.yaml | kubectl apply -f -", shell=True)
    '''

    block4 = '''
    sa = f"""apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: minio-sa
      namespace: {DEPLOY_NAMESPACE}
    secrets:
      - name: seldon-init-container-secret
    """
    with open("sa.yaml","w") as f:
        f.write(sa)
    run("kubectl apply -f sa.yaml", shell=True)
    '''

    block5 = '''
    model_yaml=f"""apiVersion: machinelearning.seldon.io/v1
    kind: SeldonDeployment
    metadata:
      name: cifar10-classifier
      namespace: {DEPLOY_NAMESPACE}
    spec:
      protocol: tensorflow
      predictors:
      - componentSpecs:
        graph:
          implementation: TENSORFLOW_SERVER
          modelUri: s3://{MINIO_MODEL_BUCKET}/{CIFAR10_MODEL_PATH}
          envSecretRefName: seldon-init-container-secret
          name: classifier
          logger:
             mode: all
        explainer:
          type: AnchorImages
        name: default
        replicas: 1
    """
    with open("model.yaml","w") as f:
        f.write(model_yaml)
    run("kubectl apply -f model.yaml", shell=True)
    '''

    block6 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l seldon-deployment-id=cifar10-classifier -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
    '''

    block7 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l seldon-deployment-id=cifar10-classifier -o jsonpath='{{.items[1].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
    '''

    block8 = '''
    def test_model():
     idx=10
     test_example=X_test[idx:idx+1].tolist()
     payload='{"instances":'+f"{test_example}"+' }'
     cmd=f"""curl -d '{payload}' \\
       http://cifar10-classifier-default.{DEPLOY_NAMESPACE}:8000/v1/models/classifier/:predict \\
       -H "Content-Type: application/json"
     """
     ret = Popen(cmd, shell=True,stdout=PIPE)
     raw = ret.stdout.read().decode("utf-8")
     print(raw)
     res=json.loads(raw)
     arr=np.array(res["predictions"])
     X = X_test[idx].reshape(1, 32, 32, 3)
     plt.imshow(X.reshape(32, 32, 3))
     plt.axis('off')
     plt.show()
     print("class:",class_names[y_test[idx][0]])
     print("prediction:",class_names[arr[0].argmax()])

    ok = False
    while not ok:
        try:
            test_model()
            ok = True
        except:
            print("Failed calling model, sleeping")
            time.sleep(2)
    '''

    block9 = '''
    idx=10
    test_example=X_test[idx:idx+1].tolist()
    payload='{"instances":'+f"{test_example}"+' }'
    cmd=f"""curl -d '{payload}' \\
       http://cifar10-classifier-default-explainer.{DEPLOY_NAMESPACE}:9000/v1/models/cifar10-classifier/:explain \\
       -H "Content-Type: application/json"
    """
    ret = Popen(cmd, shell=True,stdout=PIPE)
    raw = ret.stdout.read().decode("utf-8")
    print(raw)
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block, data_loading_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              block6,
              block7,
              block8,
              block9,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/deploy_model.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('deploy_model')

    _kale_mlmd_utils.call("mark_execution_complete")


def train_drift_detector(DRIFT_MODEL_PATH: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    DRIFT_MODEL_PATH = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(DRIFT_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_test = _kale_marshal_utils.load("X_test")
    y_test = _kale_marshal_utils.load("y_test")
    # -----------------------DATA LOADING END----------------------------------
    '''

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    import tensorflow as tf
    from tensorflow.keras.layers import Conv2D, Dense, Flatten, InputLayer, Reshape

    from alibi_detect.cd import KSDrift
    from alibi_detect.cd.preprocess import uae, hidden_output
    from alibi_detect.models.resnet import scale_by_instance
    from alibi_detect.utils.fetching import fetch_tf_model, fetch_detector
    from alibi_detect.utils.prediction import predict_batch
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.datasets import fetch_cifar10c, corruption_types_cifar10c
    '''

    block4 = '''
    tf.random.set_seed(0)

    if True:
        np.random.seed(0)
        n_test = X_test.shape[0]
        idx = np.random.choice(n_test, size=n_test // 2, replace=False)
        idx_h0 = np.delete(np.arange(n_test), idx, axis=0)
        X_ref,y_ref = X_test[idx], y_test[idx]
        X_h0, y_h0 = X_test[idx_h0], y_test[idx_h0]
        print(X_ref.shape, X_h0.shape)
        # define encoder
        encoding_dim = 32
        encoder_net = tf.keras.Sequential(
          [
              InputLayer(input_shape=(32, 32, 3)),
              Conv2D(64, 4, strides=2, padding='same', activation=tf.nn.relu),
              Conv2D(128, 4, strides=2, padding='same', activation=tf.nn.relu),
              Conv2D(512, 4, strides=2, padding='same', activation=tf.nn.relu),
              Flatten(),
              Dense(encoding_dim,)
          ]
        )

        # initialise drift detector
        p_val = .05
        cd = KSDrift(
            p_val=p_val,        # p-value for K-S test
            X_ref=X_ref,       # test against original test set
            preprocess_fn=uae,  # UAE for dimensionality reduction
            preprocess_kwargs={'encoder_net': encoder_net, 'batch_size': 128},
            alternative='two-sided'  # other options: 'less', 'greater'
        )
    else:
        cd = load_detector("/home/models/samples/cd/cifar10")
    '''

    block5 = '''
    from alibi_detect.utils.saving import save_detector, load_detector
    from os import listdir
    from os.path import isfile, join

    filepath="cifar10Drift"
    save_detector(cd, filepath) 
    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    for filename in onlyfiles:
        print(filename)
        print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{DRIFT_MODEL_PATH}/{filename}", join(filepath, filename)))
    filepath="cifar10Drift/model"
    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    for filename in onlyfiles:
        print(filename)
        print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{DRIFT_MODEL_PATH}/model/{filename}", join(filepath, filename)))
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block, data_loading_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/train_drift_detector.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('train_drift_detector')

    _kale_mlmd_utils.call("mark_execution_complete")


def train_outlier_detector(MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str, OUTLIER_MODEL_PATH: str, TRAIN_OUTLIER_DETECTOR: bool):
    pipeline_parameters_block = '''
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    OUTLIER_MODEL_PATH = "{}"
    TRAIN_OUTLIER_DETECTOR = {}
    '''.format(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH, TRAIN_OUTLIER_DETECTOR)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_train = _kale_marshal_utils.load("X_train")
    # -----------------------DATA LOADING END----------------------------------
    '''

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    import logging
    import matplotlib.pyplot as plt
    import numpy as np
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block4 = '''
    if TRAIN_OUTLIER_DETECTOR:
        latent_dim = 1024
        
        encoder_net = tf.keras.Sequential(
            [
                InputLayer(input_shape=(32, 32, 3)),
                Conv2D(64, 4, strides=2, padding='same', activation=tf.nn.relu),
                Conv2D(128, 4, strides=2, padding='same', activation=tf.nn.relu),
                Conv2D(512, 4, strides=2, padding='same', activation=tf.nn.relu)
            ])

        decoder_net = tf.keras.Sequential(
            [
                InputLayer(input_shape=(latent_dim,)),
                Dense(4*4*128),
                Reshape(target_shape=(4, 4, 128)),
                Conv2DTranspose(256, 4, strides=2, padding='same', activation=tf.nn.relu),
                Conv2DTranspose(64, 4, strides=2, padding='same', activation=tf.nn.relu),
                Conv2DTranspose(3, 4, strides=2, padding='same', activation='sigmoid')
            ])
        
         # initialize outlier detector
        od = OutlierVAE(threshold=.015,  # threshold for outlier score
                    score_type='mse',  # use MSE of reconstruction error for outlier detection
                    encoder_net=encoder_net,  # can also pass VAE model instead
                    decoder_net=decoder_net,  # of separate encoder and decoder
                    latent_dim=latent_dim,
                    samples=2)
        # train
        od.fit(X_train, 
                loss_fn=elbo,
                cov_elbo=dict(sim=.05),
                epochs=50,
                verbose=True)
    else:
        od = load_detector("/home/models/samples/od/cifar10")
    '''

    block5 = '''
    idx = 8
    X = X_train[idx].reshape(1, 32, 32, 3)
    X_recon = od.vae(X)
    plt.imshow(X.reshape(32, 32, 3))
    plt.axis('off')
    plt.show()
    plt.imshow(X_recon.numpy().reshape(32, 32, 3))
    plt.axis('off')
    plt.show()
    '''

    block6 = '''
    X = X_train[:500]
    print(X.shape)
    od_preds = od.predict(X,
                          outlier_type='instance',    # use 'feature' or 'instance' level
                          return_feature_score=True,  # scores used to determine outliers
                          return_instance_score=True)
    print(list(od_preds['data'].keys()))
    target = np.zeros(X.shape[0],).astype(int)  # all normal CIFAR10 training instances
    labels = ['normal', 'outlier']
    plot_instance_score(od_preds, target, labels, od.threshold)
    '''

    block7 = '''
    from alibi_detect.utils.saving import save_detector, load_detector
    from os import listdir
    from os.path import isfile, join

    filepath="cifar10outlier"
    save_detector(od, filepath) 
    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    for filename in onlyfiles:
        print(filename)
        print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{OUTLIER_MODEL_PATH}/{filename}", join(filepath, filename)))
    filepath="cifar10outlier/model"
    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    for filename in onlyfiles:
        print(filename)
        print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{OUTLIER_MODEL_PATH}/model/{filename}", join(filepath, filename)))
    '''

    data_saving_block = '''
    # -----------------------DATA SAVING START---------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.save(X_train, "X_train")
    # -----------------------DATA SAVING END-----------------------------------
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block, data_loading_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              block6,
              block7,
              data_saving_block)
    html_artifact = _kale_run_code(blocks)
    with open("/train_outlier_detector.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('train_outlier_detector')

    _kale_mlmd_utils.call("mark_execution_complete")


def deploy_event_display(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    DEPLOY_NAMESPACE = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    event_display=f"""apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: event-display
      namespace: {DEPLOY_NAMESPACE}          
    spec:
      replicas: 1
      selector:
        matchLabels: &labels
          app: event-display
      template:
        metadata:
          labels: *labels
        spec:
          containers:
            - name: helloworld-go
              # Source code: https://github.com/knative/eventing-contrib/tree/master/cmd/event_display
              image: gcr.io/knative-releases/knative.dev/eventing-contrib/cmd/event_display@sha256:f4628e97a836c77ed38bd3b6fd3d0b06de4d5e7db6704772fe674d48b20bd477
    ---
    kind: Service
    apiVersion: v1
    metadata:
      name: event-display
      namespace: {DEPLOY_NAMESPACE}
    spec:
      selector:
        app: event-display
      ports:
        - protocol: TCP
          port: 80
          targetPort: 8080
    ---
    apiVersion: eventing.knative.dev/v1alpha1
    kind: Trigger
    metadata:
      name: cifar10-outlier-display
      namespace: {DEPLOY_NAMESPACE}
    spec:
      broker: default
      filter:
        attributes:
          type: io.seldon.serving.inference.outlier
      subscriber:
        ref:
          apiVersion: v1
          kind: Service
          name: event-display
    ---
    apiVersion: eventing.knative.dev/v1alpha1
    kind: Trigger
    metadata:
      name: cifar10-drift-display
      namespace: {DEPLOY_NAMESPACE}
    spec:
      broker: default
      filter:
        attributes:
          type: io.seldon.serving.inference.drift
      subscriber:
        ref:
          apiVersion: v1
          kind: Service
          name: event-display
    """
    with open("event_display.yaml","w") as f:
        f.write(event_display)
    run("kubectl apply -f event_display.yaml", shell=True)
    '''

    block4 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/event-display -n {DEPLOY_NAMESPACE}", shell=True)
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/deploy_event_display.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('deploy_event_display')

    _kale_mlmd_utils.call("mark_execution_complete")


def deploy_outlier_detector(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str, OUTLIER_MODEL_PATH: str):
    pipeline_parameters_block = '''
    DEPLOY_NAMESPACE = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    OUTLIER_MODEL_PATH = "{}"
    '''.format(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    outlier_yaml=f"""apiVersion: serving.knative.dev/v1
    kind: Service
    metadata:
      name: cifar10-outlier
      namespace: {DEPLOY_NAMESPACE}
    spec:
      template:
        metadata:
          annotations:
            autoscaling.knative.dev/minScale: "1"
        spec:
          containers:
          - image: seldonio/alibi-detect-server:1.2.1
            imagePullPolicy: IfNotPresent
            args:
            - --model_name
            - cifar10od
            - --protocol
            - tensorflow.http
            - --storage_uri
            - s3://{MINIO_MODEL_BUCKET}/{OUTLIER_MODEL_PATH}
            - --reply_url
            - http://default-broker       
            - --event_type
            - io.seldon.serving.inference.outlier
            - --event_source
            - io.seldon.serving.cifar10od
            - OutlierDetector
            envFrom:
            - secretRef:
                name: seldon-init-container-secret
    """
    with open("outlier.yaml","w") as f:
        f.write(outlier_yaml)
    run("kubectl apply -f outlier.yaml", shell=True)
    '''

    block4 = '''
    trigger_outlier_yaml=f"""apiVersion: eventing.knative.dev/v1alpha1
    kind: Trigger
    metadata:
      name: cifar10-outlier-trigger
      namespace: {DEPLOY_NAMESPACE}
    spec:
      filter:
        sourceAndType:
          type: io.seldon.serving.inference.request
      subscriber:
        ref:
          apiVersion: serving.knative.dev/v1
          kind: Service
          name: cifar10-outlier
    """
    with open("outlier_trigger.yaml","w") as f:
        f.write(trigger_outlier_yaml)
    run("kubectl apply -f outlier_trigger.yaml", shell=True)
    '''

    block5 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l serving.knative.dev/service=cifar10-outlier -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/deploy_outlier_detector.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('deploy_outlier_detector')

    _kale_mlmd_utils.call("mark_execution_complete")


def test_oulier_detection(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    DEPLOY_NAMESPACE = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_train = _kale_marshal_utils.load("X_train")
    class_names = _kale_marshal_utils.load("class_names")
    y_train = _kale_marshal_utils.load("y_train")
    # -----------------------DATA LOADING END----------------------------------
    '''

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    idx = 1
    X = X_train[idx:idx+1]
    '''

    block4 = '''
    np.random.seed(0) 
    X_mask, mask = apply_mask(X.reshape(1, 32, 32, 3),
                                      mask_size=(10,10),
                                      n_masks=1,
                                      channels=[0,1,2],
                                      mask_type='normal',
                                      noise_distr=(0,1),
                                      clip_rng=(0,1))
    '''

    block5 = '''
    def predict():
        test_example=X_mask.tolist()
        payload='{"instances":'+f"{test_example}"+' }'
        cmd=f"""curl -d '{payload}' \\
           http://cifar10-classifier-default.{DEPLOY_NAMESPACE}:8000/v1/models/classifier/:predict \\
           -H "Content-Type: application/json"
        """
        ret = Popen(cmd, shell=True,stdout=PIPE)
        raw = ret.stdout.read().decode("utf-8")
        print(raw)
        res=json.loads(raw)
        arr=np.array(res["predictions"])
        plt.imshow(X_mask.reshape(32, 32, 3))
        plt.axis('off')
        plt.show()
        print("class:",class_names[y_train[idx][0]])
        print("prediction:",class_names[arr[0].argmax()])
    '''

    block6 = '''
    def get_outlier_event_display_logs():
        cmd=f"kubectl logs $(kubectl get pod -l app=event-display -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE}) -n {DEPLOY_NAMESPACE}"
        ret = Popen(cmd, shell=True,stdout=PIPE)
        res = ret.stdout.read().decode("utf-8").split("\\n")
        data= []
        for i in range(0,len(res)):
            if res[i] == 'Data,':
                j = json.loads(json.loads(res[i+1]))
                if "is_outlier"in j["data"].keys():
                    data.append(j)
        if len(data) > 0:
            return data[-1]
        else:
            return None
    j = None
    while j is None:
        predict()
        print("Waiting for outlier logs, sleeping")
        time.sleep(2)
        j = get_outlier_event_display_logs()
        
    print(j)
    print("Outlier",j["data"]["is_outlier"]==[1])
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block, data_loading_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              block6,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/test_oulier_detection.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('test_oulier_detection')

    _kale_mlmd_utils.call("mark_execution_complete")


def deploy_drift_detector(DEPLOY_NAMESPACE: str, DRIFT_MODEL_PATH: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    DEPLOY_NAMESPACE = "{}"
    DRIFT_MODEL_PATH = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(DEPLOY_NAMESPACE, DRIFT_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    drift_yaml=f"""apiVersion: serving.knative.dev/v1
    kind: Service
    metadata:
      name: cifar10-drift
      namespace: {DEPLOY_NAMESPACE}
    spec:
      template:
        metadata:
          annotations:
            autoscaling.knative.dev/minScale: "1"
        spec:
          containers:
          - image: seldonio/alibi-detect-server:1.2.2-dev
            imagePullPolicy: IfNotPresent
            args:
            - --model_name
            - cifar10cd
            - --protocol
            - tensorflow.http
            - --storage_uri
            - s3://{MINIO_MODEL_BUCKET}/{DRIFT_MODEL_PATH}
            - --reply_url
            - http://default-broker
            - --event_type
            - io.seldon.serving.inference.drift
            - --event_source
            - io.seldon.serving.cifar10cd
            - DriftDetector
            - --drift_batch_size
            - '500'
            envFrom:
            - secretRef:
                name: seldon-init-container-secret
    """
    with open("drift.yaml","w") as f:
        f.write(drift_yaml)
    run("kubectl apply -f drift.yaml", shell=True)
    '''

    block4 = '''
    trigger_outlier_yaml=f"""apiVersion: eventing.knative.dev/v1alpha1
    kind: Trigger
    metadata:
      name: cifar10-drift-trigger
      namespace: {DEPLOY_NAMESPACE}
    spec:
      filter:
        sourceAndType:
          type: io.seldon.serving.inference.request
      subscriber:
        ref:
          apiVersion: serving.knative.dev/v1
          kind: Service
          name: cifar10-drift
    """
    with open("outlier_trigger.yaml","w") as f:
        f.write(trigger_outlier_yaml)
    run("kubectl apply -f outlier_trigger.yaml", shell=True)
    '''

    block5 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l serving.knative.dev/service=cifar10-drift -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/deploy_drift_detector.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('deploy_drift_detector')

    _kale_mlmd_utils.call("mark_execution_complete")


def test_drift_detector(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    DEPLOY_NAMESPACE = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    block1 = '''
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from alibi.explainers import AnchorImage
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    from alibi_detect.utils.fetching import fetch_tf_model
    import json
    import logging
    import matplotlib.pyplot as plt
    import tensorflow as tf
    tf.keras.backend.clear_session()
    from tensorflow.keras.layers import Conv2D, Conv2DTranspose, Dense, Layer, Reshape, InputLayer
    from tqdm import tqdm

    from alibi_detect.models.losses import elbo
    from alibi_detect.od import OutlierVAE
    from alibi_detect.utils.fetching import fetch_detector
    from alibi_detect.utils.perturbation import apply_mask
    from alibi_detect.utils.saving import save_detector, load_detector
    from alibi_detect.utils.visualize import plot_instance_score, plot_feature_outlier_image
    import time

    logger = tf.get_logger()
    logger.setLevel(logging.ERROR)
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    def show(X):
        plt.imshow(X.reshape(32, 32, 3))
        plt.axis('off')
        plt.show()
    '''

    block4 = '''
    from alibi_detect.datasets import fetch_cifar10c, corruption_types_cifar10c
    corruption = ['motion_blur']
    X_corr, y_corr = fetch_cifar10c(corruption=corruption, severity=5, return_X_y=True)
    X_corr = X_corr.astype('float32') / 255
    '''

    block5 = '''
    show(X_corr[0])
    show(X_corr[1])
    show(X_corr[2])
    '''

    block6 = '''
    def predict(X):
        test_example=X.tolist()
        payload='{"instances":'+f"{test_example}"+' }'
        with open("payload.json","w") as f:
            f.write(payload)
        cmd=f"""curl -d @./payload.json \\
       http://cifar10-classifier-default.{DEPLOY_NAMESPACE}:8000/v1/models/classifier/:predict \\
       -H "Content-Type: application/json"
        """
        run(cmd, shell=True)
    '''

    block7 = '''
    def get_drift_event_display_logs():
        cmd=f"kubectl logs $(kubectl get pod -l app=event-display -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE}) -n {DEPLOY_NAMESPACE}"
        ret = Popen(cmd, shell=True,stdout=PIPE)
        res = ret.stdout.read().decode("utf-8").split("\\n")
        data= []
        for i in range(0,len(res)):
            if res[i] == 'Data,':
                j = json.loads(json.loads(res[i+1]))
                if "is_drift"in j["data"].keys():
                    data.append(j)
        if len(data) > 0:
            return data[-1]
        else:
            return None
    j = None
    for i in range(0,1000,50):
        X = X_corr[i:i+50]
        predict(X)
        print("Waiting for drift logs, sleeping")
        time.sleep(2)
        j = get_drift_event_display_logs()
        if j is not None:
            break
        
    print(j)
    print("Drift",j["data"]["is_drift"]==1)
    '''

    block8 = '''
    
    '''

    # run the code blocks inside a jupyter kernel
    from kale.utils.jupyter_utils import run_code as _kale_run_code
    from kale.utils.kfp_utils import \
        update_uimetadata as _kale_update_uimetadata
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              block5,
              block6,
              block7,
              block8,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/test_drift_detector.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('test_drift_detector')

    _kale_mlmd_utils.call("mark_execution_complete")


setup_op = comp.func_to_container_op(
    setup, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


train_model_and_explainer_op = comp.func_to_container_op(
    train_model_and_explainer, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_model_op = comp.func_to_container_op(
    deploy_model, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


train_drift_detector_op = comp.func_to_container_op(
    train_drift_detector, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


train_outlier_detector_op = comp.func_to_container_op(
    train_outlier_detector, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_event_display_op = comp.func_to_container_op(
    deploy_event_display, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_outlier_detector_op = comp.func_to_container_op(
    deploy_outlier_detector, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


test_oulier_detection_op = comp.func_to_container_op(
    test_oulier_detection, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_drift_detector_op = comp.func_to_container_op(
    deploy_drift_detector, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


test_drift_detector_op = comp.func_to_container_op(
    test_drift_detector, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


@dsl.pipeline(
    name='seldon-e2e-cifar10-glv9p',
    description='Seldon CIFAR10 Example'
)
def auto_generated_pipeline(CIFAR10_MODEL_PATH='tfserving/cifar10/model', DEPLOY_NAMESPACE='admin', DRIFT_MODEL_PATH='tfserving/cifar10/drift', EXPLAINER_MODEL_PATH='tfserving/cifar10/explainer', MINIO_ACCESS_KEY='minio', MINIO_HOST='minio-service.kubeflow:9000', MINIO_MODEL_BUCKET='seldon', MINIO_SECRET_KEY='minio123', OUTLIER_MODEL_PATH='tfserving/cifar10/outlier', TRAIN_DRIFT_DETECTOR='False', TRAIN_OUTLIER_DETECTOR='False'):
    pvolumes_dict = OrderedDict()
    volume_step_names = []
    volume_name_parameters = []

    marshal_vop = dsl.VolumeOp(
        name="kale-marshal-volume",
        resource_name="kale-marshal-pvc",
        modes=dsl.VOLUME_MODE_RWM,
        size="1Gi"
    )
    volume_step_names.append(marshal_vop.name)
    volume_name_parameters.append(marshal_vop.outputs["name"].full_name)
    pvolumes_dict['/marshal'] = marshal_vop.volume

    volume_step_names.sort()
    volume_name_parameters.sort()

    setup_task = setup_op(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after()
    setup_task.container.working_dir = "/home/jovyan"
    setup_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'setup': '/setup.html'})
    setup_task.output_artifact_paths.update(output_artifacts)
    setup_task.add_pod_label("pipelines.kubeflow.org/metadata_written", "true")
    dep_names = setup_task.dependent_names + volume_step_names
    setup_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        setup_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    train_model_and_explainer_task = train_model_and_explainer_op(CIFAR10_MODEL_PATH, EXPLAINER_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(setup_task)
    train_model_and_explainer_task.container.working_dir = "/home/jovyan"
    train_model_and_explainer_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'train_model_and_explainer': '/train_model_and_explainer.html'})
    train_model_and_explainer_task.output_artifact_paths.update(
        output_artifacts)
    train_model_and_explainer_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = train_model_and_explainer_task.dependent_names + volume_step_names
    train_model_and_explainer_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        train_model_and_explainer_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_model_task = deploy_model_op(CIFAR10_MODEL_PATH, DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(train_model_and_explainer_task)
    deploy_model_task.container.working_dir = "/home/jovyan"
    deploy_model_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'deploy_model': '/deploy_model.html'})
    deploy_model_task.output_artifact_paths.update(output_artifacts)
    deploy_model_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = deploy_model_task.dependent_names + volume_step_names
    deploy_model_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        deploy_model_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    train_drift_detector_task = train_drift_detector_op(DRIFT_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(train_model_and_explainer_task)
    train_drift_detector_task.container.working_dir = "/home/jovyan"
    train_drift_detector_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'train_drift_detector': '/train_drift_detector.html'})
    train_drift_detector_task.output_artifact_paths.update(output_artifacts)
    train_drift_detector_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = train_drift_detector_task.dependent_names + volume_step_names
    train_drift_detector_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        train_drift_detector_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    train_outlier_detector_task = train_outlier_detector_op(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH, TRAIN_OUTLIER_DETECTOR)\
        .add_pvolumes(pvolumes_dict)\
        .after(train_model_and_explainer_task)
    train_outlier_detector_task.container.working_dir = "/home/jovyan"
    train_outlier_detector_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'train_outlier_detector': '/train_outlier_detector.html'})
    train_outlier_detector_task.output_artifact_paths.update(output_artifacts)
    train_outlier_detector_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = train_outlier_detector_task.dependent_names + volume_step_names
    train_outlier_detector_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        train_outlier_detector_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_event_display_task = deploy_event_display_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(train_drift_detector_task, train_outlier_detector_task, deploy_model_task)
    deploy_event_display_task.container.working_dir = "/home/jovyan"
    deploy_event_display_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'deploy_event_display': '/deploy_event_display.html'})
    deploy_event_display_task.output_artifact_paths.update(output_artifacts)
    deploy_event_display_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = deploy_event_display_task.dependent_names + volume_step_names
    deploy_event_display_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        deploy_event_display_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_outlier_detector_task = deploy_outlier_detector_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH)\
        .add_pvolumes(pvolumes_dict)\
        .after(deploy_event_display_task)
    deploy_outlier_detector_task.container.working_dir = "/home/jovyan"
    deploy_outlier_detector_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'deploy_outlier_detector': '/deploy_outlier_detector.html'})
    deploy_outlier_detector_task.output_artifact_paths.update(output_artifacts)
    deploy_outlier_detector_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = deploy_outlier_detector_task.dependent_names + volume_step_names
    deploy_outlier_detector_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        deploy_outlier_detector_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    test_oulier_detection_task = test_oulier_detection_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(deploy_outlier_detector_task)
    test_oulier_detection_task.container.working_dir = "/home/jovyan"
    test_oulier_detection_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'test_oulier_detection': '/test_oulier_detection.html'})
    test_oulier_detection_task.output_artifact_paths.update(output_artifacts)
    test_oulier_detection_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = test_oulier_detection_task.dependent_names + volume_step_names
    test_oulier_detection_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        test_oulier_detection_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_drift_detector_task = deploy_drift_detector_op(DEPLOY_NAMESPACE, DRIFT_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(test_oulier_detection_task)
    deploy_drift_detector_task.container.working_dir = "/home/jovyan"
    deploy_drift_detector_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'deploy_drift_detector': '/deploy_drift_detector.html'})
    deploy_drift_detector_task.output_artifact_paths.update(output_artifacts)
    deploy_drift_detector_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = deploy_drift_detector_task.dependent_names + volume_step_names
    deploy_drift_detector_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        deploy_drift_detector_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    test_drift_detector_task = test_drift_detector_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(deploy_drift_detector_task)
    test_drift_detector_task.container.working_dir = "/home/jovyan"
    test_drift_detector_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update(
        {'test_drift_detector': '/test_drift_detector.html'})
    test_drift_detector_task.output_artifact_paths.update(output_artifacts)
    test_drift_detector_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = test_drift_detector_task.dependent_names + volume_step_names
    test_drift_detector_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        test_drift_detector_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))


if __name__ == "__main__":
    pipeline_func = auto_generated_pipeline
    pipeline_filename = pipeline_func.__name__ + '.pipeline.tar.gz'
    import kfp.compiler as compiler
    compiler.Compiler().compile(pipeline_func, pipeline_filename)

    # Get or create an experiment and submit a pipeline run
    import kfp
    client = kfp.Client()
    experiment = client.create_experiment('seldon-e2e-cifar10')

    # Submit a pipeline run
    from kale.utils.kfp_utils import generate_run_name
    run_name = generate_run_name('seldon-e2e-cifar10-glv9p')
    run_result = client.run_pipeline(
        experiment.id, run_name, pipeline_filename, {})
