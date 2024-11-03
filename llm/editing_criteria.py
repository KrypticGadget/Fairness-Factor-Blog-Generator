# llm/editing_criteria.py

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_editing_suggestions(
    draft: str,
    criteria: Dict[str, Any],
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """
    Generate editing suggestions based on provided criteria and article draft
    
    Args:
        draft (str): The article draft content to be reviewed
        criteria (Dict[str, Any]): Dictionary containing editing criteria and guidelines
        llm_client (Any): LLM client instance for generating responses
        prompt_handler (Any): Handler for managing prompts
        user_email (str): Email of the user making the request
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing editing suggestions or error information
    """
    try:
        logger.info("Generating editing suggestions...")
        
        # Format editing criteria prompt
        editing_prompt = await prompt_handler.format_prompt(
            'editing_criteria',
            {
                'article_draft': draft,
                'editing_criteria': criteria
            }
        )
        
        if not editing_prompt:
            raise ValueError("Failed to format editing prompt")
            
        # Generate suggestions using LLM
        suggestions = await llm_client.generate_response(
            system_prompt=(
                "You are an AI assistant for Fair Fight, tasked with providing "
                "editing suggestions for blog articles. Your role is to ensure content "
                "is clear, accurate, engaging, and aligns with Fair Fight's mission "
                "of empowering employees and promoting workplace fairness. Focus on "
                "both technical accuracy and accessibility for a general audience."
            ),
            user_prompt=editing_prompt,
            max_tokens=1500,
            user_email=user_email
        )
        
        logger.info("Editing suggestions generation complete.")
        
        return {
            'success': True,
            'suggestions': suggestions,
            'criteria_applied': list(criteria.keys())  # Track which criteria were applied
        }
        
    except Exception as e:
        logger.error(f"Error generating editing suggestions: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }