from structlog.testing import capture_logs
import sys
import unittest

import flaskr.nscope.views as views
from flaskr import create_app, db, clear_database


# required attributes:
#
#  --- endpoint ---
#  the endpoint we're requesting
#
#  --- expected_response ---
#  the dictionary or string we expect to get back
#
# optional attributes:
#
#  --- expected_log_output ---
#  the list of log entries we expect the request to produce. each entry is a
#  dictionary, which would be written in JSON format in the log
#
# optional methods:
#
#  --- process_log_entry ---
#  this method is called on each recorded log entry before comparison with the
#  expected log output. it can be used to modify each log entry in place. this
#  is useful for removing time-dependent parts of log entries, like the date
#  line in an HTTP response
#

# guidance on test database handling:
#   https://stackoverflow.com/a/17818795
#   https://flask-testing.readthedocs.io/en/v0.4/

class AbstractEndpointTest(unittest.TestCase):
  def assert_endpoint_test_attr(self, name):
    assert hasattr(self, name), (
      f"Can't construct a '{type(self).__name__}' "
      f"endpoint test without '{name}' attribute"
    )

  def __init__(self, *args, **kwargs):
    # make sure required attributes are present
    self.assert_endpoint_test_attr('endpoint')
    self.assert_endpoint_test_attr('expected_response')

    # check whether unittest is running in verbose mode
    # hat tip StackOverflow users Dimitris Fasarakis Hilliard and EquipDev...
    #   https://stackoverflow.com/a/43002355
    #   https://stackoverflow.com/questions/43001768/how-can-a-test-in-python-unittest-get-access-to-the-verbosity-level#comment73163492_43002355
    # ... who provided this code under the MIT license
    #   https://meta.stackexchange.com/q/271080
    self.verbose = ('-v' in sys.argv) or ('--verbose' in sys.argv)

    super().__init__(*args, *kwargs)

  def setUp(self):
    self.app = create_app('testing')
    self.ctx = self.app.app_context()
    with self.ctx:
      clear_database()

    # put mid-test messages on a new line
    if self.verbose:
      print()

  def tearDown(self):
    # wait for background work to finish
    if self.verbose:
      print("  Waiting for background work")
    views.executor.shutdown()
    if self.verbose:
      print("  Background work done")

    # clear database
    db.session.remove()
    with self.ctx:
      db.drop_all()

  def test_endpoint(self):
    # using test client is recommended in Flask testing how-to
    #   https://flask.palletsprojects.com/en/2.3.x/testing/
    # "The test client makes requests to the application without running a live
    # server." the `with` block runs teardown
    #   https://github.com/pallets/flask/issues/2949
    with self.app.test_client() as client, capture_logs() as log_output:
      if self.verbose:
        print("  Testing response")

      # check status
      response = client.get(self.endpoint)
      self.assertEqual(response.status_code, 200)
      
      # check response
      response_type = type(self.expected_response)
      if issubclass(response_type, dict):
        self.assertDictEqual(response.json, self.expected_response)
      elif issubclass(response_type, str):
        self.assertEqual(response.text, self.expected_response)
      else:
        raise TypeError(
          f"In a '{type(self).__name__}' endpoint test, the expected response "
          "must be a dictionary or a string, not an object of type "
          f"'{response_type.__name__}'"
        )

      # check logs
      if hasattr(self, 'expected_log_output'):
        # sort the keys in each log entry
        sorted_log_output = [dict(sorted(entry.items())) for entry in log_output]

        # process log entries
        if hasattr(self, 'process_log_entry') and callable(self.process_log_entry):
          for entry in sorted_log_output:
            self.process_log_entry(entry)

        self.assertEqual(sorted_log_output, self.expected_log_output)

      # TO DO: test background work