from flask import Blueprint, jsonify, request, current_app
import os
import json
from pathlib import Path

llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')

# Sample data for development
SAMPLE_PROMPTS = {
    "general": {"id": "general", "name": "General Query", "description": "General purpose query template"},
    "analysis": {"id": "analysis", "name": "Data Analysis", "description": "Template for data analysis tasks"}
}

SAMPLE_MODELS = {
    "gpt-3.5-turbo": {"name": "GPT-3.5 Turbo", "provider": "openai", "capabilities": ["chat", "completion"]},
    "gpt-4": {"name": "GPT-4", "provider": "openai", "capabilities": ["chat", "completion", "analysis"]}
}

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
        return jsonify({
            'status': 'success',
            'prompts': SAMPLE_PROMPTS
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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
    """Handle chat interactions"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({
            'status': 'error',
            'message': 'No message provided'
        }), 400
    
    try:
        # Mock response for development
        return jsonify({
            'status': 'success',
            'response': {
                'message': f"Echo: {data['message']}",
                'model': data.get('model', 'gpt-3.5-turbo')
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
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

@llm_bp.route('/models', methods=['GET'])
def get_models():
    """Get available models with their capabilities"""
    try:
        return jsonify({
            'status': 'success',
            'models': SAMPLE_MODELS,
            'default_model': 'gpt-3.5-turbo'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

