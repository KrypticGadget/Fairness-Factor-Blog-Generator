# llm/llm_client.py
import os
import anthropic
import asyncio
from dotenv import load_dotenv
import logging
from typing import Optional, List, Dict
from utils.mongo_manager import AsyncMongoManager

load_dotenv()
logger = logging.getLogger(__name__)

class AsyncLLMClient:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key is None:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.mongo_manager = AsyncMongoManager()

    async def log_llm_request(self, request_data: Dict) -> str:
        """Log LLM request to MongoDB"""
        _, db = await self.mongo_manager.get_connection()
        result = await db.llm_logs.insert_one({
            **request_data,
            'timestamp': datetime.now()
        })
        return str(result.inserted_id)

    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_tokens: int = 1000,
        user_email: Optional[str] = None
    ) -> Optional[str]:
        try:
            logger.info("Sending prompt to LLM...")
            
            # Log request
            request_data = {
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'max_tokens': max_tokens,
                'user_email': user_email
            }
            log_id = await self.log_llm_request(request_data)
            
            response = await self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=max_tokens,
                temperature=0.5,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                }]
            )
            
            result = response.content[0].text
            logger.info(f"LLM Response received for log_id: {log_id}")
            
            # Update log with response
            _, db = await self.mongo_manager.get_connection()
            await db.llm_logs.update_one(
                {'_id': log_id},
                {'$set': {'response': result, 'completed_at': datetime.now()}}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            if log_id:
                _, db = await self.mongo_manager.get_connection()
                await db.llm_logs.update_one(
                    {'_id': log_id},
                    {'$set': {'error': str(e), 'completed_at': datetime.now()}}
                )
            return None

    async def generate_batch_responses(
        self, 
        prompts: List[Dict[str, str]], 
        user_email: Optional[str] = None
    ) -> List[Optional[str]]:
        """Generate multiple responses concurrently"""
        tasks = []
        for prompt in prompts:
            task = asyncio.create_task(
                self.generate_response(
                    prompt['system_prompt'],
                    prompt['user_prompt'],
                    prompt.get('max_tokens', 1000),
                    user_email
                )
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)

llm_client = AsyncLLMClient()