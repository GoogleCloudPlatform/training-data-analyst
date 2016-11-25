gcloud app deploy --stop-previous-version
gcloud app deploy cron.yaml

echo
echo "Note: you have to go to IAM section of console.cloud.google.com and add your email address as an admin.  Otherwise, you will not be able to try out the app, since it is restricted to admin roles only."
