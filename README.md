# Arigato

```
Domo arigato, Mr. Librato
```

Arigato is a Python script for performing a one-time migration of your Graphite metrics to the [Librato](https://metrics.librato.com/) monitoring service. It's assumed that you've already transitioned your live metrics feed over to Librato. This utility should only be used to backfill your historical data.

Rather than attempting to coerce the raw Whisper archives to match Librato's [resolution levels](http://support.metrics.librato.com/knowledgebase/articles/66838-understanding-metrics-roll-ups-retention-and-grap), Arigato performs logical queries against the Graphite API, using `summarize()` to roll the results up into compatible resolutions for each interval.

**Note:** By default, Librato will not accept any data [older than 2 hours](http://support.metrics.librato.com/knowledgebase/articles/334530-can-i-send-measurements-from-the-past-or-future). To bypass this restriction you'll need to contact Librato Support for a temporary lifting of this policy using their beta "historical import" feature.

## Usage

### Dependencies

```
$ pip install librato-metrics
```

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

Arigato accepts a list of metric names passed to `STDIN`.

In both of the examples below, we're filtering the results to *only* match `collectd` results, so the `node` argument doesn't need to be specified. The default collectd format passes the hostname in the 2nd (index value `1`) node of the metric string.

**Note:** It may be necessary to migrate portions of your metric namespace at a time to ensure proper `source` identification.

#### Using Carbonate locally

The `carbon-list` utility provided by the [Carbonate](https://github.com/jssjr/carbonate) project is ideal for listing metrics on the Graphite server itself. The results can then by piped into Arigato.

```
$ export PYTHONPATH=$PYTHONPATH:/opt/graphite/lib
$ export LIBRATO_USER=abc
$ export LIBRATO_TOKEN=123

$ carbon-list | grep '^collectd' | \
  python arigato/script.py -p migrated

Processing collectd.graphite-0-1.load.load.shortterm:
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
...
```

#### Curl a Remote Graphite

This method is slightly more convenient if you don't have local access to your Graphite server **or** you can't install Carbonate **or** you want to iterate through a cluster Graphite servers. It does require a bit more effort to prep the output before passing it onto Arigato, however.

```
$ export LIBRATO_USER=abc
$ export LIBRATO_TOKEN=123

$ curl -s http://graphite/metrics/index.json | python -m json.tool | \
  grep '"' | sed 's/ //g' | sed 's/"//g' | sed 's/,//g' | grep '^collectd' | \
  python arigato/script.py -p migrated

Processing collectd.graphite-0-1.load.load.shortterm:
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
    Archive submitted successfully
...
```

### Sample Results

The following screenshots demonstrate Arigato's ability to maintain the proper resolution during the migration. The first chart is a 3-hour window of a single metric on the source Graphite server. The second chart is the same 3-hour window after the metric has been copied to the Librato service.

![Graphite](https://github.com/obfuscurity/arigato/raw/master/img/sample-0.png)
![Librato](https://github.com/obfuscurity/arigato/raw/master/img/sample-1.png)

### License

Arigato is distributed under the MIT license.
