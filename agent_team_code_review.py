import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ToolSet, CodeInterpreterTool
from utils.agent_team import AgentTeam, _create_task
import re
import ast
import yaml

# OpenTelemetry imports for tracing
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

load_dotenv()

# Enable content recording for tracing (set to True to trace chat message content)
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"

# Load language configs and extension mapping from YAML
with open("language_agents.yaml", "r") as f:
    config = yaml.safe_load(f)
LANGUAGE_CONFIGS = config["language_configs"]
EXTENSION_TO_LANGUAGE = config["extension_to_language"]

def detect_language(file_path: Path) -> str:
    return EXTENSION_TO_LANGUAGE.get(file_path.suffix.lower(), 'unknown')

def read_code_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def prepare_code_review_content(files: List[Path]) -> str:
    content = "Please review these files:\n\n"
    for file_path in files:
        code = read_code_file(file_path)
        content += f"File: {file_path.name}\n```{file_path.suffix[1:]}\n{code}\n```\n\n"
    return content

PROJECT_ENDPOINT = os.getenv('PROJECT_ENDPOINT')
MODEL_DEPLOYMENT_NAME = os.getenv('MODEL_DEPLOYMENT_NAME')

if not PROJECT_ENDPOINT or not MODEL_DEPLOYMENT_NAME:
    raise EnvironmentError("PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME must be set in the environment.")

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Setup Azure Monitor tracing
with tracer.start_as_current_span("setup-tracing") as setup_span:
    try:
        # For AgentsClient, we'll setup basic Azure Monitor tracing
        # Note: This assumes you have Application Insights configured
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if connection_string:
            configure_azure_monitor(connection_string=connection_string)
            setup_span.set_attribute("tracing.enabled", True)
            print("Azure Monitor tracing configured successfully.")
        else:
            print("APPLICATIONINSIGHTS_CONNECTION_STRING not set. Tracing will be local only.")
            setup_span.set_attribute("tracing.enabled", False)
    except Exception as e:
        print(f"Warning: Could not configure Azure Monitor tracing: {e}")
        setup_span.set_attribute("tracing.error", str(e))

