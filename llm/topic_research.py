# llm/topic_research.py

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

async def analyze_research_documents(
    document_contents: List[str],
    llm_client: Any,
    prompt_handler: Any,
    user_email: str
) -> Optional[Dict[str, Any]]:
    """
    Analyze research documents using LLM and return structured analysis.
    
    Args:
        document_contents (List[str]): List of document contents to analyze
        llm_client (Any): LLM client instance for generating responses
        prompt_handler (Any): Handler for managing prompts
        user_email (str): Email of the user making the request
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing analysis results or error information
    """
    try:
        logger.info("Analyzing research documents...")

        # Format research analysis prompt
        research_prompt = await prompt_handler.format_prompt(
            'topic_research',
            {'documents': '\n\n'.join(document_contents)}
        )
        
        if not research_prompt:
            raise ValueError("Failed to format research prompt")

        # Generate analysis using LLM
        analysis_content = await llm_client.generate_response(
            system_prompt=(
                "You are an AI assistant for Fair Fight, a company that provides an innovative "
                "employee benefits package designed to transform workplace dynamics and mitigate "
                "risks for enterprises. Fair Fight empowers employees with knowledge and tools to "
                "address workplace issues while providing enterprises with real-time metrics to "
                "identify and resolve potential problems proactively."
            ),
            user_prompt=research_prompt,
            max_tokens=1000,
            user_email=user_email
        )

        logger.info("Research document analysis complete.")
        
        return {
            'success': True,
            'analysis': analysis_content
        }
        
    except Exception as e:
        logger.error(f"Error analyzing research documents: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }