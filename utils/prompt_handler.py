# utils/prompt_handler.py
import os
from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AsyncPromptHandler:
    def __init__(self, db):
        self.db = db
        self.prompts_collection = db.prompts

    async def load_prompt(self, prompt_name: str) -> Optional[str]:
        """Load prompt template from database or file system"""
        try:
            # Try to load from database first
            prompt_doc = await self.prompts_collection.find_one({'name': prompt_name})
            if prompt_doc:
                return prompt_doc['content']

            # Fall back to file system
            prompt_path = f"prompts/{prompt_name}.txt"
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r') as f:
                    content = f.read()
                    # Store in database for future use
                    await self.prompts_collection.insert_one({
                        'name': prompt_name,
                        'content': content,
                        'created_at': datetime.now()
                    })
                    return content
            
            raise FileNotFoundError(f"Prompt template {prompt_name} not found")
            
        except Exception as e:
            logger.error(f"Error loading prompt {prompt_name}: {str(e)}")
            return None

    async def format_prompt(
        self, 
        prompt_name: str, 
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """Load and format prompt template with variables"""
        try:
            template = await self.load_prompt(prompt_name)
            if not template:
                return None

            # Format prompt with variables
            formatted_prompt = template
            for key, value in variables.items():
                formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))

            return formatted_prompt

        except Exception as e:
            logger.error(f"Error formatting prompt {prompt_name}: {str(e)}")
            return None

    async def save_prompt_history(
        self, 
        prompt_name: str, 
        variables: Dict[str, Any], 
        formatted_prompt: str,
        user_email: str
    ) -> Optional[str]:
        """Save prompt usage history"""
        try:
            result = await self.db.prompt_history.insert_one({
                'prompt_name': prompt_name,
                'variables': variables,
                'formatted_prompt': formatted_prompt,
                'user_email': user_email,
                'timestamp': datetime.now()
            })
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving prompt history: {str(e)}")
            return None