from flask import Blueprint, jsonify, request, current_app
from ..utils.extensions import app
from ..prompts.prompt_manager import PromptManager
from ..database.management.db_utils import DatabaseUtils
from xml.etree.ElementTree import ParseError as XMLParseError
from ..config import AppConfig
from ..llm.config import LLMConfig
from ..llm.mcp import MCPClient
import os
import xml.etree.ElementTree as ET

llm_bp = Blueprint('llm', __name__)

# Initialize services
app_config = AppConfig()
llm_config = LLMConfig()
prompt_manager = PromptManager(
    prompts_dir=app_config.get('PROMPTS_DIR', './prompts'),
    schema_dir=app_config.get('SCHEMA_DIR', './prompts/schemas')
)
mcp_client = MCPClient(llm_config)
db_utils = DatabaseUtils()

def create_error_response(message, status_code=500, details=None, error_type=None):
    response = {
        "error": message,
        "status": status_code,
        "error_type": error_type or "UnknownError"
    }
    if details and app_config.get('DEBUG', False):
        response["details"] = str(details)
    return jsonify(response), status_code

@llm_bp.route('/prompts', methods=['GET'])
def list_prompts():
    """List all available prompts"""
    try:
        prompts = prompt_manager.get_all_prompts()
        return jsonify({
            'status': 'success',
            'prompts': prompts
        })
    except Exception as e:
        return create_error_response("Failed to list prompts", 500, e)

@llm_bp.route('/prompts/<prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """Get a specific prompt by ID"""
    try:
        prompt = prompt_manager.get_prompt(prompt_id)
        return jsonify({
            'status': 'success',
            'prompt': prompt
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404

@llm_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat interactions with the LLM"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({
            'status': 'error',
            'message': 'No message provided'
        }), 400
    
    try:
        provider = data.get('provider', llm_config.get('DEFAULT_PROVIDER', 'openai'))
        model = data.get('model', llm_config.get('DEFAULT_MODEL', 'gpt-3.5-turbo'))
        context = data.get('context', [])
        
        response = mcp_client.chat(
            message=data['message'],
            provider=provider,
            model=model,
            context=context
        )
        
        return jsonify({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        return create_error_response(str(e), 500, e)

@llm_bp.route('/analyze', methods=['POST'])
def analyze_data():
    """Analyze data using a specific prompt template"""
    data = request.get_json()
    
    if not data or 'prompt_id' not in data:
        return create_error_response('No prompt ID provided', 400, error_type='ValidationError')
    
    try:
        # Load and validate prompt XML
        prompt = prompt_manager.get_prompt(data['prompt_id'])
        parameters = data.get('parameters', {})
        
        # Add schema information if needed
        if data.get('include_schema', False):
            schema_info = db_utils.get_schema_info()
            parameters['schema'] = schema_info
        
        # Process the prompt with provided parameters
        processed_prompt = prompt_manager.process_prompt(prompt, parameters)
        
        # Get response from LLM
        response = mcp_client.analyze(
            prompt=processed_prompt,
            provider=data.get('provider', llm_config.get('DEFAULT_PROVIDER', 'openai')),
            model=data.get('model', llm_config.get('DEFAULT_MODEL', 'gpt-3.5-turbo')),
            max_tokens=llm_config.get('MAX_TOKENS', 2000)
        )
        
        return jsonify({
            'status': 'success',
            'analysis': response
        })
    except XMLParseError as e:
        return create_error_response('Invalid prompt XML format', 400, e, 'XMLError')
    except ValueError as e:
        return create_error_response(str(e), 400, e, 'ValidationError')
    except Exception as e:
        return create_error_response('Analysis failed', 500, e, 'ProcessingError')

@llm_bp.route('/config', methods=['GET'])
def get_config():
    """Get current LLM configuration"""
    try:
        config = llm_config.get_config()
        return jsonify({
            'status': 'success',
            'config': config
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@llm_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get available LLM providers and their status"""
    try:
        providers = mcp_client.get_available_providers()
        return jsonify({
            'status': 'success',
            'providers': providers
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Register the blueprint with the app
app.register_blueprint(llm_bp, url_prefix='/api/llm')

