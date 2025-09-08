# test/test_lambda_function.py

import pytest
import boto3
import json
import os
import io
from moto import mock_aws

# --- Environment Setup for Moto ---
# This block sets dummy AWS credentials and environment variables required by the Lambda code.
# It must run before the lambda_function is imported, as boto3 clients are initialized at the module level.
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DDB_TABLE_NAME'] = 'test-sentiment-table'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts-topic'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'

# Add the source directory to the Python path to allow for the local import
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function')))

# This import will now succeed because the path and environment variables are set
from lambda_function import lambda_handler, analyze_feedback_with_bedrock

# --- Pytest Fixtures ---
@pytest.fixture(scope='function')
def mock_aws_environment():
    """Sets up a mocked AWS environment using Moto."""
    with mock_aws():
        s3 = boto3.client('s3', region_name=os.environ['AWS_DEFAULT_REGION'])
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_DEFAULT_REGION'])
        sns = boto3.client('sns', region_name=os.environ['AWS_DEFAULT_REGION'])
        
        # Create mock resources
        s3.create_bucket(Bucket='test-feedback-bucket')
        dynamodb.create_table(
            TableName=os.environ['DDB_TABLE_NAME'],
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        sns.create_topic(Name=os.environ['SNS_TOPIC_ARN'].split(':')[-1])
        
        yield {
            "s3": s3,
            "dynamodb": dynamodb,
            "sns": sns
        }

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

    # Mock the Bedrock call to return a predictable positive response
    monkeypatch.setattr('lambda_function.analyze_feedback_with_bedrock', lambda text: mock_bedrock_response)

    # Mock the alert/metric functions to track if they are called
    sns_calls = []
    cw_calls = []
    monkeypatch.setattr('lambda_function.send_sns_alert', lambda analysis: sns_calls.append(analysis))
    monkeypatch.setattr('lambda_function.publish_negative_sentiment_metric', lambda: cw_calls.append(True))
    
    # 1. SETUP: Upload a mock file to the mock S3 bucket
    mock_aws_environment["s3"].put_object(Bucket=feedback_bucket, Key=feedback_key, Body=feedback_content)
    
    # 2. TRIGGER: Create the S3 event payload that Lambda expects
    s3_event = { "Records": [{"s3": {"bucket": {"name": feedback_bucket}, "object": {"key": feedback_key}}}] }
    
    # 3. EXECUTE: Call the handler
    result = lambda_handler(s3_event, {})
    
    # 4. ASSERT: Verify the outcomes
    assert result['statusCode'] == 200
    
    table = mock_aws_environment["dynamodb"].Table(os.environ['DDB_TABLE_NAME'])
    ddb_item = table.get_item(Key={'id': feedback_key})['Item']
    assert ddb_item['sentiment'] == 'positive'
    
    # Assert that no alerts or negative metrics were published
    assert len(sns_calls) == 0
    assert len(cw_calls) == 0

def test_handler_negative_high_urgency_feedback(mock_aws_environment, monkeypatch):
    """Tests the end-to-end flow for a negative, urgent review, ensuring alerts are sent."""
    feedback_bucket = 'test-feedback-bucket'
    feedback_key = 'urgent-issue.txt'
    
    mock_bedrock_response = {
        "sentiment": "negative",
        "sentiment_score": 0.1,
        "topics": ["Account Access", "Data Loss"],
        "urgency": "high"
    }
    monkeypatch.setattr('lambda_function.analyze_feedback_with_bedrock', lambda text: mock_bedrock_response)

    sns_calls = []
    cw_calls = []
    monkeypatch.setattr('lambda_function.send_sns_alert', lambda analysis: sns_calls.append(analysis))
    monkeypatch.setattr('lambda_function.publish_negative_sentiment_metric', lambda: cw_calls.append(True))
    
    mock_aws_environment["s3"].put_object(Bucket=feedback_bucket, Key=feedback_key, Body="The site crashed and I think I lost my data!")
    
    s3_event = { "Records": [{"s3": {"bucket": {"name": feedback_bucket}, "object": {"key": feedback_key}}}] }
    
    lambda_handler(s3_event, {})
    
    # Assert that a CloudWatch metric was published AND an SNS alert was sent
    assert len(cw_calls) == 1
    assert len(sns_calls) == 1
    assert sns_calls['urgency'] == 'high'

def test_bedrock_output_parsing_with_extra_text(monkeypatch):
    """Tests the regex's ability to extract JSON from a messy LLM output."""
    messy_llm_output = 'Sure, here is the JSON you requested:\n```json\n{"sentiment": "negative", "sentiment_score": 0.2, "topics": ["Billing"], "urgency": "medium"}\n```\nLet me know if you need anything else!'
    
    # Mock the boto3 call to return a body with the messy text
    def mock_invoke_model(*args, **kwargs):
        response_payload = json.dumps({"generation": messy_llm_output})
        return {
            'body': io.BytesIO(response_payload.encode('utf-8'))
        }
    monkeypatch.setattr('lambda_function.bedrock.invoke_model', mock_invoke_model)

    result = analyze_feedback_with_bedrock("some feedback text")

    assert result['sentiment'] == 'negative'
    assert result['urgency'] == 'medium'
    assert 'error' not in result