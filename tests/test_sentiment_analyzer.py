import pytest
import boto3
import json
import os

# --- THIS IS THE FIX ---
# Add the 'lambda' directory to the Python path so we can import the handler
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lambda')))
# --- END OF FIX ---

# Now this import will succeed
from lambda_function import lambda_handler, analyze_feedback_with_bedrock

# --- Pytest Fixtures: Reusable Setup Code ---

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture(scope='function')
def mock_environment(aws_credentials):
    """Set up the mocked AWS environment and Lambda environment variables."""
    os.environ['DDB_TABLE_NAME'] = 'test-sentiment-table'
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alerts-topic'
    
    with mock_aws():
        s3 = boto3.client('s3', region_name='us-east-1')
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        sns = boto3.client('sns', region_name='us-east-1')
        
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

def test_handler_positive_feedback(mock_environment, monkeypatch):
    """
    Tests the full end-to-end flow with a standard, positive feedback file.
    Verifies data is stored in DynamoDB, but no alerts are sent.
    """
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
    
    s3_event = {
        "Records": [{
            "s3": {
                "bucket": {"name": feedback_bucket},
                "object": {"key": feedback_key}
            }
        }]
    }
    
    result = lambda_handler(s3_event, {})
    
    assert result['statusCode'] == 200
    
    table = mock_environment["dynamodb"].Table(os.environ['DDB_TABLE_NAME'])
    ddb_item = table.get_item(Key={'id': feedback_key})['Item']
    assert ddb_item['sentiment'] == 'positive'
    assert ddb_item['sentiment_score'] == pytest.approx(0.95)
    assert ddb_item['topics'] == ["UI/UX", "Ease of Use"]
    
    assert len(sns_calls) == 0
    assert len(cw_calls) == 0


def test_handler_negative_high_urgency_feedback(mock_environment, monkeypatch):
    """
    Tests the full flow with negative, high-urgency feedback.
    Verifies that a CloudWatch metric and an SNS alert ARE sent.
    """
    feedback_bucket = 'test-feedback-bucket'
    feedback_key = 'urgent-issue.txt'
    feedback_content = "I can't access my account and my data seems to be gone! This is a critical issue!"

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
    
    mock_environment["s3"].put_object(Bucket=feedback_bucket, Key=feedback_key, Body=feedback_content)
    
    s3_event = {
        "Records": [{"s3": {"bucket": {"name": feedback_bucket}, "object": {"key": feedback_key}}}]
    }
    
    lambda_handler(s3_event, {})
    
    assert len(cw_calls) == 1
    assert len(sns_calls) == 1
    assert sns_calls[0]['urgency'] == 'high'

def test_bedrock_output_parsing_with_extra_text(monkeypatch):
    """
    Unit tests the `analyze_feedback_with_bedrock` function specifically.
    Ensures the regex correctly extracts a JSON object even if the LLM adds extra text.
    """
    messy_llm_output = """
    Of course! Here is the analysis of the customer feedback you requested.
    
    ```json
    {
        "sentiment": "negative",
        "sentiment_score": 0.2,
        "topics": ["Billing", "Customer Support"],
        "urgency": "medium"
    }
    ```
    """
    
    def mock_invoke_model(*args, **kwargs):
        return {
            "body": {
                "read": lambda: json.dumps({"generation": messy_llm_output}).encode('utf-8')
            }
        }
    
    # We need to mock the bedrock client from within the lambda_function's scope
    # Since lambda_function.py does `bedrock = boto3.client(...)`, we patch that specific instance.
    monkeypatch.setattr('lambda_function.bedrock.invoke_model', mock_invoke_model)

    result = analyze_feedback_with_bedrock("some feedback text")

    assert result['sentiment'] == 'negative'
    assert result['urgency'] == 'medium'
    assert 'error' not in result
    assert len(result) == 4