# Sake Sensei API Reference

This document provides technical reference for Sake Sensei's backend APIs.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Authentication](#authentication)
3. [Lambda Functions](#lambda-functions)
4. [AgentCore Integration](#agentcore-integration)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)

## Architecture Overview

Sake Sensei uses a serverless architecture with the following components:

- **Frontend:** Streamlit application on ECS Fargate
- **Authentication:** AWS Cognito
- **Backend:** AWS Lambda functions
- **Database:** Amazon DynamoDB
- **Storage:** Amazon S3
- **AI Agent:** Amazon Bedrock AgentCore with Claude 4.5 Sonnet
- **Image Recognition:** Amazon Bedrock (Claude 4.5 Sonnet)

## Authentication

All API requests require authentication via AWS Cognito.

### Authentication Flow

1. User signs up/signs in via Streamlit UI
2. Cognito issues JWT tokens (ID token, Access token, Refresh token)
3. Tokens are included in requests to Lambda functions
4. Lambda functions validate tokens before processing

### Token Structure

**ID Token Claims:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "email_verified": true,
  "cognito:username": "username",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### API Authentication

Include the ID token in request headers:

```http
Authorization: Bearer <ID_TOKEN>
```

## Lambda Functions

All Lambda functions follow a common structure:

- **Runtime:** Python 3.13
- **Invocation:** Synchronous (RequestResponse)
- **Response Format:** JSON with statusCode and body
- **Error Handling:** Standardized error responses
- **Logging:** CloudWatch Logs with structured logging
- **Tracing:** X-Ray enabled

### Common Response Format

**Success Response:**
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"data\": {...}, \"message\": \"Success\"}"
}
```

**Error Response:**
```json
{
  "statusCode": 400,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"error\": \"Error description\", \"code\": \"ERROR_CODE\"}"
}
```

### 1. Recommendation Lambda

**Function Name:** `SakeSensei-Recommendation`

**Purpose:** Generate personalized sake recommendations based on user preferences and history.

**Invocation:**

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-west-2')

response = lambda_client.invoke(
    FunctionName='SakeSensei-Recommendation',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'user_id': 'user-123',
        'preferences': {
            'sweetness': 3,
            'acidity': 4,
            'richness': 2,
            'aroma_intensity': 4
        },
        'limit': 10
    })
)
```

**Request Payload:**

```json
{
  "user_id": "string (required)",
  "preferences": {
    "sweetness": "integer 1-5",
    "acidity": "integer 1-5",
    "richness": "integer 1-5",
    "aroma_intensity": "integer 1-5"
  },
  "sake_types": ["string array (optional)"],
  "exclude_tried": "boolean (optional, default: false)",
  "limit": "integer (optional, default: 10)"
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "recommendations": [
      {
        "sake_id": "sake-001",
        "name": "獺祭 純米大吟醸 磨き二割三分",
        "brewery_id": "brewery-001",
        "brewery_name": "旭酒造",
        "type": "純米大吟醸",
        "score": 0.95,
        "match_reasons": ["Matches your preference for aromatic sake", "..."],
        "characteristics": {
          "sweetness": 2,
          "acidity": 1.4,
          "richness": 2,
          "aroma_intensity": 5
        }
      }
    ],
    "count": 10
  }
}
```

### 2. Preference Lambda

**Function Name:** `SakeSensei-Preference`

**Purpose:** Manage user preference settings.

**Operations:**

#### GET Preferences

```json
{
  "httpMethod": "GET",
  "pathParameters": {
    "user_id": "user-123"
  }
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "user_id": "user-123",
    "preferences": {
      "sweetness": 3,
      "acidity": 4,
      "richness": 2,
      "aroma_intensity": 4
    },
    "sake_types": ["純米酒", "純米吟醸"],
    "contexts": ["食事中", "晩酌"],
    "food_pairings": ["魚", "野菜"],
    "updated_at": "2025-10-01T10:00:00Z"
  }
}
```

#### PUT/Update Preferences

```json
{
  "httpMethod": "PUT",
  "pathParameters": {
    "user_id": "user-123"
  },
  "body": {
    "preferences": {
      "sweetness": 4,
      "acidity": 3,
      "richness": 3,
      "aroma_intensity": 5
    },
    "sake_types": ["純米大吟醸"],
    "contexts": ["celebrations"],
    "food_pairings": ["sushi", "sashimi"]
  }
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "message": "Preferences updated successfully",
    "user_id": "user-123"
  }
}
```

### 3. Tasting Lambda

**Function Name:** `SakeSensei-Tasting`

**Purpose:** Manage tasting records (CRUD operations).

#### Create Tasting Record

```json
{
  "httpMethod": "POST",
  "body": {
    "action": "create",
    "tasting_data": {
      "user_id": "user-123",
      "sake_id": "sake-001",
      "overall_rating": 5,
      "aroma_rating": 5,
      "taste_rating": 4,
      "sweetness": 2,
      "acidity": 3,
      "body": 3,
      "finish": 4,
      "aroma_notes": ["fruity", "floral"],
      "taste_notes": ["clean", "balanced"],
      "comments": "Excellent sake!",
      "location": "Izakaya in Tokyo",
      "temperature": "cold",
      "pairing": "sashimi",
      "tasting_date": "2025-10-01"
    }
  }
}
```

**Response:**

```json
{
  "statusCode": 201,
  "body": {
    "record_id": "record-xyz",
    "message": "Tasting record created successfully"
  }
}
```

#### List Tasting Records

```json
{
  "httpMethod": "GET",
  "queryStringParameters": {
    "user_id": "user-123",
    "action": "list",
    "limit": "50"
  }
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "records": [
      {
        "record_id": "record-xyz",
        "user_id": "user-123",
        "sake_id": "sake-001",
        "sake_name": "獺祭 純米大吟醸 磨き二割三分",
        "overall_rating": 5,
        "tasting_date": "2025-10-01",
        "created_at": "2025-10-01T10:00:00Z"
      }
    ],
    "count": 1
  }
}
```

#### Get Statistics

```json
{
  "httpMethod": "GET",
  "queryStringParameters": {
    "user_id": "user-123",
    "action": "statistics"
  }
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "total_records": 42,
    "monthly_records": 5,
    "favorites_count": 12,
    "breweries_explored": 15,
    "average_rating": 4.2,
    "top_sake_types": ["純米大吟醸", "純米吟醸"],
    "recent_tastings": 5
  }
}
```

### 4. Brewery Lambda

**Function Name:** `SakeSensei-Brewery`

**Purpose:** Retrieve brewery information and sake listings.

#### Get Brewery Info

```json
{
  "pathParameters": {
    "brewery_id": "brewery-001"
  }
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "brewery_id": "brewery-001",
    "name": "旭酒造",
    "region": "山口県",
    "founded": 1948,
    "description": "Famous for Dassai brand...",
    "sake_count": 5,
    "website": "https://www.asahishuzo.ne.jp"
  }
}
```

#### List Brewery Sake

```json
{
  "queryStringParameters": {
    "brewery_id": "brewery-001",
    "action": "list_sake"
  }
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "brewery_id": "brewery-001",
    "brewery_name": "旭酒造",
    "sake_list": [
      {
        "sake_id": "sake-001",
        "name": "獺祭 純米大吟醸 磨き二割三分",
        "type": "純米大吟醸",
        "rice_polishing": 23
      }
    ],
    "count": 5
  }
}
```

### 5. Image Recognition Lambda

**Function Name:** `SakeSensei-ImageRecognition`

**Purpose:** Recognize sake labels using Claude 4.5 Sonnet vision model.

**Request:**

```json
{
  "image_data": "base64-encoded-image-string",
  "image_format": "jpeg|png",
  "user_id": "user-123"
}
```

**Response:**

```json
{
  "statusCode": 200,
  "body": {
    "recognized": true,
    "sake_name": "獺祭 純米大吟醸 磨き二割三分",
    "brewery_name": "旭酒造",
    "sake_type": "純米大吟醸",
    "confidence": 0.95,
    "additional_info": {
      "rice_polishing": "23%",
      "alcohol_content": "16%"
    },
    "matched_sake_id": "sake-001",
    "processing_time_ms": 1250
  }
}
```

## AgentCore Integration

### Agent Configuration

**Agent Name:** SakeSensei Agent
**Model:** Claude 4.5 Sonnet (anthropic.claude-sonnet-4-5-v2:0)
**Gateway:** `sakesensei-gateway-98idnabr4g`
**Memory Store:** `SakeSensei_Memory-mzOUnk3vAZ`

### MCP Tools

The agent has access to Lambda functions via AgentCore Gateway as MCP tools:

1. **get_recommendations** → Recommendation Lambda
2. **get_user_preferences** → Preference Lambda
3. **save_tasting_record** → Tasting Lambda
4. **get_brewery_info** → Brewery Lambda
5. **recognize_sake_label** → Image Recognition Lambda

### Agent Invocation

```python
import boto3
import json

agentcore = boto3.client('bedrock-agent-runtime', region_name='us-west-2')

response = agentcore.invoke_agent(
    agentId='agent-id',
    sessionId='session-123',
    inputText='Recommend a sake for dinner with sushi'
)

# Stream response
for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode())
```

### Streaming Response

The agent supports streaming responses for real-time interaction:

```python
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']['bytes'].decode()
        # Process chunk
    elif 'trace' in event:
        # Process trace information (tool calls, reasoning)
        trace = event['trace']
```

## Data Models

### Sake Model

```python
{
  "sake_id": "string (PK)",
  "name": "string",
  "name_en": "string (optional)",
  "brewery_id": "string (FK)",
  "type": "string (純米酒|純米吟醸|純米大吟醸|本醸造|吟醸|大吟醸)",
  "rice_type": "string",
  "rice_polishing": "integer (percentage)",
  "alcohol_content": "float",
  "sweetness": "integer (1-5)",
  "acidity": "float (1.0-2.0)",
  "richness": "integer (1-5)",
  "aroma_intensity": "integer (1-5)",
  "price_range": "integer (1-5)",
  "description": "string",
  "flavor_notes": ["string array"],
  "food_pairings": ["string array"],
  "serving_temp": "string (cold|cool|room|warm|hot)",
  "availability": "string"
}
```

### User Model

```python
{
  "user_id": "string (PK)",
  "email": "string",
  "username": "string",
  "preferences": {
    "sweetness": "integer (1-5)",
    "acidity": "integer (1-5)",
    "richness": "integer (1-5)",
    "aroma_intensity": "integer (1-5)"
  },
  "sake_types": ["string array"],
  "contexts": ["string array"],
  "food_pairings": ["string array"],
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

### Tasting Record Model

```python
{
  "record_id": "string (PK)",
  "user_id": "string (SK)",
  "sake_id": "string",
  "overall_rating": "integer (1-5)",
  "aroma_rating": "integer (1-5)",
  "taste_rating": "integer (1-5)",
  "sweetness": "integer (1-5)",
  "acidity": "integer (1-5)",
  "body": "integer (1-5)",
  "finish": "integer (1-5)",
  "aroma_notes": ["string array"],
  "taste_notes": ["string array"],
  "comments": "string",
  "location": "string",
  "temperature": "string",
  "pairing": "string",
  "photos": ["string array (S3 URLs)"],
  "favorite": "boolean",
  "tasting_date": "date",
  "created_at": "ISO 8601 timestamp"
}
```

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_INPUT` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication failed |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMIT` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Format

```json
{
  "statusCode": 400,
  "body": {
    "error": "Validation failed",
    "code": "INVALID_INPUT",
    "details": {
      "field": "sweetness",
      "message": "Value must be between 1 and 5"
    },
    "request_id": "req-xyz"
  }
}
```

### Retry Logic

Implement exponential backoff for transient errors:

```python
import time

def invoke_with_retry(lambda_client, function_name, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=payload
            )
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

## Rate Limits

- **Per User:** 100 requests per 5 minutes
- **Per IP:** 1000 requests per hour
- **Image Recognition:** 20 requests per minute

Rate limit headers in response:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
```

## Monitoring & Logging

### CloudWatch Metrics

- Lambda invocation count
- Error rate
- Duration (P50, P99)
- Throttles

### X-Ray Tracing

All Lambda functions have X-Ray tracing enabled. View traces in AWS X-Ray console:

- Request flow visualization
- Latency breakdown
- Error analysis

### Logging

Logs are available in CloudWatch Logs:

```
/aws/lambda/SakeSensei-Recommendation
/aws/lambda/SakeSensei-Preference
/aws/lambda/SakeSensei-Tasting
/aws/lambda/SakeSensei-Brewery
/aws/lambda/SakeSensei-ImageRecognition
```

## SDK Examples

### Python (Boto3)

```python
import boto3
import json

# Initialize clients
lambda_client = boto3.client('lambda', region_name='us-west-2')
agentcore_client = boto3.client('bedrock-agent-runtime', region_name='us-west-2')

# Get recommendations
response = lambda_client.invoke(
    FunctionName='SakeSensei-Recommendation',
    InvocationType='RequestResponse',
    Payload=json.dumps({'user_id': 'user-123', 'limit': 10})
)

result = json.loads(response['Payload'].read())
print(result)
```

### JavaScript (AWS SDK v3)

```javascript
import { LambdaClient, InvokeCommand } from "@aws-sdk/client-lambda";

const client = new LambdaClient({ region: "us-west-2" });

const command = new InvokeCommand({
  FunctionName: "SakeSensei-Recommendation",
  Payload: JSON.stringify({
    user_id: "user-123",
    limit: 10
  })
});

const response = await client.send(command);
const result = JSON.parse(new TextDecoder().decode(response.Payload));
console.log(result);
```

## Versioning

API Version: `v1`

Breaking changes will result in a new version (v2). Non-breaking changes are deployed to existing version.

## Support

For API questions or issues:

- **Email:** api-support@sakesensei.com
- **Documentation:** https://docs.sakesensei.com
- **Status Page:** https://status.sakesensei.com

---

Last Updated: 2025-10-01
