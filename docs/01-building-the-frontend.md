# Cloud Resume Challenge Solution 

## Prerequisites 

- AWS Organization configured
- CloudFlare domain registered
- Basic HTML & CSS template downloaded: https://css-tricks.com/examples/OnePageResume.zip

## Chunk 1: Building the frontend

#### 0. Set the region and profile variables before running commands. I used PowerShell, but feel free to modify the commands as needed. 
```shell
$env:REGION = "<aws-region>"
$env:SSO_PROFILE = "<your-sso-profile>"
$env:BUCKET_NAME = "<your-bucket-name>"
```
#### 1. Configure and logging with SSO profile
```shell
# Follow the steps to configure the profile
aws configure sso --profile $env:SSO_PROFILE

# Login to the profile
aws sso login --profile $env:SSO_PROFILE
```
#### 2. Create a bucket
```shell
aws s3 mb s3://$env:BUCKET_NAME --profile $env:SSO_PROFILE
```
#### 3. Copy HTML and CSS to the bucket and verify that the bucket was created
```shell
aws s3 cp <project-dir>\ s3://$env:BUCKET_NAME --recursive --profile $env:SSO_PROFILE # Create
aws s3 ls --profile $env:SSO_PROFILE | Where-Object { $_ -match "$env:BUCKET_NAME" } # Verify
aws s3 ls s3://$env:BUCKET_NAME/ --profile $env:SSO_PROFILE # Check the contents of the bucket
```
#### 4. Disable all "Block all public access" bucket settings 
```shell
# Disable all "Block all public access" bucket settings
aws s3api put-public-access-block --bucket $env:BUCKET_NAME --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" --profile $env:SSO_PROFILE 

# Verify that all "Block all public access" bucket settings are disabled
aws s3api get-public-access-block --bucket $env:BUCKET_NAME --profile $env:SSO_PROFILE
```
#### 5. Create bucket policy JSON and attach it to the bucket
```shell
# Generate the bucket policy JSON file
$policyContent = @" 
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$env:BUCKET_NAME/*"
        }
    ]
}
"@

# Write to file without BOM (Byte Order Mark)
[System.IO.File]::WriteAllText("$(Get-Location)\bucket-policy.json", $policyContent)

# Verify the content
Get-Content bucket-policy.json

# Attach the bucket policy to the bucket
aws s3api put-bucket-policy --bucket $env:BUCKET_NAME --policy file://bucket-policy.json --profile $env:SSO_PROFILE
```
#### 6. Enable static website hosting on the bucket
```shell    
aws s3 website s3://$env:BUCKET_NAME --index-document index.html --profile $env:SSO_PROFILE
```
#### 7. Verify that the static page is accessible
```shell
# Invoke-WebRequest returns a response object
$response = Invoke-WebRequest -Uri "http://$env:BUCKET_NAME.s3-website.$env:REGION.amazonaws.com" -UseBasicParsing 

# Should return 200
$response.StatusCode 
```
#### 8. Request ACM certificate for your domain. Note down the CertificateArn after making the request
```shell
aws acm request-certificate `
    --domain-name cloudresume.andreiqa.click `
    --validation-method DNS `
    --region $env:REGION `
    --profile $env:SSO_PROFILE
```
#### 9. Wait for certificate to be in "ISSUED" status. Make sure to wait for the validation to complete before proceeding.
```shell
aws acm describe-certificate `
    --certificate-arn <certificate-arn> `
    --region $env:REGION `
    --profile $env:SSO_PROFILE 
```
#### 10. Create CloudFront distribution configuration file
```shell
$cloudFrontConfig = @"
{
    "CallerReference": "$(Get-Date -Format "yyyyMMddHHmmss")",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-Website-$env:BUCKET_NAME.s3-website.$env:REGION.amazonaws.com",
                "DomainName": "$env:BUCKET_NAME.s3-website.$env:REGION.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only",
                    "OriginSslProtocols": {
                        "Quantity": 1,
                        "Items": ["TLSv1.2"]
                    },
                    "OriginReadTimeout": 30,
                    "OriginKeepaliveTimeout": 5
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-Website-$env:BUCKET_NAME.s3-website.$env:REGION.amazonaws.com",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "Compress": true,
        "DefaultTTL": 86400,
        "MinTTL": 0,
        "MaxTTL": 31536000,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            },
            "Headers": {
                "Quantity": 0
            },
            "QueryStringCacheKeys": {
                "Quantity": 0
            }
        }
    },
    "Comment": "CloudFront distribution for cloud resume",
    "Enabled": true,
    "Aliases": {
        "Quantity": 1,
        "Items": ["<your-dcomain.com>"]
    },
    "ViewerCertificate": {
        "ACMCertificateArn": <certificate-arn>,
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2019"
    }
}
"@

# Write the updated configuration to a file
[System.IO.File]::WriteAllText("$(Get-Location)\cloudfront-config.json", $cloudFrontConfig)
```
####  11. Create CloudFront distribution
```shell
aws cloudfront create-distribution `
    --distribution-config file://cloudfront-config.json `
    --profile $env:SSO_PROFILE

# Wait for CloudFront distribution to be deployed by checking the status
aws cloudfront list-distributions --query "DistributionList.Items[*].{Id:Id,DomainName:DomainName,Status:Status,Enabled:Enabled}" --output table --profile $env:SSO_PROFILE
```

#### 12. Create a DNS record that points your domain to the CloudFront distribution.
```shell
aws cloudfront list-distributions --query "DistributionList.Items[*].{Id:Id,DomainName:DomainName}" --output table --profile $env:SSO_PROFILE # get your CloudFront distribution domain name:

aws route53 list-hosted-zones --profile $env:SSO_PROFILE # Get your hosted zone ID first

# Create the CNAME record (replace YOUR_HOSTED_ZONE_ID and YOUR_CLOUDFRONT_DOMAIN)
$changeJson = @"
{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "cloudresume.andreiqa.click",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "YOUR_CLOUDFRONT_DOMAIN"
          }
        ]
      }
    }
  ]
}
"@

[System.IO.File]::WriteAllText("$(Get-Location)\dns-change.json", $changeJson)

aws route53 change-resource-record-sets --hosted-zone-id YOUR_HOSTED_ZONE_ID --change-batch file://dns-change.json --profile $env:SSO_PROFILE

```