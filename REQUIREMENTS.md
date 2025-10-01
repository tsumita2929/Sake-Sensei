# Sake Sensei - Requirements Document

## Project Overview

Sake Sensei is an AI-powered sake recommendation system designed for beginners to find sake that matches their preferences. Built with Streamlit and AWS serverless architecture, it learns from user feedback to provide personalized recommendations.

## Technology Stack

- **Frontend**: Streamlit (Python 3.12) on ECS Fargate
- **Container Orchestration**: AWS Copilot CLI
- **Load Balancer**: Application Load Balancer (ALB)
- **Agentic Framework**: Strands Agents
- **Agent Infrastructure**: Amazon Bedrock AgentCore
  - **Runtime**: Serverless agent hosting and execution
  - **Gateway**: MCP-compatible tool interface for DynamoDB and Lambda functions
  - **Memory**: Managed conversation history and long-term user preference storage
  - **Identity**: OAuth 2.0 integration with AWS Cognito
  - **Observability**: OpenTelemetry-based tracing and monitoring
- **AI**: Amazon Bedrock (Claude Sonnet 4.5)
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Security**: AWS WAF, HTTPS

## User Stories and Acceptance Criteria

### Requirement 1: Preference Survey

**User Story**: As a sake beginner, I want to answer simple questions about my preferences so that I can receive personalized sake recommendations.

#### Acceptance Criteria

1. User can complete a preference survey including:
   - Sweet/dry preference (1-5 scale)
   - Budget (price range)
   - Experience level (beginner/intermediate/advanced)
   - Categories to avoid (optional)
2. Recommendations include basic sake information:
   - Name, brewery, price
   - Characteristics (flavor profile)
   - Where to purchase
3. Recommendation reasons are clearly explained

### Requirement 2: Rating and Feedback

**User Story**: As a user who has tried sake, I want to record my feedback so that future recommendations improve based on my tastes.

#### Acceptance Criteria

1. User can record tasting feedback:
   - 5-star rating
   - Optional notes
   - Tasting date
2. System learns from past ratings to improve recommendations
3. User can view their rating history

### Requirement 3: Brewery Information

**User Story**: As a curious user, I want to learn about the breweries behind recommended sake.

#### Acceptance Criteria

1. Each sake displays brewery information:
   - Brewery name
   - Location (prefecture)
   - Representative characteristics
2. Other major sake from the same brewery are shown

### Requirement 4: Food Pairing

**User Story**: As a sake drinker, I want to know which foods pair well with recommended sake.

#### Acceptance Criteria

1. Each recommended sake shows 3-5 food pairing suggestions
2. Pairings focus on home-cookable dishes
3. Explanations of why the pairing works

### Requirement 5: Image Recognition

**User Story**: As a shopper, I want to take a photo of a sake label in a store to learn about it and see if it matches my preferences.

#### Acceptance Criteria

1. User can upload a label image
2. System identifies the sake from the image
3. Identified sake shows:
   - Basic information
   - Compatibility score with user preferences
4. If identification fails, similar sake are suggested

### Requirement 6: Web Application with Streaming

**User Story**: As a user, I want to easily access the sake recommendation service through a web browser with real-time streaming responses.

#### Acceptance Criteria

1. Streamlit web application deployed on ECS Fargate
2. **Streaming Chat Interface**:
   - Responses appear in real-time (token-by-token)
   - First token appears within 500ms
   - Smooth streaming animation with cursor indicator
   - No page reload required for responses
3. Responsive design works on mobile devices
4. User registration and login functionality available
5. Secure authentication via AWS Cognito
6. **Progress Indicators**:
   - Loading spinner while waiting for first token
   - Typing animation during streaming
   - Clear indication when response is complete
7. **High Availability**: Auto-scaling with minimum 2 tasks across multiple AZs
8. **Load Balancing**: ALB distributes traffic evenly across tasks

### Requirement 7: Sake Database Management

**User Story**: As a system administrator, I want to maintain an accurate and up-to-date sake database.

#### Acceptance Criteria

1. Database stores sake master data:
   - Name, brewery, price
   - Category, characteristics
   - Description, image URL
2. Admin can add and update sake information
3. Data integrity checks are in place

### Requirement 8: Learning System

