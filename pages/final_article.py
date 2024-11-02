# pages/final_article.py
import streamlit as st
import asyncio
from typing import Dict, Any
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging

logger = logging.getLogger(__name__)

async def generate_final_article(
    draft: str,
    suggestions: str,
    feedback: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate final article asynchronously"""
    try:
        final_prompt = await prompt_handler.format_prompt(
            'final_article',
            {
                'article_draft': draft,
                'editing_suggestions': suggestions,
                'user_feedback': feedback
            }
        )
        
        if not final_prompt:
            raise ValueError("Failed to format final article prompt")

        final_article = await llm_client.generate_response(
            system_prompt="You are an AI editor finalizing a Fairness Factor blog article...",
            user_prompt=final_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        return {
            'success': True,
            'article': final_article
        }
    except Exception as e:
        logger.error(f"Error generating final article: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def final_article_page(
    db_handlers: Dict[str, Any],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler
):
    st.title("Generate Final Fairness Factor Blog Article")
    
    user_email = st.session_state.user['email']
    
    if 'editing_suggestions' not in st.session_state:
        st.warning("Please complete the Editing Criteria step first.")
        return
    
    st.write("Editing Suggestions:")
    st.write(st.session_state['editing_suggestions'])
    
    user_feedback = st.text_area(
        "Additional feedback for the final article:",
        "Ensure the article highlights Fairness Factor's unique approach to employee advocacy."
    )
    
    if st.button("Generate Final Article"):
        with st.spinner("Generating final article..."):
            try:
                result = await generate_final_article(
                    draft=st.session_state['article_draft'],
                    suggestions=st.session_state['editing_suggestions'],
                    feedback=user_feedback,
                    llm_client=llm_client,
                    prompt_handler=prompt_handler,
                    user_email=user_email
                )
                
                if result['success']:
                    # Save final article
                    content_id = await db_handlers['blog'].save_content(
                        user_email=user_email,
                        content_type='final_article',
                        content=result['article'],
                        metadata={
                            'draft_id': st.session_state['draft_id'],
                            'editing_id': st.session_state['editing_id'],
                            'user_feedback': user_feedback
                        }
                    )
                    
                    # Update session state
                    st.session_state['final_article'] = result['article']
                    st.session_state['final_id'] = content_id
                    
                    # Log activity
                    await db_handlers['analytics'].log_activity(
                        user_email=user_email,
                        activity_type='final_article',
                        metadata={'content_id': content_id}
                    )
                    
                    st.write("Final Article:")
                    st.write(result['article'])
                    
                    if st.button("Save to Output"):
                        try:
                            with open(f"output/final_article_{content_id}.md", "w") as f:
                                f.write(result['article'])
                            st.success("Article saved to output directory")
                        except Exception as e:
                            st.error(f"Error saving file: {str(e)}")
                            
                else:
                    st.error(f"Failed to generate final article: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Error in final article generation: {str(e)}")

    # Display article history
    with st.expander("View Article History"):
        try:
            article_history = await db_handlers['blog'].get_user_content(
                user_email=user_email,
                content_type='final_article',
                limit=5
            )
            
            if article_history:
                for entry in article_history:
                    st.write(f"Article from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    if st.button(f"Load Article {entry['_id']}", key=f"load_{entry['_id']}"):
                        st.session_state['final_article'] = entry['content']
                        st.session_state['final_id'] = str(entry['_id'])
                        st.experimental_rerun()
            else:
                st.info("No previous articles found.")
                
        except Exception as e:
            st.error("Failed to load article history")
            logger.error(f"Error loading article history: {str(e)}")