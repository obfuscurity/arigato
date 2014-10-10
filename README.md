# Libratomize

Libratomize is a Python script for performing a one-time migration of your Graphite metrics to the [Librato](https://metrics.librato.com/) monitoring service. It's assumed that you've already transitioned your live metrics feed over to Librato. This utility is only for backfilling the historical data.

Rather than attempting to coerce the raw Whisper archives to match Librato's [resolution levels](http://support.metrics.librato.com/knowledgebase/articles/66838-understanding-metrics-roll-ups-retention-and-grap), Libratomize performs logical queries against the Graphite API, using `summarize()` to roll the results up into compatible resolutions for each interval.

## Usage

### Environment Variables

The following variables are used to authenticate with the Librato API and are *mandatory*. See [this article](http://support.metrics.librato.com/knowledgebase/articles/22317-librato-api-tokens-and-token-roles) which explains how to create your own Librato API token.

* `LIBRATO_USER` - Your account email associated with the token.
* `LIBRATO_TOKEN` - Your *Record Only* API token.

### Command-Line Arguments

The following arguments are available.

* `-n, --node` - Zero-indexed node from the Graphite metric string to use as the Librato [source](http://support.metrics.librato.com/knowledgebase/articles/47904-what-is-a-source). The default value is `1`.
* `-p, --prefix` - A string prefix for the Librato metric. All whitespace and leading/trailing dots are removed from the string before prefixing to the original metric string. Delimiters found within the prefix are preserved (e.g. `foo.bar`) but multiples (e.g. `foo..bar`) will be normalized to a single dot. There is no default prefix.
* `-u, --url` - The Graphite server URL to query. Uses `http://127.0.0.1` by default.

### Examples

#### Using Carbonate locally

The `carbon-list` utility provided by the [Carbonate](https://github.com/jssjr/carbonate) project is ideal for listing metrics on the Graphite server itself. The results can then by piped into Libratomize.

```
$ export PYTHONPATH=$PYTHONPATH:/opt/graphite/lib
$ export LIBRATO_USER=abc
$ export LIBRATO_TOKEN=123

$ carbon-list | grep '^collectd' | \
  python libratomize/script.py -p migrated

Processing collectd.graphite-0-1.load.load.shortterm:
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
...
```

#### Curl a Remote Graphite

This method is slightly more convenient if you don't have local access to your Graphite server **or** you can't install Carbonate **or** you want to iterate through a cluster Graphite servers. It does require a bit more effort to prep the output before passing it onto Libratomize, however.

```
$ export PYTHONPATH=$PYTHONPATH:/opt/graphite/lib
$ export LIBRATO_USER=abc
$ export LIBRATO_TOKEN=123

$ curl -s http://graphite/metrics/index.json | python -m json.tool | \
  grep '"' | sed 's/ //g' | sed 's/"//g' | sed 's/,//g' | grep '^collectd' | \
  python libratomize/script.py -p migrated

Processing collectd.graphite-0-1.load.load.shortterm:
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
...
```

### License

Libratomize is distributed under the MIT license.