**User Story**: As a system operator, I want the system to learn from user preferences to improve recommendation accuracy.

#### Acceptance Criteria

1. User rating history is stored and used in recommendation algorithm
2. Recommendation accuracy can be measured and monitored
3. Algorithm can be adjusted based on user feedback

### Requirement 9: Security and Privacy

**User Story**: As a user, I want my personal information protected while using the service.

#### Acceptance Criteria

1. Authentication uses AWS Cognito
2. Personal data is encrypted (at rest and in transit)
3. HTTPS is enforced for all communications
4. Basic security measures implemented:
   - AWS WAF protection
   - Input validation
   - Rate limiting

## Data Models

### User Profile

```python
{
    "user_id": "string",
    "email": "string",
    "preferences": {
        "sweetness": int,  # 1-5 (1=dry, 5=sweet)
        "budget": int,     # Max price in yen
        "experience_level": "string",  # beginner/intermediate/advanced
        "avoid_categories": ["string"]
    },
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Sake Master Data

```python
{
    "sake_id": "string",
    "name": "string",
    "brewery_id": "string",
    "category": "string",  # 純米大吟醸, 純米吟醸, etc.
    "price": int,
    "alcohol_content": float,
    "characteristics": {
        "sweetness": int,  # 1-5
        "acidity": int,    # 1-5
        "body": int,       # 1-5 (light-heavy)
        "aroma": "string"  # フルーティー, etc.
    },
    "pairings": ["string"],
    "description": "string",
    "image_url": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Brewery Master Data

```python
{
    "brewery_id": "string",
    "name": "string",
    "prefecture": "string",
    "description": "string",
    "representative_sakes": ["string"],
    "created_at": "datetime"
}
```

### Tasting Record

```python
{
    "record_id": "string",
    "user_id": "string",
    "sake_id": "string",
    "rating": int,  # 1-5
    "notes": "string",
    "tasting_date": "datetime"
}
```

## AgentCore Architecture

### Runtime Agent Structure

The Sake Sensei agent runs on Amazon Bedrock AgentCore Runtime with **streaming support** for real-time responses:

1. **Recommendation Agent**
   - Framework: Strands Agent
   - Model: Anthropic Claude Sonnet 4.5 via Amazon Bedrock
   - Tools: MCP tools via AgentCore Gateway
   - Memory: AgentCore Memory for user preferences and conversation history
   - **Streaming**: Real-time token-by-token response delivery

2. **Streaming Entrypoint Function**
   ```python
   @app.entrypoint
   async def invoke(payload, context):
       """
       Streaming entrypoint for AgentCore Runtime
       Returns async generator for token-by-token streaming
       """
       user_message = payload["prompt"]
       session_id = context.session_id
       actor_id = payload["actor_id"]

       # Create agent with streaming support
       agent = SakeSenseiAgent(
           gateway_token=await get_gateway_token(),
           memory_hook=SakeSenseiMemoryHook(session_id, actor_id)
       )

       # Return streaming generator
       async def stream_output():
           async for chunk in agent.stream(user_message):
               yield chunk  # Token-by-token streaming

       return stream_output()
   ```

3. **Streaming Benefits**
   - **Improved UX**: Users see responses immediately
   - **Real-time Feel**: Natural conversation experience
   - **Progress Indication**: Visual feedback during processing
   - **Lower Perceived Latency**: TTFT < 500ms vs 3+ seconds for full response

### Gateway Tools (MCP Protocol)

AgentCore Gateway converts Lambda functions and DynamoDB operations into MCP-compatible tools:

#### Tool Targets

1. **Sake Recommendation Lambda**
   - `get_recommendations`: Generate personalized sake recommendations
   - `get_sake_details`: Retrieve detailed sake information
   - `search_sakes_by_characteristics`: Search by flavor profile

2. **User Preference Lambda**
   - `get_user_preferences`: Retrieve user preference settings
   - `update_user_preferences`: Update preference survey results
   - `get_preference_history`: Get preference change history

3. **Tasting Record Lambda**
   - `add_tasting_record`: Record new sake tasting experience
   - `get_tasting_history`: Retrieve user's rating history
   - `get_tasting_statistics`: Get analytics on user's tasting patterns

4. **Brewery Information Lambda**
   - `get_brewery_info`: Get brewery details
   - `list_brewery_sakes`: List all sakes from a brewery
   - `search_breweries_by_region`: Search breweries by prefecture

5. **Image Recognition Lambda**
   - `identify_sake_from_image`: Identify sake from label photo
   - `get_similar_sakes`: Find similar sake when identification fails

### Memory Configuration

AgentCore Memory manages both short-term and long-term memory:

#### Short-Term Memory (Session-based)
- **Type**: Event Storage
- **Purpose**: Maintain conversation context within a session
- **Retention**: Duration of session
- **Data**: User messages, agent responses, tool calls

#### Long-Term Memory (Persistent)

1. **Semantic Memory**
   - **Strategy**: SEMANTIC
   - **Purpose**: Store factual information about user preferences
   - **Examples**: "User prefers dry sake", "User dislikes strong acidity"
   - **Retrieval**: Vector similarity search

2. **User Preference Memory**
   - **Strategy**: USER_PREFERENCES
   - **Purpose**: Track explicit user preferences and settings
   - **Examples**: Budget constraints, category exclusions, sweetness level
   - **Retrieval**: Direct lookup by preference key

3. **Summary Memory**
   - **Strategy**: SUMMARY
   - **Purpose**: Maintain conversation summaries for context
   - **Examples**: "User has tried 5 sake so far and prefers fruity styles"
   - **Retrieval**: Chronological summary access

### Identity and Authentication Flow

AgentCore Identity manages authentication using OAuth 2.0 with AWS Cognito:

1. **Inbound Authentication** (User → Agent)
   - User authenticates via Cognito User Pool
   - Receives OAuth access token
   - Token passed to Runtime agent via Authorization header
   - Runtime validates token with AgentCore Identity

2. **Outbound Authentication** (Agent → Tools)
   - Agent uses workload identity to access Gateway tools
   - Gateway validates agent identity
   - Tools access DynamoDB with IAM execution role

3. **Token Management**
   - Access token expiration: 1 hour
   - Refresh token for seamless session renewal
   - Token exchange handled by AgentCore Identity

### Observability Setup

AgentCore Observability provides comprehensive monitoring:

1. **CloudWatch Logs**
   - Agent execution logs
   - Tool invocation logs
   - Error and warning logs

2. **CloudWatch Metrics**
   - Agent invocation count
   - Tool execution duration
   - Memory retrieval performance
   - Error rates by tool

3. **X-Ray Tracing**
   - End-to-end request tracing
   - Tool call visualization
   - Performance bottleneck identification

4. **Custom Spans**
   - Recommendation algorithm execution
   - Memory retrieval operations
   - LLM inference timing

## Recommendation Algorithm

### Initial Recommendation (First-time Users)

1. **Preference matching**: Match sake based on preference survey
   - Sweetness/dryness alignment (±2 on 1-5 scale)
   - Within budget constraint
   - Exclude avoided categories

2. **Diversity**: Ensure variety in recommendations
   - Mix different categories
   - Mix different price points
   - Mix different regions

3. **Beginner-friendly**: For beginners, prioritize
   - Popular and well-reviewed sake
   - Easy-to-drink characteristics
   - Affordable options

### Continuous Recommendation (Return Users)

1. **Historical preference analysis**
   - Analyze past ratings (weighted by recency)
   - Identify liked characteristics
   - Identify disliked characteristics

2. **Collaborative filtering**
   - Find similar users based on rating patterns
   - Recommend sake liked by similar users

3. **Content-based filtering**
   - Recommend sake similar to highly-rated sake
   - Match characteristics of liked sake

4. **Balance**: Combine multiple factors
   - 40% historical preferences
   - 30% collaborative filtering
   - 20% content-based filtering
   - 10% diversity/exploration

### Scoring System

Each candidate sake receives a score (0-100):

- **Preference match** (0-40 points)
  - Sweetness alignment: up to 20 points
  - Price alignment: up to 20 points

- **Historical ratings** (0-30 points)
  - Based on past ratings of similar sake

- **Collaborative signals** (0-20 points)
  - Based on similar users' ratings

- **Diversity bonus** (0-10 points)
  - Bonus for introducing new categories/styles

## Image Recognition Workflow

1. **Image Upload**
   - User uploads sake label image via Streamlit
   - Image uploaded to S3 bucket
   - S3 key returned to frontend

2. **Label Detection**
   - Lambda function triggered
   - Amazon Bedrock analyzes image
   - Extract text and visual features
   - Match against sake database

3. **Sake Identification**
   - Query DynamoDB with extracted features
   - Return best match with confidence score
   - If confidence < 70%, suggest similar options

4. **Result Display**
   - Show identified sake details
   - Display compatibility with user preferences
   - Offer option to add to tasting history

## Security Requirements

### Authentication
- AWS Cognito User Pool
- Email/password authentication
- Email verification required
- Password requirements:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - At least 1 special character

### Authorization
- All API requests require valid JWT token
- Token passed in Authorization header
- Token expiration: 1 hour (access token)
- Refresh token for session renewal

### Data Protection
- DynamoDB encryption at rest
- S3 encryption at rest
- HTTPS/TLS for all API communications
- No sensitive data in logs

### Input Validation
- Sanitize all user inputs
- Validate email format
- Validate rating range (1-5)
- Validate budget range (positive integer)
- Validate image file type and size

### Rate Limiting (AWS WAF)
- 2000 requests per IP per 5 minutes
- Block known malicious IPs
- SQL injection protection
- XSS protection

## Performance Requirements

### Response Time Targets
- Page load: < 2 seconds
- API response: < 1 second (non-streaming)
- **Streaming Response**: First token < 500ms, continuous token stream
- Recommendation generation: < 3 seconds (complete response)
- Image recognition: < 5 seconds

### Streaming Performance
- **Time to First Token (TTFT)**: < 500ms
  - User sees response start immediately
  - Improves perceived responsiveness

- **Token Throughput**: 20-50 tokens/second
  - Smooth, readable streaming experience
  - Real-time conversation feel

- **End-to-End Latency**: < 3 seconds for full response
  - Complete recommendation delivered
  - Multiple sake suggestions with explanations

### Scalability
- Support 1000 concurrent users
- Support 100+ concurrent streaming sessions
- Handle 10,000 daily active users
- Store 100,000+ sake records
- Store 1,000,000+ tasting records

### Availability
- 99% uptime target
- Graceful degradation if Bedrock unavailable
- Cached recommendations as fallback
- Stream reconnection on network interruption

## Monitoring and Logging

### Metrics to Track
- API response times (p50, p95, p99)
- Error rates by endpoint
- User sign-ups and logins
- Recommendation accuracy
- Image recognition success rate
- Bedrock API usage and costs

### Alarms
- Error rate > 5% for 5 minutes
- API latency > 3 seconds for 5 minutes
- Failed authentications spike
- Bedrock throttling errors

### Logs to Collect
- All API requests (anonymized)
- Authentication events
- Recommendation requests and results
- Image recognition attempts
- Error stack traces

## Testing Requirements

### Unit Testing
- **Coverage**: 70% minimum
- **Scope**:
  - Recommendation algorithm
  - Data validation functions
  - API client methods
  - Authentication helpers

### Integration Testing
- **Scope**:
  - Lambda + DynamoDB integration
  - AppSync + Lambda resolvers
  - Cognito authentication flow
  - S3 image upload/retrieval

### End-to-End Testing
- **User Journeys**:
  1. Sign up → preference survey → view recommendations
  2. Sign in → rate sake → get updated recommendations
  3. Upload image → identify sake → view details
  4. View history → export data

### Load Testing
- Simulate 100 concurrent users
- Test recommendation generation under load
- Test image recognition under load
- Identify performance bottlenecks

## Deployment Requirements

### Environments
- **Development**: Local Streamlit + AgentCore Runtime local testing
- **Staging**: ECS Fargate (dev environment) + AgentCore Runtime (dev environment)
- **Production**: ECS Fargate (prod environment) + AgentCore Runtime (prod environment)

### AgentCore Deployment Workflow

1. **Agent Development**
   ```bash
   # Local testing
   python agent.py  # Runs on localhost:8080

   # Test locally
   curl -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Recommend sake for me"}'
   ```

2. **Agent Configuration**
   ```bash
   # Configure agent for deployment
   agentcore configure \
     --entrypoint agent.py \
     --execution-role arn:aws:iam::ACCOUNT:role/SakeSenseiAgentRole \
     --name sakesensei-recommendation-agent

   # Configure OAuth settings (Cognito)
   # OAuth Discovery URL: https://cognito-idp.ap-northeast-1.amazonaws.com/USERPOOL_ID/.well-known/openid-configuration
   # OAuth Client ID: Cognito App Client ID
   ```

3. **Agent Launch**
   ```bash
   # Deploy to AgentCore Runtime
   agentcore launch

   # Test deployed agent
   agentcore invoke '{"prompt": "Recommend sake for me"}'
   ```

4. **Gateway Setup**
   ```python
   # Create Gateway
   python scripts/create_gateway.py --name sakesensei-gateway

   # Add Lambda targets
   python scripts/add_gateway_targets.py \
     --gateway-id GATEWAY_ID \
     --lambda-arns RECOMMENDATION_LAMBDA,PREFERENCE_LAMBDA,TASTING_LAMBDA

   # Enable tool search
   python scripts/enable_tool_search.py --gateway-id GATEWAY_ID
   ```

5. **Memory Setup**
   ```python
   # Create Memory store
   python scripts/create_memory.py \
     --name sakesensei-memory \
     --strategies SEMANTIC,USER_PREFERENCES,SUMMARY
   ```

### CI/CD Pipeline

#### GitHub Actions Workflow

**Pull Request Workflow:**
```
PR opened/updated
  ├─ Lint Check (ruff format --check, ruff check)
  ├─ Type Check (mypy)
  ├─ Unit Tests (pytest with coverage)
  ├─ Security Scan (bandit)
  ├─ Docker Build (validation only)
  └─ Agent Local Test
     └─ PR status updated (pass/fail)
```

**Staging Deployment (on merge to main):**
```
main branch updated
  ├─ 1. Deploy Infrastructure
  │    ├─ CDK bootstrap (if needed)
  │    └─ CDK deploy --all
  │       ├─ DynamoDB tables
  │       ├─ Lambda functions
  │       ├─ S3 buckets
  │       ├─ Cognito User Pool
  │       └─ IAM roles
  │
  ├─ 2. Deploy AgentCore Services
  │    ├─ Update Gateway targets
  │    ├─ Configure Memory stores
  │    └─ Setup Identity integration
  │
  ├─ 3. Deploy Agent to Staging
  │    ├─ agentcore configure
  │    └─ agentcore launch --environment staging
  │
  ├─ 4. Build & Deploy Frontend
  │    ├─ Build Docker image (with git SHA tag)
  │    ├─ Push to ECR
  │    └─ copilot deploy --env dev --tag <sha>
  │
  ├─ 5. Run E2E Tests
  │    └─ pytest tests/e2e/ --base-url <staging-url>
  │
  └─ 6. Slack Notification
       └─ "✅ Staging deployment successful"
```

**Production Deployment (manual trigger):**
```
Manual workflow_dispatch
  ├─ Manual Approval Gate (GitHub environment protection)
  │
  ├─ 1. Deploy Agent to Production
  │    └─ agentcore launch --environment production
  │
  ├─ 2. Deploy Frontend to Production
  │    └─ copilot deploy --env prod --tag <version>
  │
  ├─ 3. Run Smoke Tests
  │    └─ pytest tests/smoke/ --base-url <prod-url>
  │
  └─ 4. Team Notification
       └─ "🚀 Production deployment successful"
```

#### Deployment Artifacts

**Docker Image Tagging Strategy:**
- `sakesensei:latest` - Latest staging build
- `sakesensei:<git-sha>` - Specific commit build
- `sakesensei:v<version>` - Production release (semantic versioning)

**ECR Repository:**
- Repository: `sakesensei-streamlit`
- Lifecycle policy: Keep last 10 images, expire untagged after 7 days
- Vulnerability scanning: Enabled on push

#### Monitoring & Alerts

**CI/CD Pipeline Monitoring:**
- GitHub Actions dashboard for workflow status
- Slack notifications for deployment events
- CloudWatch alarms for deployment failures

**Deployment Metrics:**
- Time to deploy (target: < 10 minutes)
- Success rate (target: > 95%)
- Rollback frequency (target: < 5% of deployments)

#### Security in CI/CD

**Secret Management:**
- AWS credentials stored as GitHub secrets
- AgentCore API keys in AWS Secrets Manager
- Cognito credentials in AWS Parameter Store
- Docker registry credentials rotated monthly

**Security Checks:**
- Bandit: Python security linting
- Safety: Dependency vulnerability scanning
- Trivy: Docker image vulnerability scanning
- AWS Config: Infrastructure compliance checking

#### Deployment Gates

**Staging Deployment:**
- All tests must pass
- Code coverage > 70%
- No high-severity security vulnerabilities
- Docker build successful

**Production Deployment:**
- Manual approval required
- E2E tests passed in staging
- Staging deployment age > 24 hours
- No active incidents

### Rollback Strategy
- Keep previous agent versions in Runtime
- Instant rollback via `agentcore rollback`
- ECS task definition revisions preserved
- Instant rollback via `copilot svc rollback`
- Lambda function versions preserved
- Gateway target version management
- Database migrations reversible
- Feature flags for new features

## Cost Estimates (Monthly)

### AWS Services

#### AgentCore Services
- **AgentCore Runtime**:
  - $0.20 per 1,000 agent invocations
  - ~$20 for 100K invocations/month
- **AgentCore Gateway**:
  - $0.10 per 1,000 tool calls
  - ~$10 for 100K tool calls/month
- **AgentCore Memory**:
  - $0.30 per GB-month storage
  - $0.05 per 1,000 read/write operations
  - ~$5 for 10GB storage + 100K operations
- **AgentCore Identity**:
  - Included with Cognito integration
- **AgentCore Observability**:
  - Included (uses CloudWatch pricing)

#### Core AWS Services
- **ECS Fargate**:
  - 0.25 vCPU, 0.5GB RAM per task
  - ~$15 for 2 tasks running 24/7
- **Application Load Balancer**:
  - ~$20 (fixed cost + data processing)
- **ECR**: ~$1 (image storage)
- **Lambda**: ~$10 (1M invocations for Gateway tools)
- **DynamoDB**: ~$5 (on-demand, 100K reads/writes)
- **S3**: ~$2 (10GB storage, 100K requests)
- **Cognito**: Free tier (50K MAU)
- **Bedrock (Claude Sonnet 4.5)**:
  - Input: $3 per 1M tokens
  - Output: $15 per 1M tokens
  - ~$50 for 1000 conversations (avg 1000 tokens in/out each)
- **CloudWatch**: ~$5 (logs + metrics)
- **WAF**: ~$5

**Total**: ~$153/month for 1000 active users

### Cost Optimization Strategies
1. **ECS Fargate**: Use Fargate Spot for dev environment (~70% savings)
2. **ALB**: Use single ALB shared across services
3. **AgentCore Runtime**: Use provisioned concurrency only for production
4. **Memory**: Configure retention policies (e.g., 90 days for events)
5. **Gateway**: Enable tool caching to reduce duplicate calls
6. **Bedrock**: Optimize prompts to minimize token usage
7. **DynamoDB**: Use on-demand billing for variable workloads

## Future Enhancements (Out of Scope for MVP)

1. **Social Features**
   - Share recommendations with friends
   - Sake tasting events
   - Community reviews

2. **Advanced Filtering**
   - Filter by region
   - Filter by rice variety
   - Filter by serving temperature

3. **Gamification**
   - Badges for trying new sake
   - Tasting challenges
   - Leaderboards

4. **Mobile App**
   - Native iOS/Android apps
   - Offline mode
   - Push notifications

5. **Subscription Service**
   - Monthly sake delivery
   - Exclusive recommendations
   - Virtual tasting sessions

6. **Multi-language Support**
   - English interface
   - Translated sake descriptions
   - International shipping

## Success Metrics

### User Engagement
- Daily active users (DAU)
- Weekly active users (WAU)
- Average session duration
- Recommendations viewed per session

### Recommendation Quality
- Click-through rate on recommendations
- Average rating of recommended sake
- Diversity of tried sake
- Return user rate

### Business Metrics
- User sign-up rate
- User retention (7-day, 30-day)
- Recommendation acceptance rate
- Cost per active user

### Technical Metrics
- System uptime
- API response times
- Error rates
- Bedrock API success rate