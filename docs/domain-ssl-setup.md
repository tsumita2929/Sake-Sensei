# Domain and SSL Certificate Setup Guide

This guide covers setting up a custom domain with SSL/TLS certificate for SakeSensei production environment.

## Prerequisites

- AWS account with Route 53 access
- Registered domain name (or ability to register one)
- Access to AWS Certificate Manager (ACM)
- Deployed ECS service with Application Load Balancer

## Step 1: Register or Transfer Domain

### Option A: Register New Domain with Route 53

```bash
# List available domains
aws route53domains check-domain-availability \
  --domain-name sakesensei.com \
  --region us-east-1

# Register domain (interactive)
aws route53domains register-domain \
  --domain-name sakesensei.com \
  --duration-in-years 1 \
  --admin-contact file://contact.json \
  --registrant-contact file://contact.json \
  --tech-contact file://contact.json \
  --privacy-protect-admin-contact \
  --privacy-protect-registrant-contact \
  --privacy-protect-tech-contact \
  --region us-east-1
```

### Option B: Transfer Existing Domain

Follow AWS Route 53 domain transfer process in the console.

## Step 2: Create Hosted Zone

Route 53 hosted zone manages DNS records for your domain.

```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name sakesensei.com \
  --caller-reference "$(date +%s)" \
  --hosted-zone-config Comment="SakeSensei production domain"

# Get name servers
aws route53 get-hosted-zone \
  --id /hostedzone/HOSTED_ZONE_ID \
  --query "DelegationSet.NameServers"
```

**Action Required:** Update your domain registrar's name servers to the Route 53 name servers.

## Step 3: Request SSL/TLS Certificate

Use AWS Certificate Manager (ACM) to provision a free SSL certificate.

### Request Certificate

```bash
# Request certificate for domain and www subdomain
aws acm request-certificate \
  --domain-name sakesensei.com \
  --subject-alternative-names www.sakesensei.com \
  --validation-method DNS \
  --region us-west-2 \
  --tags Key=Environment,Value=production Key=Project,Value=SakeSensei
```

### DNS Validation

1. Get certificate details:

```bash
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-west-2:ACCOUNT_ID:certificate/CERTIFICATE_ID \
  --region us-west-2
```

2. Add CNAME records to Route 53 for validation:

```bash
# ACM will provide CNAME name and value
# Add these to your hosted zone
aws route53 change-resource-record-sets \
  --hosted-zone-id HOSTED_ZONE_ID \
  --change-batch file://dns-validation.json
```

Example `dns-validation.json`:

```json
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "_xxx.sakesensei.com",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{
        "Value": "_yyy.acm-validations.aws."
      }]
    }
  }]
}
```

3. Wait for validation (usually 5-30 minutes):

```bash
aws acm wait certificate-validated \
  --certificate-arn arn:aws:acm:us-west-2:ACCOUNT_ID:certificate/CERTIFICATE_ID \
  --region us-west-2
```

## Step 4: Configure ALB with SSL Certificate

### Option A: Update via Copilot

Edit `copilot/environments/prod/manifest.yml`:

```yaml
http:
  public:
    certificates:
      - arn:aws:acm:us-west-2:ACCOUNT_ID:certificate/CERTIFICATE_ID
```

Then deploy:

```bash
copilot env deploy --name prod
```

### Option B: Update via AWS Console/CLI

```bash
# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names sakesensei-prod-PublicLoadBalancer \
  --query "LoadBalancers[0].LoadBalancerArn" \
  --output text \
  --region us-west-2)

# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-west-2:ACCOUNT_ID:certificate/CERTIFICATE_ID \
  --default-actions Type=forward,TargetGroupArn=TARGET_GROUP_ARN \
  --region us-west-2
```

## Step 5: Create DNS Records

Point your domain to the Application Load Balancer.

### Get ALB DNS Name

```bash
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names sakesensei-prod-PublicLoadBalancer \
  --query "LoadBalancers[0].DNSName" \
  --output text \
  --region us-west-2)

echo "ALB DNS: $ALB_DNS"
```

### Create A Record (Alias)

