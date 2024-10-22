## Chunk 2

##### 1. Create yaml file that will create a simple table inside DynamoDB 
```
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
##### 2. Deploy a DynamoDB table with CloudFormation
`aws cloudformation deploy --template-file dynamodb-table.yml --stack-name cloudresumecounter --profile <your-sso-profile>` 

##### 3. Create a single attribute to hold the visitor count
`aws dynamodb put-item --table-name cloudresumecounter --item '{"Site":{"N":"0"}, "Visits": {"N": "0"}}' --profile <your-sso-profile>`

##### 4. Create the REST API 
`aws apigateway create-rest-api --name "VisitorCountAPI" --description "Visitor count API" --region <region> --profile <your-sso-profile> > api-details.json`