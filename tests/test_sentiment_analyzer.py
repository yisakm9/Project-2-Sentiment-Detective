import pytest
import boto3
import json
import os
import io
from moto import mock_aws

# Set ALL required environment variables BEFORE the lambda_function is imported.
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DDB_TABLE_NAME'] = 'test-sentiment-table'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts-topic'

# Add the 'lambda' directory to the Python path so we can import the handler
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lambda')))

# This import will now succeed
from lambda_function import lambda_handler, analyze_feedback_with_bedrock

# --- Pytest Fixtures ---

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='function')
def mock_environment(aws_credentials):
    """Set up the mocked AWS environment."""
    with mock_aws():
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        sns = boto3.client('sns')
        
        s3.create_bucket(Bucket='test-feedback-bucket')
        dynamodb.create_table(
            TableName=os.environ['DDB_TABLE_NAME'],
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        sns.create_topic(Name='test-alerts-topic')
        
        yield {
            "s3": s3,
            "dynamodb": dynamodb,
            "sns": sns
        }

# --- Test Cases ---

# --- FIX: Add aws_credentials fixture as an argument ---
def test_handler_positive_feedback(aws_credentials, mock_environment, monkeypatch):
    feedback_bucket = 'test-feedback-bucket'
    feedback_key = 'positive-review.txt'
    feedback_content = "The new user interface is fantastic and very easy to use. Great job!"
    
    mock_bedrock_response = {
        "sentiment": "positive",
        "sentiment_score": 0.95,
        "topics": ["UI/UX", "Ease of Use"],
        "urgency": "low"
    }

    def mock_analyze_feedback(*args, **kwargs):
        return mock_bedrock_response
    monkeypatch.setattr('lambda_function.analyze_feedback_with_bedrock', mock_analyze_feedback)

    sns_calls = []
    cw_calls = []
    monkeypatch.setattr('lambda_function.send_sns_alert', lambda analysis: sns_calls.append(analysis))
    monkeypatch.setattr('lambda_function.publish_negative_sentiment_metric', lambda: cw_calls.append(True))
    
    mock_environment["s3"].put_object(Bucket=feedback_bucket, Key=feedback_key, Body=feedback_content)
    
    s3_event = { "Records": [{"s3": {"bucket": {"name": feedback_bucket}, "object": {"key": feedback_key}}}] }
    
    result = lambda_handler(s3_event, {})
    
    assert result['statusCode'] == 200
    
    table = mock_environment["dynamodb"].Table(os.environ['DDB_TABLE_NAME'])
    ddb_item = table.get_item(Key={'id': feedback_key})['Item']
    assert ddb_item['sentiment'] == 'positive'
    
    assert len(sns_calls) == 0
    assert len(cw_calls) == 0


# --- FIX: Add aws_credentials fixture as an argument ---
def test_handler_negative_high_urgency_feedback(aws_credentials, mock_environment, monkeypatch):
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
    
    mock_environment["s3"].put_object(Bucket=feedback_bucket, Key=feedback_key, Body="irrelevant")
    
    s3_event = { "Records": [{"s3": {"bucket": {"name": feedback_bucket}, "object": {"key": feedback_key}}}] }
    
    lambda_handler(s3_event, {})
    
    assert len(cw_calls) == 1
    assert len(sns_calls) == 1
    assert sns_calls[0]['urgency'] == 'high'

def test_bedrock_output_parsing_with_extra_text(monkeypatch):
    messy_llm_output = '```json\n{"sentiment": "negative", "sentiment_score": 0.2, "topics": ["Billing"], "urgency": "medium"}\n```'
    
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