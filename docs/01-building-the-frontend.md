# Cloud Resume Challenge Solution 

## Prerequisites 

- Organizations configured
- CloudFlare domain registered
- Basic HTML & CSS template downloaded: https://css-tricks.com/examples/OnePageResume.zip

## Chunk 1: Building the frontend

#### 0. Set the region and profile variables before running commands. I used PowerShell, but feel free to modify the commands as needed. 
```
$Env:REGION = <aws-region>
$Env:SSO_PROFILE = <your-sso-profile>
```

#### 1. Logging with SSO profile
`aws login sso --profile $Env:SSO_PROFILE`

#### 2. Create a bucket
`aws s3 mb s3://<bucket-name> --profile $Env:SSO_PROFILE` 

#### 3. Copy HTML and CSS to the bucket
`aws s3 cp <project_dir> s3://<bucket-name> --recursive --profile $Env:SSO_PROFILE` 

#### 4. List all the buckets in your account associated with that profile
`aws s3 ls --profile $Env:SSO_PROFILE`

#### 5. List all files in a bucket
`aws s3 ls s3://<bucket-name>/ --profile $Env:SSO_PROFILE` 

#### 6. Disable all settings in the "Block all public access" 
```
aws s3api put-public-access-block --bucket <bucket-name> --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" --profile $Env:SSO_PROFILE
```
#### 7. Verify "Block all public access" settings
`aws s3api get-public-access-block --bucket <bucket-name> --profile $Env:SSO_PROFILE`

#### 8. Create bucket policy json  
```
echo '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::<bucket-name>/*"
        }
    ]
}' > bucket-policy.com
```

#### 9. Set the bucket policy
`aws s3api put-bucket-policy --bucket <bucket-name> --policy file://bucket-policy.json --profile $Env:SSO_PROFILE`

#### 10. Verify that static page is accessible
`curl -o /dev/null -s -w "%{http_code}\n" http://<bucket-name>.s3-website.<bucket-region>.amazonaws.com`

#### 11. Request ACM certificate for your domain. Note down the CertificateArn after making the request
```
aws acm request-certificate \
    --domain-name <your-domain-name> \
    --validation-method DNS \
    --subject-alternative-names <optional-alternative-names> \
    --region $Env:REGION
    --profile $Env:SSO_PROFILE
```

#### 12. Verify the certificate status and save the output to text file. We will need the ResourceRecord Name and Value to configure it on the DNS side
```
aws acm describe-certificate \
    --certificate-arn <certificate-arn> \
    --region $Env:REGION
    --profile $Env:SSO_PROFILE
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