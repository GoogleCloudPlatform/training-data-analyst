# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

TRTIS_NAME=trtis
WEBAPP_NAME=webapp
PIPELINE_NAME=resnet-cifar10-pipeline
KF_NAMESPACE=kubeflow

kubectl delete service/$TRTIS_NAME -n $KF_NAMESPACE
kubectl delete deployment.apps/$TRTIS_NAME -n $KF_NAMESPACE

for service in $( kubectl get svc -n $KF_NAMESPACE | grep $WEBAPP_NAME | cut -d' ' -f1 ); do
    kubectl delete -n $KF_NAMESPACE service/$service
done

for deployment in $( kubectl get deployment -n $KF_NAMESPACE | grep $WEBAPP_NAME | cut -d' ' -f1 ); do
    kubectl delete -n $KF_NAMESPACE deployment.apps/$deployment
done

for pod in $(kubectl get pod -n kubeflow | grep $PIPELINE_NAME | cut -d' ' -f1); do 
    kubectl delete -n $KF_NAMESPACE pod/$pod
done
