import unittest
import flaskr.nscope.test.abstract_endpoint_test as abstract_endpoint_test


class TestGetOEISValuesWithoutShift(abstract_endpoint_test.AbstractEndpointTest):
  endpoint = 'http://localhost:5000/api/get_oeis_values/A153080/12'
  
  # we choose A153080 because:
  # - it has zero shift, so the test can pass even if the shift defaults to zero
  # - it currently has small values and few references, which speeds up the
  #   background work triggered by the request
  expected_response = {
    'id': 'A153080',
    'name': 'A153080 [name not yet loaded]',
    'values': {
      '0': '2',
      '1': '15',
      '2': '28',
      '3': '41',
      '4': '54',
      '5': '67',
      '6': '80',
      '7': '93',
      '8': '106',
      '9': '119',
      '10': '132',
      '11': '145'
    }
  }

class TestGetOEISValues(abstract_endpoint_test.AbstractEndpointTest):
  endpoint = 'http://localhost:5000/api/get_oeis_values/A321580/12'
  
  # we choose A321580 because:
  # - it has a nonzero shift, so we can make sure the default value is getting
  #   changed to the actual value
  # - it currently has small values and few references, which speeds up the
  #   background work triggered by the request
  expected_response = {
    'id': 'A321580',
    'name': 'A321580 [name not yet loaded]',
    'values': {
      '1': '1',
      '2': '2',
      '3': '4',
      '4': '8',
      '5': '10',
      '6': '12',
      '7': '16',
      '8': '18',
      '9': '24',
      '10': '26',
      '11': '28',
      '12': '32'
    }
  }

class TestGetOEISValuesNegativeShift(abstract_endpoint_test.AbstractEndpointTest):
  endpoint = 'http://localhost:5000/api/get_oeis_values/A078302/10'

  # we choose A078302 because:
  # - it has a negative shift, so we can make sure such shifts do not prevent
  #   the parsing of the b-file (per #50)
  # - it currently has small values and few references, which speeds up the
  #   background work triggered by the request
  # - it only has four values, so we can make sure it works to request more
  #   values than exist
  # - its b-file has a comment, so we test that pulling the initial name from
  #   such a comment works
  expected_response = {
    'id': 'A078302',
    'name': ' A078302 (b-file synthesized from sequence entry)',
    'values': {
      '-43': '5',
      '-42': '3',
      '-41': '9',
      '-40': '1'
    }
  }

if __name__ == "__main__":
    unittest.main()
