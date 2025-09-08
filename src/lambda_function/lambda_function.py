# src/lambda_function/lambda_function.py

import boto3
import json
import os
import re # Import the regular expression module
from decimal import Decimal
from urllib.parse import unquote_plus

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
cloudwatch = boto3.client("cloudwatch")
bedrock = boto3.client("bedrock-runtime")
sns = boto3.client("sns")

# These environment variables are set by our Terraform module
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

table = dynamodb.Table(DDB_TABLE_NAME)

def lambda_handler(event, context):
    """
    Main handler function triggered by S3.
    """
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        # 1. Get feedback file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        raw_data = response["Body"].read()
        try:
            text_data = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            print("UTF-8 decode failed, trying other common encodings.")
            text_data = raw_data.decode("latin-1") # A common fallback

        # 2. Analyze the feedback text with Bedrock
        analysis = analyze_feedback_with_bedrock(text_data)

        # 3. Store the results in DynamoDB
        store_results_in_dynamodb(key, analysis)

        # 4. Handle alerts and metrics based on analysis
        handle_analysis(analysis)

    return {"statusCode": 200, "body": json.dumps("Processing complete.")}

def analyze_feedback_with_bedrock(text):
    """
    Uses Bedrock's Llama 3 model to analyze sentiment, topics, and urgency.
    """
    prompt = f"""
    You are a text analysis expert. Analyze the following customer feedback.
    Feedback: "{text}"
    
    Your entire response must be ONLY a single, valid JSON object and nothing else. Do not add any explanation, commentary, or markdown formatting like ```json.
    
    The JSON object must have these exact keys:
    "sentiment": (string: "positive", "negative", or "neutral")
    "sentiment_score": (float between 0.0 and 1.0)
    "topics": (array of strings)
    "urgency": (string: "low", "medium", or "high")
    """

    body = json.dumps({
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature": 0
    })

    response = bedrock.invoke_model(
        modelId="meta.llama3-8b-instruct-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    response_body = json.loads(response["body"].read())
    output_text = response_body['generation']

    try:
        # Greedily find the first JSON object in the model's response.
        json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
        else:
            raise ValueError("No JSON object found in the model's response.")
            
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error processing model output: {e}")
        print(f"Raw output from model: {output_text}")
        result = {
            "sentiment": "unknown",
            "sentiment_score": 0.0,
            "topics": [],
            "urgency": "low",
            "error": "Failed to parse model output",
            "raw_output": output_text
        }
    return result

def store_results_in_dynamodb(item_id, analysis):
    """
    Stores the analysis results in the DynamoDB table.
    """
    score = analysis.get("sentiment_score", 0.0)
    if not isinstance(score, (int, float)):
        score = 0.0

    table.put_item(Item={
        "id": item_id,
        "sentiment": analysis.get("sentiment", "unknown"),
        "sentiment_score": Decimal(str(score)),
        "topics": analysis.get("topics", []),
        "urgency": analysis.get("urgency", "low")
    })

def handle_analysis(analysis):
    """
    Triggers CloudWatch metrics and SNS alerts based on the analysis.
    """
    sentiment = analysis.get("sentiment", "unknown").lower()
    urgency = analysis.get("urgency", "low").lower()

    if sentiment == "negative":
        publish_negative_sentiment_metric()
    if urgency == "high":
        send_sns_alert(analysis)

def publish_negative_sentiment_metric():
    """
    Publishes a custom CloudWatch metric for a negative sentiment event.
    """
    cloudwatch.put_metric_data(
        Namespace="SentimentDetective",
        MetricData=[{ "MetricName": "NegativeSentimentCount", "Value": 1, "Unit": "Count" }]
    )

def send_sns_alert(analysis):
    """
    Sends a formatted alert to the SNS topic for high-urgency issues.
    """
    message = (
        f"🚨 High urgency issue detected!\n\n"
        f"Sentiment: {analysis.get('sentiment', 'N/A').capitalize()}\n"
        f"Topics: {', '.join(analysis.get('topics', ['N/A']))}\n"
        f"Urgency: {analysis.get('urgency', 'N/A').capitalize()}"
    )
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="High Urgency Customer Feedback Detected"
    )