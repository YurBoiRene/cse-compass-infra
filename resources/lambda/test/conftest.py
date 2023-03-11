import boto3
import os
import pytest

from moto import mock_dynamodb


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-2"


@pytest.fixture
def dynamodb_client(aws_credentials):
    with mock_dynamodb():
        conn = boto3.client("dynamodb", region_name="us-east-2")
        yield conn

# Sets up tokens table for mocking
@pytest.fixture
def tokens_table_test(dynamodb_client):
    TABLE_NAME = "tokens"
    dynamodb_client.create_table(
        TableName=TABLE_NAME,
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
    os.environ['TOKEN_TABLE_NAME'] = TABLE_NAME
    os.environ['EMAIL_INDEX_NAME'] = 'email-expires_at-index'
    yield