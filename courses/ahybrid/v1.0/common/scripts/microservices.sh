ISTIO_VERSION=$(kubectl -n istio-system get pods -l app=istiod -o json | jq -r '.items[0].metadata.labels["istio.io/rev"]')
kubectl create namespace prod

if [ "$ISTIO_VERSION" == "default" ]; then
    kubectl label namespace prod istio-injection=enabled --overwrite
else
    kubectl label namespace prod istio.io/rev=$ISTIO_VERSION --overwrite
fi

kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/kubernetes-manifests.yaml
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/istio-manifests.yaml
kubectl patch -n prod deployments/productcatalogservice -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1"}}}}}'