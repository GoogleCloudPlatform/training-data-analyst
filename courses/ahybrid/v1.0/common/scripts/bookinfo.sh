kubectl label namespace default istio-injection=enabled --overwrite

# Deploy BookInfo application
kubectl apply -f \
./istio-1.6.8-asm.9/samples/bookinfo/platform/kube/bookinfo.yaml

# Sleep while Bookinfo pods initialize
sleep 30s

# Expose Bookinfo external gateway/IP
kubectl apply -f \
.istio-1.6.8-asm.9/samples/bookinfo/networking/bookinfo-gateway.yaml