import pytest
import os
from moto import mock_dynamodb

@pytest.fixture
def table_name():
    return "polls"

@pytest.fixture
def dynamodb_test(dynamodb_client, table_name):
    dynamodb_client.create_table(
        TableName=table_name,
        AttributeDefinitions=[{
            'AttributeName': 'token',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'email',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'expires_at',
            'AttributeType': 'N'
        }],
        KeySchema=[{
            'AttributeName': 'token',
            'KeyType': 'HASH'
        }],
        GlobalSecondaryIndexes=[{
            'IndexName': 'email-expires_at-index',
            'KeySchema': [{'AttributeName':'email', 'KeyType': 'HASH'},
                         {'AttributeName':'expires_at', 'KeyType': 'RANGE'}],
            'Projection': {
                'ProjectionType': 'INCLUDE',
                'NonKeyAttributes': ['used']
            }
        }],
        BillingMode='PAY_PER_REQUEST')
    os.environ['TOKEN_TABLE_NAME'] = table_name
    os.environ['EMAIL_INDEX_NAME'] = 'email-expires_at-index'
    yield

def gen_error(message):
    return {'body': {'message': message},
            'statusCode': 401}


def test_no_event(dynamodb_client, dynamodb_test):
    from sendToken import sendToken

    event = {}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("No email parameter provided")

def test_empty_email(dynamodb_client, dynamodb_test):
    from sendToken import sendToken

    event = {'email': ''}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")

def test_gmail(dynamodb_client, dynamodb_test):
    from sendToken import sendToken

    event = {'email': 'example@gmail.com'}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")

def test_buckeyemail(dynamodb_client, dynamodb_test):
    from sendToken import sendToken

    event = {'email': 'example@buckeyemail.gmail.com'}
    context = {}
    response = sendToken.lambda_handler(event, context)
    assert response == gen_error("Not a valid OSU email")