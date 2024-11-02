# pages/editing_criteria.py
import streamlit as st
import asyncio
from typing import Dict, Any, List
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging

logger = logging.getLogger(__name__)

async def generate_editing_suggestions(
    draft: str,
    criteria: Dict[str, str],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate editing suggestions asynchronously"""
    try:
        # Format editing prompt
        editing_prompt = await prompt_handler.format_prompt(
            'editing_criteria',
            {
                'article_draft': draft,
                'editing_criteria': '\n'.join(f"{k}: {v}" for k, v in criteria.items())
            }
        )
        
        if not editing_prompt:
            raise ValueError("Failed to format editing prompt")

        suggestions = await llm_client.generate_response(
            system_prompt="You are an AI editor for Fairness Factor...",
            user_prompt=editing_prompt,
            max_tokens=1500,
            user_email=user_email
        )
        
        return {
            'success': True,
            'suggestions': suggestions
        }
    except Exception as e:
        logger.error(f"Error generating editing suggestions: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def editing_criteria_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    st.title("Fairness Factor Blog Editing Criteria")
    
    user_email = st.session_state.user['email']
    
    if 'article_draft' not in st.session_state:
        st.warning("Please generate an article draft first.")
        return
    
    st.write("Article Draft:")
    st.write(st.session_state['article_draft'])
    
    # Split draft into sections
    sections = st.session_state['article_draft'].split('\n\n')
    
    editing_criteria = {}
    for i, section in enumerate(sections):
        st.subheader(f"Section {i+1}")
        st.write(section)
        criteria = st.text_area(
            f"Editing criteria for Section {i+1}",
            "Improve clarity, add more details about Fairness Factor's solution, include relevant statistics",
            key=f"criteria_{i}"
        )
        editing_criteria[f"Section {i+1}"] = criteria
    
    if st.button("Generate Editing Suggestions"):
        with st.spinner("Generating editing suggestions..."):
            try:
                result = await generate_editing_suggestions(
                    draft=st.session_state['article_draft'],
                    criteria=editing_criteria,
                    llm_client=llm_client,
                    prompt_handler=prompt_handler,
                    user_email=user_email
                )
                
                if result['success']:
                    # Save editing suggestions
                    content_id = await db_handlers['blog'].save_content(
                        user_email=user_email,
                        content_type='editing_suggestions',
                        content=result['suggestions'],
                        metadata={
                            'draft_id': st.session_state['draft_id'],
                            'criteria': editing_criteria
                        }
                    )
                    
                    # Update session state
                    st.session_state['editing_suggestions'] = result['suggestions']
                    st.session_state['editing_id'] = content_id
                    
                    # Log activity
                    await db_handlers['analytics'].log_activity(
                        user_email=user_email,
                        activity_type='editing_suggestions',
                        metadata={'content_id': content_id}
                    )
                    
                    st.write("Editing Suggestions:")
                    st.write(result['suggestions'])
                else:
                    st.error(f"Failed to generate editing suggestions: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in editing suggestions: {str(e)}")