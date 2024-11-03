# llm/article_draft.py

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_article_draft(
    topic: str,
    structure: str,
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """
    Generate article draft based on selected topic and structure
    
    Args:
        topic (str): Selected topic for the article
        structure (str): Proposed article structure
        llm_client (Any): LLM client instance for generating responses
        prompt_handler (Any): Handler for managing prompts
        user_email (str): Email of the user making the request
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing draft content or error information
    """
    try:
        logger.info("Generating article draft...")
        
        # Format article draft prompt
        draft_prompt = await prompt_handler.format_prompt(
            'article_draft',
            {
                'selected_topic': topic,
                'article_structure': structure
            }
        )
        
        if not draft_prompt:
            raise ValueError("Failed to format draft prompt")
            
        # Generate draft using LLM
        draft_content = await llm_client.generate_response(
            system_prompt=(
                "You are an AI assistant for Fair Fight, tasked with generating "
                "blog article drafts on employee rights and workplace issues. "
                "Your goal is to create informative, engaging content that helps "
                "employees understand their rights while providing practical guidance."
            ),
            user_prompt=draft_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        logger.info("Article draft generation complete.")
        
        return {
            'success': True,
            'draft': draft_content
        }
        
    except Exception as e:
        logger.error(f"Error generating article draft: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }