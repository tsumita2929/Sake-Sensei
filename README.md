# Sake Sensei

AI-powered sake recommendation system for beginners, built with Streamlit and AWS.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- **uv** package manager (mandatory)
- **AWS Copilot CLI** (for frontend deployment)
- **Docker** (for containerization)
- AWS account with appropriate permissions
- AWS CLI configured

### Installation

1. **Install uv** (if not already installed):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Clone the repository**:

```bash
git clone https://github.com/your-org/sake-sensei.git
cd sake-sensei
```

3. **Install dependencies**:

```bash
# Sync all dependencies (including dev)
uv sync --all-extras
```

4. **Set up environment variables**:

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your AWS credentials
# COGNITO_USER_POOL_ID=...
# COGNITO_CLIENT_ID=...
# APPSYNC_API_URL=...
# etc.
```

5. **Run the application**:

```bash
uv run streamlit run streamlit_app/app.py
```

## 🛠️ Development

### Code Quality

**Format code:**
```bash
uv run ruff format .
```

**Lint code:**
```bash
uv run ruff check --fix .
```

**Type checking:**
```bash
uv run mypy streamlit_app backend
```

### Testing

**Run all tests:**
```bash
uv run pytest
```

**Run with coverage:**
```bash
uv run pytest --cov=streamlit_app --cov=backend
```

**Run specific test:**
```bash
uv run pytest tests/unit/test_recommendation.py -v
```

### Adding Dependencies

**Production dependency:**
```bash
uv add package-name
```

**Dev dependency:**
```bash
uv add --dev package-name
```

## 📁 Project Structure

```
SakeSensei/
├── streamlit_app/          # Frontend Streamlit application
│   ├── app.py             # Main entry point
│   ├── Dockerfile         # Container image definition
│   ├── requirements.txt   # Python dependencies (from uv export)
│   ├── pages/             # Streamlit pages
│   ├── components/        # Reusable components
│   └── utils/             # Utility functions
├── copilot/               # AWS Copilot configuration
│   ├── .workspace         # Copilot workspace
│   ├── environments/      # Environment configs (dev, prod)
│   └── streamlit-app/     # ECS service manifest
├── infrastructure/        # IaC with AWS CDK
│   ├── app.py             # CDK app
│   └── stacks/            # CDK stacks
├── agent/                 # Strands Agent
│   ├── agent.py           # Agent definition
│   └── entrypoint.py      # AgentCore Runtime entrypoint
├── backend/               # Backend Lambda functions
│   ├── lambdas/           # Lambda function code
│   └── infrastructure/    # Legacy CloudFormation
├── scripts/               # AgentCore setup scripts
├── tests/                 # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── data/                  # Master data files
├── pyproject.toml         # Project configuration & dependencies
└── CLAUDE.md              # Implementation rules
```

## 📚 Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Common implementation rules (mandatory reading)
- **[REQUIREMENTS.md](./REQUIREMENTS.md)** - Detailed project requirements
- **[DESIGN.md](./DESIGN.md)** - System design and architecture
- **[TASKS.md](./TASKS.md)** - Implementation task list

## 🔒 Security

- All secrets must be stored in environment variables (never commit `.env`)
- AWS Cognito for authentication
- HTTPS enforced for all communications
- WAF protection enabled
- Input validation on all user inputs

## 🚢 Deployment

### Prerequisites

```bash
# Install AWS Copilot CLI
brew install aws/tap/copilot-cli

# Install Docker
brew install --cask docker

# Configure AWS CLI
aws configure
```

### Infrastructure (AWS CDK)

```bash
cd infrastructure
uv run cdk bootstrap  # First time only
uv run cdk deploy --all
```

### AgentCore Services

```bash
# Create Gateway
uv run python scripts/create_gateway.py

# Create Memory Store
uv run python scripts/create_memory.py

# Setup Identity with Cognito
uv run python scripts/setup_identity.py

# Deploy Agent to Runtime
cd agent
uv run agentcore configure --entrypoint entrypoint.py
uv run agentcore launch
```

### Frontend (ECS Fargate via Copilot)

```bash
# Initialize Copilot application (first time only)
cd streamlit_app
copilot init --app sakesensei --name streamlit-app --type "Load Balanced Web Service" --dockerfile ./Dockerfile

# Create environment
copilot env init --name dev --profile default --default-config

# Deploy to environment
copilot deploy --env dev

# For production
copilot env init --name prod --profile default
copilot deploy --env prod
```

### CI/CD Pipeline

See [CI/CD Workflow](#cicd-workflow) section below.

## 🔄 CI/CD Workflow

### GitHub Actions Pipeline

**On Pull Request:**
- Run unit tests (`pytest`)
- Run linting (`ruff format`, `ruff check`)
- Type checking (`mypy`)
- Security scans (`bandit`)
- Build Docker image (validation)
- Test agent locally

**On Merge to Main (Staging):**
1. Deploy infrastructure via CDK
2. Deploy Lambda functions
3. Update AgentCore Gateway targets
4. Deploy agent to staging Runtime
5. Build and push Docker image to ECR
6. Deploy Streamlit app to staging ECS (Copilot)
7. Run E2E tests
8. Create Slack notification

**Production Deployment (Manual Approval):**
1. Manual approval gate in GitHub Actions
2. Deploy agent to production Runtime
3. Deploy Streamlit app to production ECS (Copilot)
4. Run smoke tests
5. Notify team

### Rollback Procedures

```bash
# Rollback ECS service
copilot svc rollback --env prod

# Rollback agent
cd agent
uv run agentcore rollback

# Rollback infrastructure
cd infrastructure
uv run cdk deploy --rollback
```

## 🤝 Contributing

1. Read [CLAUDE.md](./CLAUDE.md) for implementation rules
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run quality checks:
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   uv run mypy streamlit_app backend
   uv run pytest
   ```
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `ci:` - CI/CD pipeline changes

## 📄 License

[MIT License](./LICENSE)

## 🙋 Support

For questions or issues, please open an issue on GitHub.

---

Built with ❤️ using Streamlit, AWS, and Claude Sonnet 4.5