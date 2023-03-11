import pytest
import os
import sys
from moto import mock_dynamodb
from datetime import datetime

# Cringe hack to import lambda src
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../src/')

# Generate error response with custom message
def gen_error(message):
    return {'body': {'message': message},
            'statusCode': 401}


# === TESTS ===

def test_stub(dynamodb_client):
    os.environ['POLL_TABLE_NAME'] = "stub"
    from submitPoll import submitPoll

    assert 1 == 1