```bash
# Create alias record for root domain
aws route53 change-resource-record-sets \
  --hosted-zone-id HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "sakesensei.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "ALB_HOSTED_ZONE_ID",
          "DNSName": "'"$ALB_DNS"'",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'

# Create alias record for www subdomain
aws route53 change-resource-record-sets \
  --hosted-zone-id HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.sakesensei.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "ALB_HOSTED_ZONE_ID",
          "DNSName": "'"$ALB_DNS"'",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

**Note:** ALB_HOSTED_ZONE_ID for us-west-2 is `Z1H1FL5HABSF5`

## Step 6: Configure HTTP to HTTPS Redirect

Redirect all HTTP traffic to HTTPS.

```bash
# Modify HTTP listener to redirect to HTTPS
aws elbv2 modify-listener \
  --listener-arn HTTP_LISTENER_ARN \
  --default-actions Type=redirect,RedirectConfig='{
    "Protocol":"HTTPS",
    "Port":"443",
    "StatusCode":"HTTP_301"
  }' \
  --region us-west-2
```

## Step 7: Verification

### Test DNS Resolution

```bash
# Check DNS propagation
dig sakesensei.com
dig www.sakesensei.com

# Test with specific name server
dig @8.8.8.8 sakesensei.com
```

### Test HTTPS Access

```bash
# Test HTTPS (should succeed)
curl -I https://sakesensei.com

# Test HTTP (should redirect to HTTPS)
curl -I http://sakesensei.com

# Test SSL certificate
openssl s_client -connect sakesensei.com:443 -servername sakesensei.com
```

### Browser Testing

1. Visit `https://sakesensei.com`
2. Check for:
   - ✅ Green padlock in browser
   - ✅ Valid certificate
   - ✅ No mixed content warnings
   - ✅ HTTP redirects to HTTPS

## Step 8: Update Application Configuration

Update environment variables and configuration to use the new domain:

```bash
# Update SSM parameters
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/DOMAIN_NAME" \
  --type "String" \
  --value "sakesensei.com" \
  --overwrite \
  --region us-west-2

aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/APP_URL" \
  --type "String" \
  --value "https://sakesensei.com" \
  --overwrite \
  --region us-west-2
```

## Additional Configuration

### Enable HTTP Strict Transport Security (HSTS)

Add security headers to ALB:

```yaml
# In copilot/streamlit-app/manifest.yml
http:
  additional_rules:
    - path: "*"
      healthcheck: "/_stcore/health"
      target_container: "streamlit-app"
      headers:
        - "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload"
        - "X-Content-Type-Options: nosniff"
        - "X-Frame-Options: DENY"
        - "X-XSS-Protection: 1; mode=block"
```

### Set up CloudFront (Optional)

For global distribution with caching:

```bash
# Create CloudFront distribution pointing to ALB
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json
```

### Configure WAF (Already done in Phase 10)

Associate the WAF Web ACL with the ALB (see security_stack.py).

## Monitoring

### Set up Route 53 Health Checks

```bash
aws route53 create-health-check \
  --health-check-config \
    Type=HTTPS,\
    ResourcePath=/_stcore/health,\
    FullyQualifiedDomainName=sakesensei.com,\
    Port=443,\
    RequestInterval=30,\
    FailureThreshold=3 \
  --caller-reference "$(date +%s)"
```

### CloudWatch Alarms

Create alarms for:
- Certificate expiration (ACM sends notifications automatically)
- Health check failures
- High 4XX/5XX error rates

## Troubleshooting

### Certificate Not Validating

- Check CNAME records are correctly added to Route 53
- Ensure name servers are updated at registrar
- Wait up to 30 minutes for propagation

### Domain Not Resolving

- Verify A records point to correct ALB
- Check ALB is in "active" state
- Confirm security groups allow inbound 443

### SSL Errors

- Verify certificate covers domain and www subdomain
- Check certificate is in "Issued" status
- Ensure certificate is in the same region as ALB (us-west-2)

## Cost Considerations

- **Route 53 Hosted Zone:** $0.50/month
- **DNS Queries:** $0.40 per million queries
- **ACM Certificates:** FREE
- **Domain Registration:** Varies by TLD (~$12-50/year)

## Security Best Practices

1. Enable DNSSEC for Route 53 hosted zone
2. Use CAA records to restrict certificate issuance
3. Monitor certificate expiration (though ACM auto-renews)
4. Regularly rotate any API keys or credentials
5. Use AWS Shield Standard (free) for DDoS protection

## References

- [Route 53 Documentation](https://docs.aws.amazon.com/route53/)
- [ACM Documentation](https://docs.aws.amazon.com/acm/)
- [Copilot Custom Domains](https://aws.github.io/copilot-cli/docs/developing/domain/)
