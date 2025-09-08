# test/test_lambda_function.py

import pytest
import boto3
import json
import os
import io
from moto import mock_aws

# --- Environment Setup for Moto ---
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DDB_TABLE_NAME'] = 'test-sentiment-table'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts-topic'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'

# Add the source directory to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function')))

from lambda_function import lambda_handler, analyze_feedback_with_bedrock

# --- Pytest Fixtures ---
@pytest.fixture(scope='function')
def mock_aws_environment():
    """Sets up a mocked AWS environment using Moto."""
    with mock_aws():
        s3 = boto3.client('s3', region_name=os.environ['AWS_DEFAULT_REGION'])
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_DEFAULT_REGION'])
        sns = boto3.client('sns', region_name=os.environ['AWS_DEFAULT_REGION'])
        
        s3.create_bucket(Bucket='test-feedback-bucket')
        dynamodb.create_table(
            TableName=os.environ['DDB_TABLE_NAME'],
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        # Correctly create the topic using the name from the ARN
        sns.create_topic(Name=os.environ['SNS_TOPIC_ARN'].split(':')[-1])
        
        yield { "s3": s3, "dynamodb": dynamodb, "sns": sns }

# --- Test Cases ---
def test_handler_positive_feedback(mock_aws_environment, monkeypatch):
    """Tests the end-to-end flow for a positive review, ensuring no alerts are sent."""
    feedback_bucket = 'test-feedback-bucket'
    feedback_key = 'positive-review.txt'
    feedback_content = "The new user interface is fantastic and very easy to use. Great job!"
    
    mock_bedrock_response = {
        "sentiment": "positive",
        "sentiment_score": 0.95,
        "topics": ["UI/UX", "Ease of Use"],
        "urgency": "low"
    }
    monkeypatch.setattr('lambda_function.analyze_feedback_with_bedrock', lambda text: mock_bedrock_response)

    sns_calls = []
    cw_calls = []
    monkeypatch.setattr('lambda_function.send_sns_alert', lambda analysis: sns_calls.append(analysis))
    monkeypatch.setattr('lambda_function.publish_negative_sentiment_metric', lambda: cw_calls.append(True))
    
    mock_aws_environment["s3"].put_object(Bucket=feedback_bucket, Key=feedback_key, Body=feedback_content)
    s3_event = { "Records": [{"s3": {"bucket": {"name": feedback_bucket}, "object": {"key": feedback_key}}}] }
    result = lambda_handler(s3_event, {})
    
    assert result['statusCode'] == 200
    table = mock_aws_environment["dynamodb"].Table(os.environ['DDB_TABLE_NAME'])
    ddb_item = table.get_item(Key={'id': feedback_key})['Item']
    assert ddb_item['sentiment'] == 'positive'
    assert len(sns_calls) == 0
    assert len(cw_calls) == 0

def test_handler_negative_high_urgency_feedback(mock_aws_environment