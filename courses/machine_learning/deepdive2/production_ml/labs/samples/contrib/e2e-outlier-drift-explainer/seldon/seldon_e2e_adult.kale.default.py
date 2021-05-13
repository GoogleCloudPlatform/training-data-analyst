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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
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


def build_model(INCOME_MODEL_PATH: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    INCOME_MODEL_PATH = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(INCOME_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    adult = fetch_adult()
    adult.keys()
    '''

    block4 = '''
    data = adult.data
    target = adult.target
    feature_names = adult.feature_names
    category_map = adult.category_map
    '''

    block5 = '''
    from alibi.utils.data import gen_category_map
    '''

    block6 = '''
    np.random.seed(0)
    data_perm = np.random.permutation(np.c_[data, target])
    data = data_perm[:,:-1]
    target = data_perm[:,-1]
    '''

    block7 = '''
    idx = 30000
    X_train,Y_train = data[:idx,:], target[:idx]
    X_test, Y_test = data[idx+1:,:], target[idx+1:]
    '''

    block8 = '''
    ordinal_features = [x for x in range(len(feature_names)) if x not in list(category_map.keys())]
    ordinal_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')),
                                          ('scaler', StandardScaler())])
    '''

    block9 = '''
    categorical_features = list(category_map.keys())
    categorical_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')),
                                              ('onehot', OneHotEncoder(handle_unknown='ignore'))])
    '''

    block10 = '''
    preprocessor = ColumnTransformer(transformers=[('num', ordinal_transformer, ordinal_features),
                                                   ('cat', categorical_transformer, categorical_features)])
    '''

    block11 = '''
    np.random.seed(0)
    clf = RandomForestClassifier(n_estimators=50)
    '''

    block12 = '''
    model=Pipeline(steps=[("preprocess",preprocessor),("model",clf)])
    model.fit(X_train,Y_train)
    '''

    block13 = '''
    def predict_fn(x):
        return model.predict(x)
    '''

    block14 = '''
    #predict_fn = lambda x: clf.predict(preprocessor.transform(x))
    print('Train accuracy: ', accuracy_score(Y_train, predict_fn(X_train)))
    print('Test accuracy: ', accuracy_score(Y_test, predict_fn(X_test)))
    '''

    block15 = '''
    dump(model, 'model.joblib') 
    '''

    block16 = '''
    print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{INCOME_MODEL_PATH}/model.joblib", 'model.joblib'))
    '''

    data_saving_block = '''
    # -----------------------DATA SAVING START---------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.save(X_test, "X_test")
    _kale_marshal_utils.save(X_train, "X_train")
    _kale_marshal_utils.save(Y_train, "Y_train")
    _kale_marshal_utils.save(adult, "adult")
    _kale_marshal_utils.save(category_map, "category_map")
    _kale_marshal_utils.save(feature_names, "feature_names")
    _kale_marshal_utils.save(model, "model")
    _kale_marshal_utils.save(predict_fn, "predict_fn")
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
              block15,
              block16,
              data_saving_block)
    html_artifact = _kale_run_code(blocks)
    with open("/build_model.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('build_model')

    _kale_mlmd_utils.call("mark_execution_complete")


def build_outlier(MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str, OUTLIER_MODEL_PATH: str):
    pipeline_parameters_block = '''
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    OUTLIER_MODEL_PATH = "{}"
    '''.format(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_train = _kale_marshal_utils.load("X_train")
    Y_train = _kale_marshal_utils.load("Y_train")
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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    from alibi_detect.od import IForest

    od = IForest(
        threshold=0.,
        n_estimators=200,
    )
    '''

    block4 = '''
    od.fit(X_train)
    '''

    block5 = '''
    np.random.seed(0)
    perc_outlier = 5
    threshold_batch = create_outlier_batch(X_train, Y_train, n_samples=1000, perc_outlier=perc_outlier)
    X_threshold, y_threshold = threshold_batch.data.astype('float'), threshold_batch.target
    #X_threshold = (X_threshold - mean) / stdev
    print('{}% outliers'.format(100 * y_threshold.mean()))
    '''

    block6 = '''
    od.infer_threshold(X_threshold, threshold_perc=100-perc_outlier)
    print('New threshold: {}'.format(od.threshold))
    threshold = od.threshold
    '''

    block7 = '''
    X_outlier = [[300,  4,  4,  2,  1,  4,  4,  0,  0,  0, 600,  9]]
    '''

    block8 = '''
    od.predict(
        X_outlier
    )
    '''

    block9 = '''
    from alibi_detect.utils.saving import save_detector, load_detector
    from os import listdir
    from os.path import isfile, join

    filepath="ifoutlier"
    save_detector(od, filepath) 
    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    for filename in onlyfiles:
        print(filename)
        print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{OUTLIER_MODEL_PATH}/{filename}", join(filepath, filename)))
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
    with open("/build_outlier.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('build_outlier')

    _kale_mlmd_utils.call("mark_execution_complete")


def train_explainer(EXPLAINER_MODEL_PATH: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    EXPLAINER_MODEL_PATH = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(EXPLAINER_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_train = _kale_marshal_utils.load("X_train")
    category_map = _kale_marshal_utils.load("category_map")
    feature_names = _kale_marshal_utils.load("feature_names")
    model = _kale_marshal_utils.load("model")
    predict_fn = _kale_marshal_utils.load("predict_fn")
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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    model.predict(X_train)
    explainer = AnchorTabular(predict_fn, feature_names, categorical_names=category_map)
    '''

    block4 = '''
    explainer.fit(X_train, disc_perc=[25, 50, 75])
    '''

    block5 = '''
    with open("explainer.dill", "wb") as dill_file:
        dill.dump(explainer, dill_file)    
        dill_file.close()
    print(get_minio().fput_object(MINIO_MODEL_BUCKET, f"{EXPLAINER_MODEL_PATH}/explainer.dill", 'explainer.dill'))
    '''

    data_saving_block = '''
    # -----------------------DATA SAVING START---------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.save(X_train, "X_train")
    _kale_marshal_utils.save(explainer, "explainer")
    _kale_marshal_utils.save(model, "model")
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
              data_saving_block)
    html_artifact = _kale_run_code(blocks)
    with open("/train_explainer.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('train_explainer')

    _kale_mlmd_utils.call("mark_execution_complete")


def deploy_seldon(DEPLOY_NAMESPACE: str, EXPLAINER_MODEL_PATH: str, INCOME_MODEL_PATH: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    DEPLOY_NAMESPACE = "{}"
    EXPLAINER_MODEL_PATH = "{}"
    INCOME_MODEL_PATH = "{}"
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_MODEL_BUCKET = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(DEPLOY_NAMESPACE, EXPLAINER_MODEL_PATH, INCOME_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)

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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
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
      name: income-classifier
      namespace: {DEPLOY_NAMESPACE}
    spec:
      predictors:
      - componentSpecs:
        graph:
          implementation: SKLEARN_SERVER
          modelUri: s3://{MINIO_MODEL_BUCKET}/{INCOME_MODEL_PATH}
          envSecretRefName: seldon-init-container-secret
          name: classifier
          logger:
             mode: all
        explainer:
          type: AnchorTabular
          modelUri: s3://{MINIO_MODEL_BUCKET}/{EXPLAINER_MODEL_PATH}
          envSecretRefName: seldon-init-container-secret
        name: default
        replicas: 1
    """
    with open("model.yaml","w") as f:
        f.write(model_yaml)
    run("kubectl apply -f model.yaml", shell=True)
    '''

    block6 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l seldon-deployment-id=income-classifier -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
    '''

    block7 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l seldon-deployment-id=income-classifier -o jsonpath='{{.items[1].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
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
              )
    html_artifact = _kale_run_code(blocks)
    with open("/deploy_seldon.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('deploy_seldon')

    _kale_mlmd_utils.call("mark_execution_complete")


def test_model(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_SECRET_KEY: str):
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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    payload='{"data": {"ndarray": [[53,4,0,2,8,4,4,0,0,0,60,9]]}}'
    cmd=f"""curl -d '{payload}' \\
       http://income-classifier-default.{DEPLOY_NAMESPACE}:8000/api/v1.0/predictions \\
       -H "Content-Type: application/json"
    """
    ret = Popen(cmd, shell=True,stdout=PIPE)
    raw = ret.stdout.read().decode("utf-8")
    print(raw)
    '''

    block4 = '''
    payload='{"data": {"ndarray": [[53,4,0,2,8,4,4,0,0,0,60,9]]}}'
    cmd=f"""curl -d '{payload}' \\
       http://income-classifier-default-explainer.{DEPLOY_NAMESPACE}:9000/api/v1.0/explain \\
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
    blocks = (pipeline_parameters_block,
              block1,
              block2,
              block3,
              block4,
              )
    html_artifact = _kale_run_code(blocks)
    with open("/test_model.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('test_model')

    _kale_mlmd_utils.call("mark_execution_complete")


def deploy_outlier(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_MODEL_BUCKET: str, MINIO_SECRET_KEY: str, OUTLIER_MODEL_PATH: str):
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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
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
      name: income-outlier
      namespace: {DEPLOY_NAMESPACE}
    spec:
      template:
        metadata:
          annotations:
            autoscaling.knative.dev/minScale: "1"
        spec:
          containers:
          - image: seldonio/alibi-detect-server:1.2.2-dev_alibidetect
            imagePullPolicy: IfNotPresent
            args:
            - --model_name
            - adultod
            - --http_port
            - '8080'
            - --protocol
            - seldon.http
            - --storage_uri
            - s3://{MINIO_MODEL_BUCKET}/{OUTLIER_MODEL_PATH}
            - --reply_url
            - http://default-broker       
            - --event_type
            - io.seldon.serving.inference.outlier
            - --event_source
            - io.seldon.serving.incomeod
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
      name: income-outlier-trigger
      namespace: {DEPLOY_NAMESPACE}
    spec:
      filter:
        sourceAndType:
          type: io.seldon.serving.inference.request
      subscriber:
        ref:
          apiVersion: serving.knative.dev/v1alpha1
          kind: Service
          name: income-outlier
    """
    with open("outlier_trigger.yaml","w") as f:
        f.write(trigger_outlier_yaml)
    run("kubectl apply -f outlier_trigger.yaml", shell=True)
    '''

    block5 = '''
    run(f"kubectl rollout status -n {DEPLOY_NAMESPACE} deploy/$(kubectl get deploy -l serving.knative.dev/service=income-outlier -o jsonpath='{{.items[0].metadata.name}}' -n {DEPLOY_NAMESPACE})", shell=True)
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
    with open("/deploy_outlier.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('deploy_outlier')

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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
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
      name: income-outlier-display
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


def test_outliers(DEPLOY_NAMESPACE: str, MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_SECRET_KEY: str):
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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    def predict():
        payload='{"data": {"ndarray": [[300,  4,  4,  2,  1,  4,  4,  0,  0,  0, 600,  9]]}}'
        cmd=f"""curl -d '{payload}' \\
           http://income-classifier-default.{DEPLOY_NAMESPACE}:8000/api/v1.0/predictions \\
           -H "Content-Type: application/json"
        """
        ret = Popen(cmd, shell=True,stdout=PIPE)
        raw = ret.stdout.read().decode("utf-8")
        print(raw)
    '''

    block4 = '''
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

    block5 = '''
    
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
    with open("/test_outliers.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('test_outliers')

    _kale_mlmd_utils.call("mark_execution_complete")


def explain(MINIO_ACCESS_KEY: str, MINIO_HOST: str, MINIO_SECRET_KEY: str):
    pipeline_parameters_block = '''
    MINIO_ACCESS_KEY = "{}"
    MINIO_HOST = "{}"
    MINIO_SECRET_KEY = "{}"
    '''.format(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)

    from kale.utils import mlmd_utils as _kale_mlmd_utils
    _kale_mlmd_utils.init_metadata()

    data_loading_block = '''
    # -----------------------DATA LOADING START--------------------------------
    from kale.marshal import utils as _kale_marshal_utils
    _kale_marshal_utils.set_kale_data_directory("/marshal")
    _kale_marshal_utils.set_kale_directory_file_names()
    X_test = _kale_marshal_utils.load("X_test")
    X_train = _kale_marshal_utils.load("X_train")
    adult = _kale_marshal_utils.load("adult")
    explainer = _kale_marshal_utils.load("explainer")
    model = _kale_marshal_utils.load("model")
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
    from alibi.explainers import AnchorTabular
    from alibi.datasets import fetch_adult
    from minio import Minio
    from minio.error import ResponseError
    from joblib import dump, load
    import dill
    import time
    import json
    from subprocess import run, Popen, PIPE
    from alibi_detect.utils.data import create_outlier_batch
    '''

    block2 = '''
    def get_minio():
        return Minio(MINIO_HOST,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)
    '''

    block3 = '''
    model.predict(X_train)
    idx = 0
    class_names = adult.target_names
    print('Prediction: ', class_names[explainer.predict_fn(X_test[idx].reshape(1, -1))[0]])
    '''

    block4 = '''
    explanation = explainer.explain(X_test[idx], threshold=0.95)
    print('Anchor: %s' % (' AND '.join(explanation['names'])))
    print('Precision: %.2f' % explanation['precision'])
    print('Coverage: %.2f' % explanation['coverage'])
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
              )
    html_artifact = _kale_run_code(blocks)
    with open("/explain.html", "w") as f:
        f.write(html_artifact)
    _kale_update_uimetadata('explain')

    _kale_mlmd_utils.call("mark_execution_complete")


setup_op = comp.func_to_container_op(
    setup, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


build_model_op = comp.func_to_container_op(
    build_model, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


build_outlier_op = comp.func_to_container_op(
    build_outlier, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


train_explainer_op = comp.func_to_container_op(
    train_explainer, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_seldon_op = comp.func_to_container_op(
    deploy_seldon, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


test_model_op = comp.func_to_container_op(
    test_model, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_outlier_op = comp.func_to_container_op(
    deploy_outlier, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


deploy_event_display_op = comp.func_to_container_op(
    deploy_event_display, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


test_outliers_op = comp.func_to_container_op(
    test_outliers, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


explain_op = comp.func_to_container_op(
    explain, base_image='seldonio/jupyter-lab-alibi-kale:0.11')


@dsl.pipeline(
    name='seldon-e2e-adult-ttonn',
    description='Seldon e2e adult'
)
def auto_generated_pipeline(DEPLOY_NAMESPACE='admin', EXPLAINER_MODEL_PATH='sklearn/income/explainer', INCOME_MODEL_PATH='sklearn/income/model', MINIO_ACCESS_KEY='minio', MINIO_HOST='minio-service.kubeflow:9000', MINIO_MODEL_BUCKET='seldon', MINIO_SECRET_KEY='minio123', OUTLIER_MODEL_PATH='sklearn/income/outlier'):
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

    build_model_task = build_model_op(INCOME_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(setup_task)
    build_model_task.container.working_dir = "/home/jovyan"
    build_model_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'build_model': '/build_model.html'})
    build_model_task.output_artifact_paths.update(output_artifacts)
    build_model_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = build_model_task.dependent_names + volume_step_names
    build_model_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        build_model_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    build_outlier_task = build_outlier_op(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH)\
        .add_pvolumes(pvolumes_dict)\
        .after(build_model_task)
    build_outlier_task.container.working_dir = "/home/jovyan"
    build_outlier_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'build_outlier': '/build_outlier.html'})
    build_outlier_task.output_artifact_paths.update(output_artifacts)
    build_outlier_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = build_outlier_task.dependent_names + volume_step_names
    build_outlier_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        build_outlier_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    train_explainer_task = train_explainer_op(EXPLAINER_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(build_model_task)
    train_explainer_task.container.working_dir = "/home/jovyan"
    train_explainer_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'train_explainer': '/train_explainer.html'})
    train_explainer_task.output_artifact_paths.update(output_artifacts)
    train_explainer_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = train_explainer_task.dependent_names + volume_step_names
    train_explainer_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        train_explainer_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_seldon_task = deploy_seldon_op(DEPLOY_NAMESPACE, EXPLAINER_MODEL_PATH, INCOME_MODEL_PATH, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(train_explainer_task)
    deploy_seldon_task.container.working_dir = "/home/jovyan"
    deploy_seldon_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'deploy_seldon': '/deploy_seldon.html'})
    deploy_seldon_task.output_artifact_paths.update(output_artifacts)
    deploy_seldon_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = deploy_seldon_task.dependent_names + volume_step_names
    deploy_seldon_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        deploy_seldon_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    test_model_task = test_model_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(deploy_seldon_task)
    test_model_task.container.working_dir = "/home/jovyan"
    test_model_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'test_model': '/test_model.html'})
    test_model_task.output_artifact_paths.update(output_artifacts)
    test_model_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = test_model_task.dependent_names + volume_step_names
    test_model_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        test_model_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_outlier_task = deploy_outlier_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_MODEL_BUCKET, MINIO_SECRET_KEY, OUTLIER_MODEL_PATH)\
        .add_pvolumes(pvolumes_dict)\
        .after(build_outlier_task, test_model_task)
    deploy_outlier_task.container.working_dir = "/home/jovyan"
    deploy_outlier_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'deploy_outlier': '/deploy_outlier.html'})
    deploy_outlier_task.output_artifact_paths.update(output_artifacts)
    deploy_outlier_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = deploy_outlier_task.dependent_names + volume_step_names
    deploy_outlier_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        deploy_outlier_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    deploy_event_display_task = deploy_event_display_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(deploy_outlier_task)
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

    test_outliers_task = test_outliers_op(DEPLOY_NAMESPACE, MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(deploy_event_display_task)
    test_outliers_task.container.working_dir = "/home/jovyan"
    test_outliers_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'test_outliers': '/test_outliers.html'})
    test_outliers_task.output_artifact_paths.update(output_artifacts)
    test_outliers_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = test_outliers_task.dependent_names + volume_step_names
    test_outliers_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        test_outliers_task.add_pod_annotation(
            "kubeflow-kale.org/volume-name-parameters",
            json.dumps(volume_name_parameters))

    explain_task = explain_op(MINIO_ACCESS_KEY, MINIO_HOST, MINIO_SECRET_KEY)\
        .add_pvolumes(pvolumes_dict)\
        .after(train_explainer_task)
    explain_task.container.working_dir = "/home/jovyan"
    explain_task.container.set_security_context(
        k8s_client.V1SecurityContext(run_as_user=0))
    output_artifacts = {}
    output_artifacts.update(
        {'mlpipeline-ui-metadata': '/mlpipeline-ui-metadata.json'})
    output_artifacts.update({'explain': '/explain.html'})
    explain_task.output_artifact_paths.update(output_artifacts)
    explain_task.add_pod_label(
        "pipelines.kubeflow.org/metadata_written", "true")
    dep_names = explain_task.dependent_names + volume_step_names
    explain_task.add_pod_annotation(
        "kubeflow-kale.org/dependent-templates", json.dumps(dep_names))
    if volume_name_parameters:
        explain_task.add_pod_annotation(
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
    experiment = client.create_experiment('seldon-e2e-adult')

    # Submit a pipeline run
    from kale.utils.kfp_utils import generate_run_name
    run_name = generate_run_name('seldon-e2e-adult-ttonn')
    run_result = client.run_pipeline(
        experiment.id, run_name, pipeline_filename, {})
