# Sentiment Detective: Serverless Text Analysis with AWS and Bedrock

This project outlines a robust, serverless architecture on AWS for performing sentiment and text analysis on customer feedback files. It leverages Amazon Bedrock's powerful foundation models to analyze text, stores the results for further analysis, and triggers alerts for high-urgency or negative feedback. The entire infrastructure is managed using Terraform and deployed via a multi-environment CI/CD pipeline with GitHub Actions.

# Table of Contents

  - [Architecture Overview](https://www.google.com/search?q=%23architecture-overview)
  - [Key Features](https://www.google.com/search?q=%23key-features)
  - [CI/CD Pipeline](https://www.google.com/search?q=%23cicd-pipeline)
      - [Deployment Workflow](https://www.google.com/search?q=%23deployment-workflow)
      - [Destroy Workflow](https://www.google.com/search?q=%23destroy-workflow)
  - [How It Works](https://www.google.com/search?q=%23how-it-works)
  - [Infrastructure as Code (IaC)](https://www.google.com/search?q=%23infrastructure-as-code-iac)
      - [Terraform Variables](https://www.google.com/search?q=%23terraform-variables)
      - [Environment Configuration](https://www.google.com/search?q=%23environment-configuration)
  - [Getting Started](https://www.google.com/search?q=%23getting-started)

# Architecture Overview

The architecture is designed to be event-driven and scalable. When a new feedback file is uploaded to the designated S3 bucket, it triggers a series of automated actions:

1.  **S3 Upload Trigger**: A text file containing customer feedback is uploaded to an S3 bucket.
2.  [cite\_start]**Lambda Invocation**: The S3 `ObjectCreated` event [cite: 26] triggers an AWS Lambda function.
3.  **Text Analysis with Bedrock**: The Lambda function invokes an Amazon Bedrock foundation model (`meta.llama3-8b-instruct-v1:0`) to analyze the text for sentiment, key topics, and urgency.
4.  [cite\_start]**Store Results in DynamoDB**: The analysis results are stored in a DynamoDB table[cite: 17], using the S3 object key as the unique identifier.
5.  **Alerting & Monitoring**:
      * [cite\_start]If the feedback is identified as "high urgency," an alert is immediately published to an SNS topic[cite: 21], which then sends an email notification to a configured address.
      * [cite\_start]If the feedback has a "negative" sentiment, the function publishes a custom metric to CloudWatch[cite: 21].
      * [cite\_start]A CloudWatch Alarm [cite: 27] monitors this metric. If the number of negative feedback events surpasses a defined threshold within a 5-minute window, it triggers an SNS alert.

 ---

# Key Features

  * Serverless First: Built entirely on serverless components (S3, Lambda, DynamoDB) for automatic scaling and cost-efficiency.
  * AI-Powered Analysis: Utilizes Amazon Bedrock for sophisticated, AI-driven text analysis.
  * Infrastructure as Code (IaC): The entire AWS infrastructure is defined and managed with Terraform, ensuring consistency and reproducibility.
  * Multi-Environment CI/CD: Automated deployment pipeline using GitHub Actions for `development`, `staging`, and `production` environments.
  * Automated Alerting: Proactive notifications for high-urgency and negative sentiment trends via SNS and CloudWatch Alarms.
  * Configurable Environments: Each environment is configured via its own `.tfvars` file, allowing for different settings (e.g., lower alarm thresholds in development).



# CI/CD Pipeline

The project is managed by two distinct GitHub Actions workflows: `deploy.yml` for deployment and `destroy.yml` for infrastructure teardown.

# Deployment Workflow (`deploy.yml`)

This workflow automates the testing, building, and deployment of the application.

*Triggers:

  * A `push` to the `develop` branch deploys to the development environment.
  * A `push` to the `staging` branch deploys to the staging environment.
  * A `push` to the `main` branch deploys to the production environment.
  * Can also be run manually via `workflow_dispatch`.

Jobs:

1.  lint-and-test :
      * Checks out the code.
      * Installs Python dependencies from `lambda/requirements.txt`.
      * Lints the Python code using `flake8`.
      * Runs unit tests using `pytest`.
2.   build :
      * Creates a `lambda_package.zip` artifact containing the Lambda function code and its Python dependencies.
      * Uploads the artifact to be used in the deployment job.
3.   deploy :
      * Depends on the success of the lint, test, and build jobs.
      * Downloads the Lambda artifact.
      * Configures AWS credentials using repository secrets.
      * Selects the appropriate `.tfvars` file (`dev.tfvars`, `staging.tfvars`, or `prod.tfvars`) based on the branch name.
      * Runs terraform init , terraform plan, and terraform apply to deploy the infrastructure.

# Destroy Workflow (`destroy.yml`)

This workflow provides a manual, safe way to tear down an environment's infrastructure.

Trigger:

  * Triggered manually using GitHub's `workflow_dispatch` event.
  * Requires the user to select the target environment (`development`, `staging`, or `production`) from a dropdown list.

Jobs:

1.  `destroy`:
      * Configures AWS credentials.
      * Sets up Terraform.
      * **Creates a dummy `lambda_package.zip` file. This is a crucial step to satisfy the `filebase64sha256()` function in the Terraform configuration, which requires the file to exist even during a destroy operation.
      * Selects the correct `.tfvars` file based on the user's input.
      * Runs `terraform init` and `terraform destroy -auto-approve` to remove all resources managed by the configuration for that environment.

 

# How It Works

The core logic resides in the `lambda_function.py` file. The function performs the following steps:

1.  Receives S3 Event : It is triggered when a file is uploaded to the S3 bucket.
2.  Reads File Content : It fetches the uploaded file from S3 and decodes it as text.
3.  Calls Bedrock : It constructs a detailed prompt and sends the text to the Bedrock API to get a JSON object containing the analysis. The prompt specifically instructs the model to return *only* a valid JSON object.
4.  Parses Response : A regular expression is used to safely extract the JSON object from the model's response, making the parsing process resilient to extraneous text.
5.  Stores Data : The results are converted to the appropriate format (e.g., using `Decimal` for scores) and stored in DynamoDB.
6.  Handles Alerts : It checks the urgency and sentiment from the analysis to decide whether to send an SNS alert or publish a CloudWatch metric.

 

# Infrastructure as Code (IaC)

The project's AWS resources are defined in `main.tf`.

Key Resources:

  * [cite\_start] `aws_s3_bucket`: A private S3 bucket [cite: 15, 16] to receive feedback files.
  * [cite\_start] `aws_dynamodb_table`: A DynamoDB table with on-demand billing to store analysis results[cite: 17].
  * [cite\_start]`aws_lambda_function` : The serverless function that orchestrates the analysis process[cite: 23, 24].
  * [cite\_start] `aws_iam_role` : A dedicated IAM role for the Lambda function with precisely scoped permissions [cite: 18, 19, 20, 21, 22] to access S3, DynamoDB, Bedrock, SNS, and CloudWatch.
  *  `aws_sns_topic` : An SNS topic for sending out email alerts.
  *  `aws_cloudwatch_metric_alarm` : An alarm that monitors the custom "NegativeSentimentCount" metric.

#  Terraform Variables

The infrastructure is made configurable through variables defined in `variables.tf`.

| Variable Name            | Type         | Description                                                                              | Default Value                |
| ------------------------ | ------------ | ---------------------------------------------------------------------------------------- | ---------------------------- |
| `alert_email_endpoint`   | `string`     | [cite\_start]The email address to send high-urgency SNS alerts to. [cite: 1, 2]                            | [cite\_start]`yisakmesifin@gmail.com` [cite: 3] |
| `alarm_threshold`        | `number`     | [cite\_start]The number of negative sentiment events needed to trigger the CloudWatch alarm. [cite: 4] | `10`                         |
| `log_retention_days`     | `number`     | [cite\_start]Number of days to keep Lambda logs. [cite: 5]                                                | `30`                         |
| `environment_tags`       | `map(string)`| [cite\_start]A map of tags to apply to all resources for a specific environment. [cite: 6]              | `{}`                         |

#  Environment Configuration

Each environment has a dedicated `.tfvars` file to provide values for the variables, allowing for tailored configurations.

  *  Development (`dev.tfvars`) :
      * [cite\_start]`alarm_threshold`: Set to a low value of `2` for easy testing[cite: 10].
      * [cite\_start]`log_retention_days`: Set to `7` days to reduce cost[cite: 11].
      * [cite\_start]`environment_tags`: Tags resources with `Environment = "Development"`[cite: 12].
  *  Staging (`staging.tfvars`) :
      * `alarm_threshold`: `5`
      * `log_retention_days`: `14`
      * `environment_tags`: `Environment = "Staging"`
  *  Production (`prod.tfvars`) :
      * [cite\_start]`alarm_threshold`: `10` [cite: 7]
      * [cite\_start]`log_retention_days`: `30` [cite: 7]
      * [cite\_start]`environment_tags`: `Environment = "Production"` [cite: 7]

 

# Getting Started

#  Prerequisites

1.  An AWS Account.
2.  A GitHub repository with GitHub Actions enabled.
3.  Terraform installed locally (for any manual operations).
4.  AWS credentials (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_KEY`) configured as secrets in the GitHub repository.

#  Deployment

1.  Clone the Repository :

    ```sh
    git clone <your-repository-url>
    cd <repository-name>
    ```

2.  Configure Terraform Backend :
    [cite\_start]In `terraform/main.tf`, update the S3 backend configuration with your own bucket name to store the Terraform state file remotely[cite: 14].

    ```hcl
    terraform {
      backend "s3" {
        bucket = "your-unique-terraform-state-bucket-name"
        key    = "sentiment-detective/terraform.tfstate"
        region = "us-east-1"
      }
    }
    ```

3.  Configure Variables :
    [cite\_start]Update the email endpoint in `dev.tfvars` [cite: 9][cite\_start], `staging.tfvars` [cite: 13][cite\_start], and `prod.tfvars` [cite: 7] to your desired email address.

4.  Push to a Branch :

      * Pushing to the `develop` branch will deploy the development environment.
      * Pushing to `main` will deploy the production environment.
      * Monitor the deployment progress in the "Actions" tab of your GitHub repository.

Once the deployment is complete, you can find the name of the S3 bucket in the Terraform output of the GitHub Actions run. Upload a `.txt` file to that bucket to test the pipeline.