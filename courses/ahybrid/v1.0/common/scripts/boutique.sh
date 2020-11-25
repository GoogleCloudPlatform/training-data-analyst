echo $ENV
echo ${ENV}

kubectl create namespace ${ENV}

if [ "$(CTYPE)" != 'REMOTE' ]; then
  kubectl label namespace ${ENV} \
    istio.io/rev=$(kubectl -n istio-system get pods -l app=istiod -o json | jq -r '.items[0].metadata.labels["istio.io/rev"]') \
    --overwrite
else
  kubectl label namespace ${ENV} istio-injection=enabled
fi

kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/kubernetes-manifests.yaml
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/istio-manifests.yaml
kubectl patch -n prod deployments/productcatalogservice -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1"}}}}}'