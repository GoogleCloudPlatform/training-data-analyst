
ISTIO_VERSION="${ISTIO_VERSION:-1.7.3}"
curl -L https://git.io/getLatestIstio | ISTIO_VERSION=$ISTIO_VERSION sh -

kubectl create namespace istio-system
kubectl create secret generic cacerts -n istio-system \
--from-file=istio-$ISTIO_VERSION/samples/certs/ca-cert.pem \
--from-file=istio-$ISTIO_VERSION/samples/certs/ca-key.pem \
--from-file=istio-$ISTIO_VERSION/samples/certs/root-cert.pem \
--from-file=istio-$ISTIO_VERSION/samples/certs/cert-chain.pem

./istio-$ISTIO_VERSION/bin/istioctl manifest apply \
--set profile=demo

kubectl create namespace prod
kubectl label namespace prod istio-injection=enabled --overwrite
kubectl apply -n prod -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/kubernetes-manifests.yaml
kubectl apply -n prod-f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/master/release/istio-manifests.yaml
kubectl patch -n prod deployments/productcatalogservice -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1"}}}}}'
