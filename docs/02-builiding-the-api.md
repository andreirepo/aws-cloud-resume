## Chunk 2: Building the API
#### 0. Set the region and profile variables before running commands. I used PowerShell, but feel free to modify the commands as needed. 
```shell
$Env:REGION = <aws-region>
$Env:SSO_PROFILE = <your-sso-profile>
```
#### 1. Create a YAML file that will create a simple table inside DynamoDB 
```shell
echo 'AWSTemplateFormatVersion: "2010-09-09"
Resources: 
  CloudResumeCounterDynamodb: 
    Type: AWS::DynamoDB::Table
    Properties: 
      AttributeDefinitions: 
        - 
          AttributeName: "Site"
          AttributeType: "N"
      KeySchema: 
        - 
          AttributeName: "Site"
          KeyType: "HASH"
      ProvisionedThroughput: 
        ReadCapacityUnits: "1"
        WriteCapacityUnits: "1"
      TableName: "cloudresumecounter"' > dynamodb-table.yml
```
#### 2. Deploy a DynamoDB table with CloudFormation
```shell
aws cloudformation deploy --template-file dynamodb-table.yml --stack-name cloudresumecounter --profile $Env:SSO_PROFILE
```

#### 3. Create a single attribute to hold the visitor count
```shell
aws dynamodb put-item --table-name cloudresumecounter --item '{"Site":{"N":"0"}, "Visits": {"N": "0"}}' --profile $Env:SSO_PROFILE
```
#### 4. Create a REST API and store its ID in an environmental variable
```shell
$Env:APIID = aws apigateway create-rest-api --name "ResumeAPI" --description "Cloud Resume API Gateway" --region $Env:REGION --query 'id' --output json --profile $Env:SSO_PROFILE | ConvertFrom-Json
```

#### 5. Get the parent resource ID and store it in an environmental variable
```shell
$Env:PARENTID = aws apigateway get-resources --rest-api-id $Env:APIID --region $Env:REGION --query 'items[0].id' --output json --profile $Env:SSO_PROFILE | ConvertFrom-Json
```

#### 6. Create a resource and store its ID in an environmental variable
```shell
$Env:RESOURCEID = aws apigateway create-resource --rest-api-id $Env:APIID --parent-id $Env:PARENTID --path-part visits --region $Env:REGION --query 'id' --output json --profile $Env:SSO_PROFILE | ConvertFrom-Json
```

#### 7. Create an HTTP GET Method
```shell
aws apigateway put-method --rest-api-id $Env:APIID --resource-id $Env:RESOURCEID --http-method GET --authorization-type "NONE" --region $Env:REGION --profile $Env:SSO_PROFILE
```

#### 8. Create an HTTP POST Method
```shell
aws apigateway put-method --rest-api-id $Env:APIID --resource-id $Env:RESOURCEID --http-method POST --authorization-type "NONE" --region $Env:REGION --profile $Env:SSO_PROFILE
```

#### 9. Create an IAM policy for the lambda function to access DynamoDB
```shell
echo '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:UpdateItem",
                "dynamodb:GetItem"
            ],
            "Resource": "arn:aws:dynamodb:REGION:ACCOUNT_ID:table/YOUR_TABLE_NAME"
        }
    ]
}' > lambda-iam-policy.json
```

#### 10. Create an IAM policy for the lambda function to access DynamoDB
```shell
aws iam create-role --role-name LambdaDynamoDBGetUpdate --assume-role-policy-document file://lambda-iam-policy.json
```

#### 11. Compress the lambda function
```shell
Compress-Archive -Path lambda_function.py -DestinationPath function.zip  
```

#### 12. Create the lambda function 
```shell
aws lambda create-function --function-name CloudResumeVisitCounter `
    --zip-file fileb://function.zip --handler lambda_function.lambda_handler `
    --runtime python3.8 --role arn:aws:iam::123456789012:role/YourLambdaExecutionRole `
    --profile $Env:SSO_PROFILE
```