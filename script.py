#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """\
    Copyright (c) 2014 Jason Dixon <jdixon@librato.com>

    Permission to use, copy, modify, and distribute this software for any
    purpose with or without fee is hereby granted, provided that the above
    copyright notice and this permission notice appear in all copies.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.\
        """

import argparse
import fileinput
import urllib2
import json
import os
import sys
import re
import librato

parser = argparse.ArgumentParser(
    description="""Given a list of metrics via STDIN, this
                   script will query a Graphite server and
                   forward the results to your Librato account.""",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-n', '--node', default=1,
                    help='Node to extract source (hostname) from')

parser.add_argument('-p', '--prefix', default=None,
                    help='Prefix for metric name')

parser.add_argument('-u', '--url', default='http://127.0.0.1',
                    help='Graphite server URL')

args = parser.parse_args()

try:
    librato_user = os.environ['LIBRATO_USER']
    librato_token = os.environ['LIBRATO_TOKEN']
    librato_api = librato.connect(librato_user, librato_token)
except KeyError:
    print "missing env vars LIBRATO_USER or LIBRATO_TOKEN"
    sys.exit(1)

# These summarized queries match up with Librato's published retentions
# 2 days at the raw resolution of the metric source
# 1 week at 1 minute resolution
# 1 month at 15 minute resolution
# 1 year at 1 hour resolution
retentions = [
    "/render/?from=-2days&target=%s&format=json",
    "/render/?from=-1week&until=-2days&target=summarize(%s,\"1min\")&format=json",
    "/render/?from=-1month&until=-1week&target=summarize(%s,\"15min\")&format=json",
    "/render/?from=-1year&until=-1month&target=summarize(%s,\"1hour\")&format=json"]

try:
    for metric in fileinput.input([]):
        print "Processing %s:" % metric.strip()

        for query in retentions:

            # construct our Graphite queries
            metric = metric.strip()
            uri = query % metric
            u1 = urllib2.urlopen(args.url + uri)

            try:
                # extract the requested source node
                s = metric.split('.')[int(args.node)]
            except IndexError:
                print "invalid node index"

            # rebuild our metric without the source
            normalized_metric = metric.split('.')
            normalized_metric.pop(int(args.node))
            normalized_metric = '.'.join(normalized_metric)

            # clean-up and apply any prefix
            prefix = args.prefix
            if prefix is not None:
                prefix = re.sub('\s+', '', prefix)
                prefix = re.sub('\.+', '.', prefix)
                prefix = re.sub('^\.', '', prefix)
                prefix = re.sub('\.+$', '', prefix)
                normalized_metric = "%s.%s" % (prefix, normalized_metric)

            # new Librato queue
            q = librato_api.new_queue()
            q_length = 0

            # loop through our Graphite results
            for datapoint in json.loads(u1.read())[0]['datapoints']:
                (value, timestamp) = datapoint

                # skip nulls
                if value is None:
                    continue

                # add to batch request
                q.add(
                    normalized_metric,
                    value,
                    measure_time=timestamp,
                    source=s)
                q_length += 1

            # Finally, submit our batch request
            if q_length > 0:
                q.submit()
            print "    Archive submitted successfully"

except KeyboardInterrupt:
    sys.exit(1)
