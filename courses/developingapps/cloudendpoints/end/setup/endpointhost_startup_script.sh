# Installs nodejs, downloads source from git, installs ESP, runs app
curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
sudo apt-get install -y nodejs

export CLOUD_ENDPOINTS_REPO="google-cloud-endpoints-jessie"
echo "deb http://packages.cloud.google.com/apt $CLOUD_ENDPOINTS_REPO main" | sudo tee /etc/apt/sources.list.d/google-cloud-endpoints.list
curl --silent https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
sudo apt-get install endpoints-runtime

echo PORT=80 >> /etc/default/nginx
sudo service nginx restart
