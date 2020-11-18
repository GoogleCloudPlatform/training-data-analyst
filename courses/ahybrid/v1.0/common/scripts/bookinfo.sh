kubectl label namespace default istio-injection=enabled --overwrite

# Deploy BookInfo application
kubectl apply -f ../samples/bookinfo/platform/kube/bookinfo.yaml

# Sleep while Bookinfo pods initialize
sleep 30s

# Expose Bookinfo external gateway/IP
kubectl apply -f ../samples/bookinfo/networking/bookinfo-gateway.yaml