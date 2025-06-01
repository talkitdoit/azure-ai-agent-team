# Azure AI Agent Team Code Review 🤖📝

A multi-agent system powered by Azure AI Foundry that automatically reviews code files in different programming languages and generates comprehensive markdown reports. Features OpenTelemetry tracing for deep observability.

## 🎥 Video Tutorial

Follow along with the [YouTube video tutorial](YOUR_VIDEO_LINK_HERE) for a complete walkthrough of this project.

## 📋 Prerequisites

### 1. Azure Account & Services
- **Azure Account**: [Create a free Azure account](https://azure.microsoft.com/free/)
- **Azure AI Foundry**: Access to Azure AI Foundry (formerly Azure AI Studio)
- **Azure OpenAI**: Deployed model (GPT-4, GPT-3.5-turbo, etc.)

### 2. Development Environment
- **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
- **Git**: [Install Git](https://git-scm.com/downloads)
- **uv**: Fast Python package manager (we'll install this)

## 🚀 Step-by-Step Setup

### Step 1: Install uv (Python Package Manager)

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify installation:**
```bash
uv --version
```

### Step 2: Clone the Repository

```bash
git clone [YOUR_REPOSITORY_URL]
cd azure-ai-agent-team
```

### Step 3: Set Up Python Virtual Environment

```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
# Install all required packages
uv pip install -r requirements.txt
```

### Step 5: Azure AI Foundry Setup

#### 5.1 Create Azure AI Foundry Project

1. Go to [Azure AI Foundry](https://ai.azure.com/)
2. Click **"New project"**
3. Choose your subscription and resource group
4. Give your project a name (e.g., "code-review-agents")
5. Select your region
6. Click **"Create"**

#### 5.2 Deploy a Model

1. In your AI Foundry project, go to **"Deployments"** → **"Deploy model"**
2. Choose a model (recommended: **GPT-4** or **GPT-3.5-turbo**)
3. Give it a deployment name (e.g., "gpt-4-deployment")
4. Configure settings and deploy
5. **Note down the deployment name** - you'll need this for your `.env` file

#### 5.3 Get Project Endpoint

1. In your AI Foundry project, go to **"Settings"** → **"Properties"**
2. Copy the **"Target URI"** or **"Endpoint"**
3. It should look like: `https://your-project.services.ai.azure.com/api/projects/your-project`

### Step 6: Tracing Setup (Optional but Recommended)

#### 6.1 Enable Tracing in Azure AI Foundry

1. In your AI Foundry project, go to **"Tracing"** in the left navigation
2. Follow the steps in the tracing section to set up Application Insights
3. Azure AI Foundry will automatically create and configure the Application Insights resource for you
4. Once configured, you can view traces directly in the AI Foundry portal

#### 6.2 Get Connection String (Optional)

If you want to include the Application Insights connection string in your `.env` file:

1. After setting up tracing in Step 6.1, Azure App Insights will show you the connection string, via 'properties'
2. Copy the **"Connection String"**
3. It looks like: `InstrumentationKey=xxx;IngestionEndpoint=https://...`

### Step 7: Environment Configuration

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
```

Add the following variables to your `.env` file:

```env
# Required: Azure AI Foundry Settings
PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
MODEL_DEPLOYMENT_NAME=your-model-deployment-name

# Optional: Application Insights for Tracing (auto-detected if set up in AI Foundry)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://...

# Optional: Tracing Configuration
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

**Example filled `.env`:**
```env
PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
MODEL_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

### Step 8: Authentication Setup

The project uses **Azure Default Credentials**, which automatically uses your logged-in Azure account.

#### Setup Azure CLI Authentication

```bash
# Install Azure CLI if not already installed
# macOS: brew install azure-cli
# Windows: Download from https://aka.ms/installazurecliwindows

# Login to Azure with your account
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

**That's it!** The `DefaultAzureCredential` will automatically use your logged-in Azure CLI credentials.

#### Alternative: Environment Variables (For Production/CI)

For production or CI/CD scenarios, you can use service principal credentials or an API key:

```env
# Add to your .env file
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### Step 9: Prepare Code for Review

Create the input directory and add code files:

```bash
# Create input directory
mkdir -p code-input

# Add your code files (examples)
echo 'print("Hello, World!")' > code-input/hello.py
echo 'console.log("Hello, World!");' > code-input/hello.js
echo 'SELECT * FROM users;' > code-input/query.sql
```

### Step 10: Configure Language Agents

Make sure you have the `language_agents.yaml` file in your project root. This file defines which agents handle which programming languages.

Example structure:
```yaml
language_configs:
  python:
    name: "python-expert"
    instructions: "You are a Python code review expert..."
  javascript:
    name: "javascript-expert"
    instructions: "You are a JavaScript code review expert..."
  # ... more languages

extension_to_language:
  ".py": "python"
  ".js": "javascript"
  ".ts": "typescript"
  # ... more extensions
```

### Step 11: Run the Project

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run the code review
python agent_team_code_review.py
```

## 📊 Viewing Traces (Optional)

If you set up tracing in Step 6:

### In Azure AI Foundry Portal
1. Go to your AI Foundry project
2. Click **"Tracing"** in the left menu
3. View your traces and execution details
4. Analyze agent performance and interactions

### In Azure Application Insights
1. From the tracing section in AI Foundry, click to open Application Insights
2. Click **"Transaction search"** or **"Application map"**
3. View detailed telemetry and performance data

## 📁 Project Structure

```
azure-ai-agent-team/
├── README.md
├── requirements.txt
├── .env                          # Your environment variables
├── agent_team_code_review.py     # Main application
├── language_agents.yaml          # Agent configurations
├── utils/
│   └── agent_team.py             # Agent team utilities
├── code-input/                   # Place your code files here
│   ├── example.py
│   ├── example.js
│   └── example.sql
└── code_review_report.md         # Generated report (after running)
```

## 🎯 Expected Output

After running successfully, you'll see:

1. **Console output** showing agent creation and processing
2. **`code_review_report.md`** file with comprehensive code review
3. **Traces in Azure** (if tracing is configured)

## 🔍 Troubleshooting

### Common Issues

#### "HTTP transport has already been closed"
- **Cause**: Client context issue
- **Solution**: Make sure you're using the latest code version

#### "Authentication failed"
- **Cause**: Azure credentials not set up
- **Solution**: Run `az login` to authenticate with your Azure account

#### "Model deployment not found"
- **Cause**: Wrong `MODEL_DEPLOYMENT_NAME` in `.env`
- **Solution**: Check deployment name in Azure AI Foundry

#### "No supported code files found"
- **Cause**: No files in `code-input` directory
- **Solution**: Add code files to `code-input/` directory

### Environment Variables Checklist

- [ ] `PROJECT_ENDPOINT` - Azure AI Foundry project endpoint
- [ ] `MODEL_DEPLOYMENT_NAME` - Exact name of your model deployment
- [ ] Azure CLI authentication: `az login` completed

### Verify Setup

```bash
# Check Python version
python --version  # Should be 3.11+

# Check uv installation
uv --version

# Check Azure login and account
az account show

# Check virtual environment
which python  # Should point to .venv/bin/python
```

## 🛠️ Advanced Configuration

### Custom Service Name
```env
OTEL_SERVICE_NAME=my-custom-service-name
```

### Disable Content Recording (for privacy)
```env
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=false
```

### Local-only Tracing
Simply don't set up tracing in Azure AI Foundry and traces will be local only.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add appropriate tracing spans
5. Test thoroughly
6. Submit a pull request

## 📚 Additional Resources

- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [uv Package Manager](https://astral.sh/uv/)

## 📄 License

[Include your license information here]

---

**Happy Code Reviewing! 🚀**

*Don't forget to ⭐ star the repository if this helped you!* 