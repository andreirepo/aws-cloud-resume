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
#### 1. Logging with SSO profile
```shell
aws login sso --profile $env:SSO_PROFILE
```
#### 2. Create a bucket
```shell
aws s3 mb s3://$env:BUCKET_NAME --profile $env:SSO_PROFILE
```
#### 3. Copy HTML and CSS to the bucket
```shell
aws s3 cp <project-dir> s3://$env:BUCKET_NAME --recursive --profile $env:SSO_PROFILE
```
#### 4. Verify that the bucket was created
```shell
aws s3 ls --profile $env:SSO_PROFILE | Where-Object { $_ -match "$env:BUCKET_NAME" }
```
#### 5. Check the contents of the bucket
```shell
aws s3 ls s3://$env:BUCKET_NAME/ --profile $env:SSO_PROFILE
```
#### 6. Disable all "Block all public access" bucket settings 
```shell
aws s3api put-public-access-block --bucket $env:BUCKET_NAME --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" --profile $env:SSO_PROFILE
```
#### 7. Verify "Block all public access" bucket settings
```shell
aws s3api get-public-access-block --bucket $env:BUCKET_NAME --profile $env:SSO_PROFILE
```
#### 8. Create bucket policy JSON  
```shell
echo '{
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
}' > bucket-policy.com
```
#### 9. Set the bucket policy
```shell
aws s3api put-bucket-policy --bucket $env:BUCKET_NAME --policy file://bucket-policy.json --profile $env:SSO_PROFILE
```
#### 10. Verify that static page is accessible
```shell
$response = Invoke-WebRequest -Uri "http://$env:BUCKET_NAME.s3-website.$env:REGION.amazonaws.com" -UseBasicParsing
$response.StatusCode
```
#### 11. Request ACM certificate for your domain. Note down the CertificateArn after making the request
```shell
aws acm request-certificate \
    --domain-name <your-domain-name> \
    --validation-method DNS \
    --subject-alternative-names <optional-alternative-names> \
    --region $env:REGION
    --profile $env:SSO_PROFILE
```
#### 12. Verify the certificate status and save the output to text file. We will need the ResourceRecord Name and Value to configure it on the DNS side
```shell
aws acm describe-certificate \
    --certificate-arn <certificate-arn> \
    --region $env:REGION
    --profile $env:SSO_PROFILE
    > certificate.txt
```
#### 13. On CloudFlare, navigate to DNS page and add new CNAME record where NAME is ResourceRecord Name and TARGET is ResourceRecord Value. Turn of proxying, it should say "DNS only"

#### 14. Check the ACM certificate status again after a few minutes, validation status should change to "SUCCSESS"

#### 15. Create CloudFront distribution
```
> cloudfront-config.json
```

#### 16. Verify CloudFront distribution domain is accessible

#### 17. On CloudFlare, navigate to DNS page and add new CNAME record where NAME is @ (root) and TARGET is your CloudFront distribution domain