# Main execution wrapped in tracing span
with tracer.start_as_current_span("code-review-agent-team") as main_span:
    main_span.set_attribute("project.endpoint", PROJECT_ENDPOINT)
    main_span.set_attribute("model.deployment", MODEL_DEPLOYMENT_NAME)
    
    # File discovery and language detection
    with tracer.start_as_current_span("file-discovery") as discovery_span:
        input_dir = Path('code-input')
        input_dir.mkdir(exist_ok=True)
        
        # Group files by language
        language_files: Dict[str, List[Path]] = {}
        total_files = 0
        for file_path in input_dir.glob('**/*'):
            if file_path.is_file():
                language = detect_language(file_path)
                if language != 'unknown':
                    language_files.setdefault(language, []).append(file_path)
                    total_files += 1
        
        discovery_span.set_attribute("files.total", total_files)
        discovery_span.set_attribute("languages.detected", list(language_files.keys()))
        discovery_span.set_attribute("languages.count", len(language_files))
        
        if not language_files:
            raise ValueError("No supported code files found in code-input directory")

    # Original client setup
    credential = DefaultAzureCredential()
    agents_client = AgentsClient(endpoint=PROJECT_ENDPOINT, credential=credential)
    
    # Register _create_task for function calling (required for AgentTeam delegation)
    agents_client.enable_auto_function_calls({_create_task})

    with agents_client:
        # Agent team setup (wrapped in span)
        with tracer.start_as_current_span("agent-team-setup") as team_span:
            team_span.set_attribute("team.name", "code_review_team")
            
            agent_team = AgentTeam("code_review_team", agents_client=agents_client)

            # Add a review agent for each language
            for language, files in language_files.items():
                with tracer.start_as_current_span(f"create-agent-{language}") as agent_span:
                    agent_span.set_attribute("agent.language", language)
                    agent_span.set_attribute("agent.files_count", len(files))
                    
                    config = LANGUAGE_CONFIGS[language]
                    code_interpreter = CodeInterpreterTool()
                    toolset = ToolSet()
                    toolset.add(code_interpreter)
                    agent_team.add_agent(
                        model=MODEL_DEPLOYMENT_NAME,
                        name=config['name'],
                        instructions=config['instructions'] + "\n\nYou will receive a list of files to review in the user request.",
                        toolset=toolset,
                        can_delegate=False,
                    )
                    
                    agent_span.set_attribute("agent.name", config['name'])

            # Add a documentation agent
            with tracer.start_as_current_span("create-documentation-agent") as doc_agent_span:
                doc_instructions = """You are a technical documentation expert. Your task is to:\n1. Take multiple code review feedbacks and format them into clear markdown\n2. Create a well-structured document with sections per language\n3. Include code examples where relevant\n4. Add an executive summary at the top\nImportant formatting rules:\n- Use proper markdown heading levels\n- For code examples, use appropriate language tags"""
                code_interpreter = CodeInterpreterTool()
                doc_toolset = ToolSet()
                doc_toolset.add(code_interpreter)
                agent_team.add_agent(
                    model=MODEL_DEPLOYMENT_NAME,
                    name="documentation-agent",
                    instructions=doc_instructions,
                    toolset=doc_toolset,
                    can_delegate=False,
                )
                
                doc_agent_span.set_attribute("agent.name", "documentation-agent")
                doc_agent_span.set_attribute("agent.type", "documentation")

            agent_team.assemble_team()

        # Request processing (wrapped in span)
        with tracer.start_as_current_span("process-code-review") as review_span:
            # Prepare the user request for the team leader
            review_requests = []
            for language, files in language_files.items():
                review_requests.append(f"Review the following {language} files:\n\n" + prepare_code_review_content(files))
            user_request = "\n\n".join(review_requests) + "\n\nAfter reviewing, consolidate all feedback into a markdown document."
            
            review_span.set_attribute("request.length", len(user_request))
            review_span.set_attribute("request.languages", list(language_files.keys()))

            print("\nSubmitting user request to agent team...\n")
            result = agent_team.process_request(request=user_request)

        # Message processing and report generation (wrapped in span)
        with tracer.start_as_current_span("generate-report") as report_span:
            # Fetch all agent messages from the thread
            thread_id = agent_team._agent_thread.id
            messages = list(agents_client.messages.list(thread_id=thread_id))
            
            report_span.set_attribute("messages.count", len(messages))

            # Debug: print the full message object for each message
            for msg in messages:
                print(msg)

            # Heuristic: find the first substantial markdown message from any agent or assistant
            def is_documentation_message(msg):
                if hasattr(msg, 'content') and msg.content:
                    text = str(msg.content).strip()
                    return (msg.role in ("agent", "assistant")) and (text.startswith("#") or "Code Review" in text or "Overview" in text)
                return False

            doc_message = next((msg for msg in messages if is_documentation_message(msg)), None)

            # Fallback: find the longest markdown message with headings
            if not doc_message:
                markdown_candidates = [msg for msg in messages if hasattr(msg, 'content') and msg.content and (str(msg.content).strip().startswith("#") or "Code Review" in str(msg.content) or "Overview" in str(msg.content))]
                if markdown_candidates:
                    doc_message = max(markdown_candidates, key=lambda m: len(str(m.content)))

            # Helper to extract markdown from various content structures
            def extract_markdown_content(content):
                # If content is a list, concatenate all markdown strings found
                if isinstance(content, list):
                    markdowns = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item and 'value' in item['text']:
                            markdowns.append(item['text']['value'])
                    if markdowns:
                        return "\n\n".join(markdowns)
                # If content is a dict with 'text'->'value'
                if isinstance(content, dict) and 'text' in content and 'value' in content['text']:
                    return content['text']['value']
                # If content is a string that looks like a list/dict, parse and extract
                if isinstance(content, str) and content.strip().startswith("[{"):
                    try:
                        parsed = ast.literal_eval(content)
                        return extract_markdown_content(parsed)
                    except Exception:
                        pass
                # If content is a string, return as is
                if isinstance(content, str):
                    return content
                return str(content)

            # Helper to clean up and normalize markdown text
            def reformat_to_markdown(text):
                text = text.strip()
                # Replace escaped newlines with real newlines
                text = text.replace("\\n", "\n")
                # Optionally, fix double-escaped code blocks, etc.
                text = re.sub(r"```+", "```", text)
                # Remove any remaining single quotes at start/end
                text = text.strip("'")
                return text

            report_generated = False
            if doc_message:
                markdown_doc = extract_markdown_content(doc_message.content)
                markdown_doc = reformat_to_markdown(markdown_doc)
                with open("code_review_report.md", "w") as f:
                    f.write(markdown_doc)
                print("\nMarkdown document saved as 'code_review_report.md'")
                report_generated = True
            else:
                print("No documentation agent response found in thread.")
            
            report_span.set_attribute("report.generated", report_generated)
            if report_generated:
                report_span.set_attribute("report.filename", "code_review_report.md")

        # Cleanup (wrapped in span) - MOVED INSIDE agents_client context
        with tracer.start_as_current_span("cleanup") as cleanup_span:
            agent_team.dismantle_team()
            cleanup_span.set_attribute("cleanup.completed", True)
            print("All agents dismantled.") 