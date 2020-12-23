ISTIO_VERSION="${ISTIO_VERSION:-1.8.1}"
curl -L https://git.io/getLatestIstio | ISTIO_VERSION=$ISTIO_VERSION sh -

kubectl create namespace istio-system
./istio-$ISTIO_VERSION/bin/istioctl install --set profile=demo -y