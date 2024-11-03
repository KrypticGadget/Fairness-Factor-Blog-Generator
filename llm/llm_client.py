# llm/llm_client.py

import os
import anthropic
import asyncio
from dotenv import load_dotenv
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from utils.mongo_manager import AsyncMongoManager, get_db_session, ensure_event_loop

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class AsyncLLMClient:
    """
    Asynchronous LLM Client for handling interactions with Anthropic's Claude API
    """
    
    def __init__(self, model: str = "claude-3-opus-20240229", temperature: float = 0.5):
        """
        Initialize the LLM client
        
        Args:
            model (str): Model identifier to use for generation
            temperature (float): Temperature setting for generation (0.0-1.0)
        """
        self.model = model
        self.temperature = temperature
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key is None:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        # Initialize Anthropic client
        ensure_event_loop()  # Ensure event loop exists
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        
        # Initialize request tracking
        self.total_requests = 0
        self.failed_requests = 0

    async def log_llm_request(self, request_data: Dict[str, Any]) -> str:
        """
        Log LLM request details to MongoDB
        
        Args:
            request_data (Dict[str, Any]): Request data to log
            
        Returns:
            str: ID of the logged request
        """
        try:
            async with get_db_session() as (_, db, _):
                result = await db.llm_logs.insert_one({
                    **request_data,
                    'timestamp': datetime.now(),
                    'model': self.model,
                    'temperature': self.temperature
                })
                return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to log LLM request: {str(e)}")
            return None

    async def update_log(self, log_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing log entry
        
        Args:
            log_id (str): ID of the log entry to update
            update_data (Dict[str, Any]): Data to update in the log
            
        Returns:
            bool: Success status of the update operation
        """
        try:
            async with get_db_session() as (_, db, _):
                await db.llm_logs.update_one(
                    {'_id': log_id},
                    {'$set': {
                        **update_data,
                        'updated_at': datetime.now()
                    }}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to update log: {str(e)}")
            return False

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        user_email: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Generate a response using the LLM
        
        Args:
            system_prompt (str): System context for the generation
            user_prompt (str): User prompt for generation
            max_tokens (int): Maximum tokens to generate
            user_email (Optional[str]): Email of the requesting user
            request_metadata (Optional[Dict[str, Any]]): Additional metadata for the request
            
        Returns:
            Optional[str]: Generated response or None if generation fails
        """
        try:
            logger.info(f"Sending prompt to {self.model}...")
            self.total_requests += 1

            # Prepare request data for logging
            request_data = {
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'max_tokens': max_tokens,
                'user_email': user_email,
                'metadata': request_metadata or {},
                'status': 'pending'
            }
            
            # Log the request
            log_id = await self.log_llm_request(request_data)

            # Generate response
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                }]
            )

            result = response.content[0].text
            logger.info(f"LLM Response received for log_id: {log_id}")

            # Update log with success
            await self.update_log(log_id, {
                'response': result,
                'status': 'completed',
                'token_count': len(result.split()),  # Rough estimate
                'completed_at': datetime.now()
            })

            return result

        except Exception as e:
            self.failed_requests += 1
            logger.error(f"LLM error: {str(e)}")
            
            # Update log with error
            if 'log_id' in locals():
                await self.update_log(log_id, {
                    'error': str(e),
                    'status': 'failed',
                    'completed_at': datetime.now()
                })
            
            return None

    async def generate_batch_responses(
        self,
        prompts: List[Dict[str, str]],
        user_email: Optional[str] = None,
        batch_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Optional[str]]:
        """
        Generate multiple responses concurrently
        
        Args:
            prompts (List[Dict[str, str]]): List of prompt dictionaries
            user_email (Optional[str]): Email of the requesting user
            batch_metadata (Optional[Dict[str, Any]]): Additional metadata for the batch
            
        Returns:
            List[Optional[str]]: List of generated responses
        """
        tasks = []
        for idx, prompt in enumerate(prompts):
            request_metadata = {
                **(batch_metadata or {}),
                'batch_index': idx,
                'batch_size': len(prompts)
            }
            
            task = asyncio.create_task(
                self.generate_response(
                    prompt.get('system_prompt', ''),
                    prompt.get('user_prompt', ''),
                    prompt.get('max_tokens', 1000),
                    user_email,
                    request_metadata
                )
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the client
        
        Returns:
            Dict[str, Any]: Usage statistics
        """
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (
                ((self.total_requests - self.failed_requests) / self.total_requests * 100)
                if self.total_requests > 0 else 0
            )
        }

# Create singleton manager
_llm_client_instance = None

def get_llm_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None
) -> AsyncLLMClient:
    """
    Get or create LLM client instance
    
    Args:
        model (Optional[str]): Override default model
        temperature (Optional[float]): Override default temperature
        
    Returns:
        AsyncLLMClient: LLM client instance
    """
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = AsyncLLMClient(
            model=model or "claude-3-opus-20240229",
            temperature=temperature or 0.5
        )
    return _llm_client_instance