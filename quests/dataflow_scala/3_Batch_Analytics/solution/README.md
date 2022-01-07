# batch

## Raison d'être

TODO: your project description

## Features

This project comes with number of preconfigured features, including:

### Running

* `sbt stage`
* `target/universal/stage/bin/word-count --output=wc`

### Packaging

This template comes with [sbt-native-packager](https://sbt-native-packager.readthedocs.io) and it allows you to build **zips**, **docker** images, etc. Have a look at the documentation for more details.

```bash
sbt
# create a zip file
> universal:packageBin
# publish a docker image to your local registry
> docker:publishLocal
```

### Testing

This template comes with an example of a test, to run tests:

```bash
sbt test
```

### REPL

To experiment with current codebase in [Scio REPL](https://github.com/spotify/scio/wiki/Scio-REPL)
simply:

```bash
sbt repl/run
```

---

This project is based on the [scio.g8](https://github.com/spotify/scio.g8).
