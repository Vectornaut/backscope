# Logging

## Where to find logs

### Basics

Logs are kept in the `logs` directory, in the [rotating log files](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.RotatingFileHandler) `api.log`, `api.log.1`, …, `api.log.9`. These files are created automatically as needed. The newest logs are at the end of `api.log`.

When the `DEVELOPMENT` environment flag is set, logs are also printed to the console. The console logs include events that aren't important enough to store long-term in the log files.

### File rotation

When `api.log` fills up to its maximum size of 20&nbsp;MB, it's renamed to `api.log.1`, while the former `api.log.1` becomes `api.log.2`, …, the former `api.log.8` becomes `api.log.9`, and the former `api.log.9` is deleted.

If there's a big problem that creates enough log entries and fills up all the log files, we'll start losing the logs from the beginning of the problem, which might be the most valuable ones. The logs might fill up after as few as 20,000 entries, based on the estimate that a 404 error from the OEIS generates a 5–10&nbsp;kB log entry. We could avoid this pitfall by switching from size-based to time-based rotation. That doesn't seem worth the trouble at our current small scale, though.

## How to read logs

### Format

On the terminal, log entries are printed in a pretty, somewhat human-readable format. Unfortunately, some log entries contain very long values, like HTTP request dumps. This makes them a lot less readable. That might be a good thing to fix.

In the log files, each entry is written on its own line as a JSON dictionary. The string stored in the "event" key tells you what kind of event each entry describes. Here are some known event types. The ones in bold are directly generated by Backscope.

* "Exception on..." – Uncaught exception
* **"request issue"** – Problem with an HTTP request

### Event types

#### Uncaught exception

When the event string starts with "Exception on...", the log entry describes an uncaught exception.

#### Request issue

A "request issue" event describes a problem with an HTTP request. It should always come with a dump of the associated request-response conversation, stored in the key "response" as a base64 string:
```
"response": "PCBHRVQgc3R1ZmYNCjwgSFRUUC8xLjENCg=="
```
Applying [`base64.b64decode`](https://docs.python.org/3/library/base64.html#base64.b64decode) to the conversation will turn it into byte array, like this:
```python
b'< GET stuff\\r\\n< HTTP/1.1\\r\\n< Host: oeis.org\\r\\n< ...'
```
You can turn the byte array into a string, for printing or other uses, by calling its `decode('utf-8')` method. To understand how this string is formatted, let's look at an actual example (somewhat shortened). In the conversation below, we ask the OEIS for the B-file of a non-existent sequence, and we get a 404 error in response. To distinguish the two sides of the conversation, a `<` is added to the start of every request line, and a `>` is added to the start of every response line. (The last line of the response breaks over several lines when it's printed out here, because it contains newline characters.)
```
< GET /A000000/b000000.txt HTTP/1.1
< Host: oeis.org
< User-Agent: python-requests/2.31.0
< Accept-Encoding: gzip, deflate
< Accept: */*
< Connection: keep-alive
< 

> HTTP/1.1 404 Not Found
> Cache-Control: private, no-store
> Content-Type: text/html; charset=utf-8
> Date: Thu, 11 Apr 2024 04:05:59 GMT
> Vary: *
> Transfer-Encoding: chunked
> 

<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
  
  <head>
  <!-- ... -->
  
  <title>The On-Line Encyclopedia of Integer Sequences&reg; (OEIS&reg;)</title>
  <link rel="search" type="application/opensearchdescription+xml" title="OEIS" href="/oeis.xml">
  <script>
  var myURL = "\/A000000\/b000000.txt"
  function redir() {
      var host = document.location.hostname;
      if(host != "oeis.org" && host != "127.0.0.1" && host != "localhost" && host != "localhost.localdomain") {
          document.location = "https"+":"+"//"+"oeis"+".org/" + myURL;
      }
  }
  function sf() {
      if(document.location.pathname == "/" && document.f) document.f.q.focus();
  }
  </script>
  </head>
  <body bgcolor=#ffffff onload="redir();sf()">
    <!-- ... -->
  </body>
</html>
```

## Choosing the level of detail

What gets logged depends on what environment mode Backscope is running in. Each log entry is assigned a [level of importance](https://docs.python.org/3/library/logging.html#logging-levels). From highest to lowest, the possible levels are: *critical*, *error*, *warning*, *info*, *debug*.

The file logs include all entries at *warning* level or higher. If the `DEVELOPMENT` environment flag is set, the console log includes all entries at *info* level or higher, and it also includes entries at *debug* level if the `DEBUG` flag is set. Without the `DEVELOPMENT` flag, the console log is silent.

## How to write logs

### Package documentation

We use [*structlog*](https://www.structlog.org/) package.

### Basic usage

#### Starting a draft log entry

The function call
```python
current_app.structlogger.bind(tags=[])
```
returns a draft of a log entry, with no content except an empty list of tags.

As this example shows, the app keeps its structured logger in the custom `structlogger` attribute. The default `logger` attribute still points to the basic logger that Flask is presumably designed to use internally. The basic logger feeds its output into the structured logger. Backscope should always write logs to `current_app.structlogger`, bypassing the basic logger.

#### Updating a draft log entry

If `log` is a log entry, the method call
```python
log.bind(attempts=8, mood='confused')
```
returns an updated version of `log` with (possibly new) keys `'attempts'` and `'mood'` holding the values `8` and `'confused'`, respectively. Keep in mind that all values will ultimately be converted to strings and written in a JSON file or printed to the console.

The entry that `log` points to is not modified. If you want to use the updated log entry, you have to store the reference to it that `log.bind` returns! In most cases, you'll want to throw away the old version of the log entry and keep the new version in its place. In that case, you might use the pattern
```python
log = log.bind(attempts=8, mood='confused')
```

#### Adding and removing tags

If `log` is a log entry, the call
```python
structlog.get_context(log)['tags']
```
returns a reference to the entry's `tags` attribute. You can use that reference to add and remove tags.

#### Writing a log entry

Once you've finished drafting a log entry, you can write it to the log by calling
```python
log.error('connection failed')
```
The string `'connection failed'` should describe the event being logged. It becomes the value of the `'event'` key.

## Testing the logging system

### Automated tests

Automated tests that involve the logging system include:
 - [test_logging.py](/flaskr/nscope/test/test_logging.py)
   - `LoggingTest`
 - [test_lookup_errors.py](/flaskr/nscope/test/test_lookup_errors.py)
   - `TestNonexistentSequence`

### Manual tests

An easy way to manually generate a log entry is to request values from a non-existent series. For example, you could launch Backscope locally and visit the following URL in a web browser:
```
http://localhost:5000/api/get_oeis_values/A000000/12
```
Backscope should return the following message:

> Error: B-file for ID 'A000000' not found in OEIS.

At the same time, it should add a line to the end of `api.log`. You can use `'timestamp'` values to distinguish new log entries from old ones. Right now, when Backscope fails to retrieve information about a sequence, it gets stuck thinking it's waiting for metadata, so future requests for the same sequence will get the response:

> Error: Value fetching for {oeis_id} in progress.

Right now, to request the same sequence again and see the same behavior, you first have to clear the database with `flask clear-database`.

:warning: **Beware:** this will clear the database named by the `POSTGRES_DB` variable in the `.env` file.