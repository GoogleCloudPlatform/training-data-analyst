kubectl delete pods healthy-monolith monolith secure-monolith
kubectl delete services monolith auth frontend hello
kubectl delete deployments auth frontend hello hello-canary hello-green
kubectl delete secrets tls-certs
kubectl delete configmaps nginx-frontend-conf nginx-proxy-conf
