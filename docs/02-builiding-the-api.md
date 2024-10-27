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