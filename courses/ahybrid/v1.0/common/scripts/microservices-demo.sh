kubectl create namespace prod

if [[ $MESH = "ASM" ]]
then
  kubectl label namespace prod \
    istio.io/rev=$(kubectl -n istio-system get pods -l app=istiod -o json | jq -r '.items[0].metadata.labels["istio.io/rev"]') \
    --overwrite
else
  kubectl label namespace prod istio-injection=enabled --overwrite
fi

# Install the App
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/kubernetes-manifests.yaml
kubectl patch -n prod deployments/productcatalogservice -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1"}}}}}'

# Install the ingress Gateway:
git clone https://github.com/GoogleCloudPlatform/anthos-service-mesh-packages
kubectl apply -n prod -f anthos-service-mesh-packages/samples/gateways/istio-ingressgateway

# Configure the Gateway:
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/istio-manifests.yaml
