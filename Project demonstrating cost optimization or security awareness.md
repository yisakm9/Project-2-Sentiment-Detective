
# 💰 Cost Optimization

The project demonstrates cost optimization through a few key practices, mainly by using different settings for each environment. 

* [cite_start] Log Retention:  The project configures different CloudWatch log retention periods for each environment[cite: 4, 24]. [cite_start]The dev  environment keeps logs for only 7 days to save costs, while  staging  and production  have longer retention periods of 14 and 30 days, respectively[cite: 4, 26, 27]. [cite_start]This ensures that while logs are available for troubleshooting in the production environment, the cost of storing them is reduced in less critical environments[cite: 4, 24, 26, 27]. 

* [cite_start] DynamoDB Billing Mode: The DynamoDB table is configured to use Pay-Per-Request billing mode[cite: 9]. [cite_start]This is a cost-effective choice for workloads with unpredictable or infrequent traffic, as you only pay for the reads and writes that your application actually performs, rather than for a pre-provisioned capacity[cite: 9]. 

* [cite_start] S3 Lifecycle Policy: The S3 bucket for customer feedback has a lifecycle rule that automatically expires objects after 30 days[cite: 6]. [cite_start]This helps prevent the long-term accumulation of data, thereby reducing storage costs[cite: 6]. 



#  🔒 Security Awareness

Security awareness is demonstrated through careful handling of credentials, least-privilege access, and restricted network access. 

* AWS Credentials Handling:  The GitHub Actions workflows use AWS credentials stored as encrypted  secrets  (`${{ secrets.AWS_ACCESS_KEY_ID }}` and `${{ secrets.AWS_SECRET_KEY }}`) instead of hardcoding them directly in the YAML files. This is a fundamental security best practice that prevents sensitive information from being exposed in plain text in the codebase. 
* [cite_start]**Principle of Least Privilege:  The AWS Lambda function's IAM role is granted only the specific permissions it needs to perform its job[cite: 11, 12, 13, 14, 15]. [cite_start]The custom IAM policy explicitly allows actions like `s3:GetObject` and `s3:ListBucket` on the feedback bucket, `dynamodb:PutItem` on the analysis results table, `bedrock:InvokeModel` for analysis, `cloudwatch:PutMetricData` for metrics, and `sns:Publish` for alerts[cite: 11, 12, 13, 14]. [cite_start]It doesn't have broad, unrestricted access to the entire AWS account[cite: 11, 12, 13, 14, 15]. 

* [cite_start]**S3 Public Access Block:  The S3 bucket is configured with a public access block[cite: 8]. [cite_start]This is a crucial security measure that prevents the bucket from being made public, ensuring that sensitive customer feedback data remains private and protected from unauthorized access[cite: 8]. 

* Secure Infrastructure Management:  The project uses GitHub Actions with Terraform to manage infrastructure. This approach ensures that infrastructure changes are automated, version-controlled, and subject to review, reducing the risk of human error or unauthorized, manual changes that could introduce security vulnerabilities. 

***

# 🚀 Conclusion

This project effectively balances operational needs with responsible cost management and robust security practices. [cite_start]By implementing variable log retention, optimizing DynamoDB billing, and using an S3 lifecycle policy, it minimizes unnecessary expenses without compromising functionality. [cite: 4, 9, 24] [cite_start]Simultaneously, it upholds a strong security posture by adhering to the principle of least privilege, protecting credentials, and blocking public access to data storage, making it a professional and well-architected solution. [cite: 8, 11, 12, 13, 14]