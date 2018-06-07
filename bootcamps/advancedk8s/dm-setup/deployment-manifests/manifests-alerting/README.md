In order for the alerting component to work, a Kubernetes secret called "slack-hook-url" needs to be created. The content of the secret needs to be the Slack Hook API url.

For more information see

1. https://kubernetes.io/docs/user-guide/secrets/
2. https://api.slack.com/incoming-webhooks