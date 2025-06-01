# Azure AI Agent Team with Tracing

This project now includes comprehensive OpenTelemetry tracing support using Azure AI Foundry and Azure Monitor. The tracing provides deep visibility into your agent team's execution, helping with debugging, performance monitoring, and understanding agent interactions.

## 🚀 Features Added

### Tracing Capabilities
- **OpenTelemetry Integration**: Full OpenTelemetry standard compliance
- **Azure Monitor Export**: Traces automatically sent to Application Insights
- **Content Recording**: Optional recording of chat message content
- **Hierarchical Spans**: Detailed breakdown of execution flow
- **Custom Attributes**: Rich metadata for each operation

### Traced Operations
- File discovery and language detection
- Agent team setup and configuration
- Individual agent creation
- Code review processing
- Report generation
- Cleanup operations

## 📋 Prerequisites

### Azure Setup
1. **Azure AI Foundry Project**: You need an active Azure AI Foundry project
2. **Application Insights**: Connect an Application Insights resource to your project:
   - Navigate to **Tracing** in your Azure AI Foundry portal
   - Create a new Application Insights resource if needed
   - Connect it to your AI Foundry project

### Environment Variables
```bash
# Required for agent functionality
PROJECT_ENDPOINT=your_azure_ai_foundry_endpoint
MODEL_DEPLOYMENT_NAME=your_model_deployment_name

# Optional: Enable content recording (default: true)
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

## 🛠️ Installation

Install the required dependencies:

```bash
# Using pip
pip install -r requirements.txt

# Using uv (as per your preference)
uv pip install -r requirements.txt
```

### Key Dependencies Added
- `azure-monitor-opentelemetry`: Azure Monitor integration
- `opentelemetry-sdk`: Core OpenTelemetry SDK
- `azure-ai-projects`: Updated Azure AI client with tracing support

## 🔍 Tracing Architecture

### Span Hierarchy
```
code-review-agent-team (root span)
├── setup-tracing
├── file-discovery
├── agent-team-setup
│   ├── create-agent-{language} (per language)
│   └── create-documentation-agent
├── process-code-review
├── generate-report
└── cleanup
```

### Trace Attributes
Each span includes relevant attributes:
- **Project info**: `project.endpoint`, `model.deployment`
- **File metrics**: `files.total`, `languages.detected`, `languages.count`
- **Agent details**: `agent.language`, `agent.name`, `agent.files_count`
- **Processing data**: `request.length`, `messages.count`, `report.generated`

## 📊 Viewing Traces

### Azure AI Foundry Portal
1. Navigate to your Azure AI Foundry project
2. Go to **Tracing** in the left navigation
3. Filter and view your traces
4. Click on individual traces to see detailed spans and timing

### Azure Monitor Application Insights
1. Open Application Insights from "Manage data source" in Azure AI Foundry
2. Use **End-to-end transaction details** view
3. Query traces with KQL:
   ```kql
   traces
   | where cloud_RoleName == "your_service_name"
   | order by timestamp desc
   ```

## 🎯 Understanding Trace Data

### Key Metrics to Monitor
- **File Discovery Time**: How long it takes to scan and categorize files
- **Agent Setup Duration**: Time to create and configure agents
- **Processing Time**: Duration of the actual code review
- **Message Count**: Number of agent interactions
- **Report Generation**: Success/failure of final documentation

### Troubleshooting with Traces
- **High Latency**: Check span durations to identify bottlenecks
- **Agent Failures**: Look for error attributes in agent creation spans
- **Missing Reports**: Check `report.generated` attribute
- **File Processing Issues**: Examine file discovery span attributes

## 🔧 Configuration Options

### Content Recording
```python
# Enable content recording (may contain sensitive data)
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"

# Disable content recording for privacy
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "false"
```

### Service Name (for multiple apps)
```bash
# Set via environment variable
export OTEL_SERVICE_NAME="code-review-agent-team"
```

Or programmatically:
```python
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

resource = Resource.create({"service.name": "code-review-agent-team"})
trace.set_tracer_provider(TracerProvider(resource=resource))
```

## 🚨 Important Notes

### Privacy Considerations
- **Content Recording**: When enabled, traces may contain file content and chat messages
- **Sensitive Data**: Review what data is being traced before enabling in production
- **Compliance**: Ensure tracing configuration meets your organization's data policies

### Performance Impact
- **Minimal Overhead**: OpenTelemetry adds minimal performance overhead
- **Async Processing**: Traces are sent asynchronously to avoid blocking operations
- **Sampling**: Consider implementing sampling for high-volume scenarios

### Error Handling
- **Graceful Degradation**: If Application Insights is not configured, the app continues without tracing
- **Fallback Mode**: Traces can be logged locally if Azure Monitor is unavailable
- **Debug Output**: Enable debug logging to troubleshoot tracing issues

## 🔍 Advanced Usage

### Custom Spans
Add your own tracing to custom functions:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def custom_function():
    with tracer.start_as_current_span("custom_operation") as span:
        span.set_attribute("custom.attribute", "value")
        # Your logic here
        return result
```

### Local Tracing (Development)
For local development without Azure Monitor:

```python
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace import TracerProvider

# Log traces to console
span_exporter = ConsoleSpanExporter()
tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)
```

## 📚 Additional Resources

- [Azure AI Foundry Tracing Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-application)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/languages/python/)
- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)

## 🤝 Contributing

When adding new functionality, consider:
1. Adding appropriate tracing spans for new operations
2. Including relevant attributes for debugging
3. Following the existing span naming conventions
4. Testing both with and without Application Insights configured 