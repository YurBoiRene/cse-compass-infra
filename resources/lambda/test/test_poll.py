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

def test_no_event(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("No email parameter provided")

def test_empty_email(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': ''}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")

def test_gmail(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': 'example@gmail.com'}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")

def test_buckeyemail(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': 'example@buckeyemail.osu.edu'}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")

    
def test_bad_osu(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': 'descartes@osu.edu'}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")

def test_good_osu(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': 'descartes.1337@osu.edu'}
    context = {}
    response = sendToken.lambda_handler(event, context)

    assert response['statusCode'] == 200
    assert isinstance(response['body']['expires_at'], int)

    assert response['body']['expires_at'] > round(datetime.now().timestamp())
    # TODO read table to check if token is present
    
def test_same_email(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': 'descartes.1337@osu.edu'}
    context = {}
    response1 = sendToken.lambda_handler(event, context)

    assert response1['statusCode'] == 200
    
    response2 = sendToken.lambda_handler(event, context)
    assert response2 == gen_error("Email already has active token.")
    # TODO read table to check if token is present
    

def test_spam(dynamodb_client, tokens_table_test):
    from sendToken import sendToken

    event = {'email': 'descartes.1337@osu.edu'}
    context = {}
    response = sendToken.lambda_handler(event, context)

    assert response['statusCode'] == 200
    
    for i in range(50): 
        response = sendToken.lambda_handler(event, context)
        assert response == gen_error("Email already has active token.")
    # TODO read table to check if token is present