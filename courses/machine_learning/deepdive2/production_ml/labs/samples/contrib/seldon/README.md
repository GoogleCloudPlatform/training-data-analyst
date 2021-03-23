# Seldon Samples

[Seldon](https://github.com/SeldonIO/seldon-core) is a model serving solution that supports multiple deployment strategies and provides out of the box [observability](https://docs.seldon.io/projects/seldon-core/en/latest/analytics/analytics.html). These examples are an overview of how seldon can be used with pipelines:

- iris_storagebucket.py is the simplest case and best place to start. It shows how seldon can [serve a packaged model from a storage bucket URI](https://docs.seldon.io/projects/seldon-core/en/latest/servers/overview.html).
- mabdeploy_seldon.py shows how components can be assembled into [inference graphs](https://docs.seldon.io/projects/seldon-core/en/latest/analytics/routers.html) such as [multi-armed bandits](https://docs.seldon.io/projects/seldon-core/en/latest/examples/helm_examples.html#Serve-Multi-Armed-Bandit).
- mnist_tf.py shows how seldon can be used with [custom-built serving images](https://docs.seldon.io/projects/seldon-core/en/latest/workflow/README.html) where a model is baked into the docker image.
- mnist_tf_volume.py shows a model being stored in a volume and served using a serving image.

See the seldon docs for other uses such as [autoscaling](https://docs.seldon.io/projects/seldon-core/en/latest/examples/autoscaling_example.html), [canaries](https://docs.seldon.io/projects/seldon-core/en/latest/examples/istio_canary.html) and [tracing](https://docs.seldon.io/projects/seldon-core/en/latest/examples/tmpl_model_tracing.html)