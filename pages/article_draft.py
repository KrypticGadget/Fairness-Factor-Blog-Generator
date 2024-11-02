# pages/article_draft.py
import streamlit as st
import asyncio
from typing import Dict, Any, Optional
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging

logger = logging.getLogger(__name__)

async def generate_draft(
    topic: str,
    structure: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate article draft asynchronously"""
    try:
        # Format draft prompt
        draft_prompt = await prompt_handler.format_prompt(
            'article_draft',
            {
                'selected_topic': topic,
                'article_structure': structure
            }
        )
        
        if not draft_prompt:
            raise ValueError("Failed to format draft prompt")

        # Generate draft
        draft = await llm_client.generate_response(
            system_prompt="You are an AI assistant for Fairness Factor, drafting blog articles...",
            user_prompt=draft_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'draft': draft
        }
    except Exception as e:
        logger.error(f"Error generating draft: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def article_draft_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    st.title("Generate Fairness Factor Blog Article Draft")
    
    user_email = st.session_state.user['email']
    
    if 'research_analysis' not in st.session_state:
        st.warning("Please complete the Topic Research step first.")
        return
        
    st.write("Research Analysis:")
    st.write(st.session_state['research_analysis'])
    
    # Article structure template
    default_structure = """
    1. Introduction
    2. The Challenge
    3. Fairness Factor's Solution
    4. Benefits for Employees
    5. Benefits for Employers
    6. Case Study or Example
    7. Conclusion and Call to Action
    """
    
    article_structure = st.text_area(
        "Edit the article structure if needed:",
        value=default_structure,
        height=300,
        key="article_structure"
    )
    
    topic = st.text_input(
        "Enter the article topic:",
        key="article_topic"
    )
    
    if st.button("Generate Article Draft"):
        with st.spinner("Generating article draft..."):
            try:
                # Generate draft
                result = await generate_draft(
                    topic=topic,
                    structure=article_structure,
                    llm_client=llm_client,
                    prompt_handler=prompt_handler,
                    user_email=user_email
                )
                
                if result['success']:
                    # Save draft content
                    content_id = await db_handlers['blog'].save_article_draft(
                        user_email=user_email,
                        research_id=st.session_state['research_id'],
                        content=result['draft'],
                        metadata={
                            'topic': topic,
                            'structure': article_structure
                        }
                    )
                    
                    # Update session state
                    st.session_state['article_draft'] = result['draft']
                    st.session_state['draft_id'] = content_id
                    
                    # Log activity
                    await db_handlers['analytics'].log_activity(
                        user_email=user_email,
                        activity_type='draft_generation',
                        metadata={
                            'content_id': content_id,
                            'research_id': st.session_state['research_id'],
                            'topic': topic
                        }
                    )
                    
                    # Display draft
                    st.write("Generated Article Draft:")
                    st.write(result['draft'])
                    
                else:
                    st.error(f"Draft generation failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in article draft generation: {str(e)}")

    # Display draft history
    with st.expander("View Draft History"):
        try:
            draft_history = await db_handlers['blog'].get_user_content(
                user_email=user_email,
                content_type='draft',
                limit=5
            )
            
            if draft_history:
                for entry in draft_history:
                    st.write(f"Draft from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    if st.button(f"Load Draft {entry['_id']}", key=f"load_{entry['_id']}"):
                        st.session_state['article_draft'] = entry['content']
                        st.session_state['draft_id'] = str(entry['_id'])
                        st.experimental_rerun()
            else:
                st.info("No previous drafts found.")
                
        except Exception as e:
            st.error("Failed to load draft history")
            logger.error(f"Error loading draft history: {str(e)}")