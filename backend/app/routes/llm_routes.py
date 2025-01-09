from flask import Blueprint, jsonify, request, current_app
from ..utils.extensions import app
from ..llm.prompts import PromptManager
from ..llm.config import LLMConfig
from ..llm.mcp import MCPClient
import os
import xml.etree.ElementTree as ET

llm_bp = Blueprint('llm', __name__)

# Initialize services
llm_config = LLMConfig()
prompt_manager = PromptManager()
mcp_client = MCPClient(llm_config)

def create_error_response(message, status_code=500, details=None):
    response = {
        "error": message,
        "status": status_code
    }
    if details and current_app.debug:
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
        provider = data.get('provider', 'openai')
        model = data.get('model', 'gpt-3.5-turbo')
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
        return jsonify({
            'status': 'error',
            'message': 'No prompt ID provided'
        }), 400
    
    try:
        prompt = prompt_manager.get_prompt(data['prompt_id'])
        parameters = data.get('parameters', {})
        
        # Process the prompt with provided parameters
        processed_prompt = prompt_manager.process_prompt(prompt, parameters)
        
        # Get response from LLM
        response = mcp_client.analyze(
            prompt=processed_prompt,
            provider=data.get('provider', 'openai'),
            model=data.get('model', 'gpt-3.5-turbo')
        )
        
        return jsonify({
            'status': 'success',
            'analysis': response
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

