# pages/article_draft.py
import streamlit as st
import asyncio
from typing import Dict, Any, Optional
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
from datetime import datetime
import logging
import json
import yaml

logger = logging.getLogger(__name__)

class ArticleDraftGenerator:
    """Handles article draft generation and validation"""
    
    ARTICLE_TYPES = {
        "informative": "Educational content",
        "analytical": "In-depth analysis",
        "case_study": "Real-world examples",
        "how_to": "Practical guides"
    }
    
    DEFAULT_STRUCTURE = {
        "introduction": {
            "key_points": [
                "Hook the reader with a compelling opening",
                "Introduce the workplace issue or challenge",
                "Establish Fairness Factor's expertise"
            ]
        },
        "problem_statement": {
            "key_points": [
                "Define the workplace challenge",
                "Present relevant statistics or examples",
                "Explain impact on employees"
            ]
        },
        "solution": {
            "key_points": [
                "Introduce Fairness Factor's approach",
                "Highlight unique value proposition",
                "Explain methodology"
            ]
        },
        "benefits": {
            "employees": [
                "Improved workplace rights",
                "Better work environment",
                "Professional growth opportunities"
            ],
            "employers": [
                "Enhanced compliance",
                "Improved employee relations",
                "Reduced legal risks"
            ]
        },
        "case_study": {
            "elements": [
                "Real-world example",
                "Challenge faced",
                "Solution implemented",
                "Results achieved"
            ]
        },
        "conclusion": {
            "elements": [
                "Summarize key points",
                "Reinforce Fairness Factor's value",
                "Call to action"
            ]
        }
    }
    
    @staticmethod
    def validate_draft(draft: str) -> bool:
        """Validate article draft"""
        if not draft or len(draft.strip()) < 500:
            return False
        return True

async def generate_draft(
    topic: str,
    article_type: str,
    structure: Dict[str, Any],
    research_analysis: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate article draft asynchronously"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Format draft prompt
        draft_prompt = await prompt_handler.format_prompt(
            'article_draft',
            {
                'selected_topic': topic,
                'article_type': article_type,
                'article_structure': json.dumps(structure, indent=2),
                'research_analysis': research_analysis
            }
        )
        
        if not draft_prompt:
            raise ValueError("Failed to format draft prompt")

        # Generate draft
        draft = await llm_client.generate_response(
            system_prompt=(
                "You are an expert content writer for Fairness Factor, creating "
                f"engaging {article_type} articles about employee rights and workplace "
                "advocacy. Maintain a professional yet approachable tone, emphasizing "
                "Fairness Factor's expertise and commitment to employee advocacy."
            ),
            user_prompt=draft_prompt,
            max_tokens=2000,
            user_email=user_email
        )
        
        if not ArticleDraftGenerator.validate_draft(draft):
            raise ValueError("Generated draft does not meet minimum requirements")
        
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
    """Article Draft Page Handler"""
    try:
        # Check user authentication
        if 'user' not in st.session_state or not st.session_state.user:
            st.warning("Please log in to access this page.")
            return

        user_email = st.session_state.user['email']
        
        st.title("Generate Fairness Factor Blog Article Draft")
        
        # Check prerequisites
        if 'topic_campaign' not in st.session_state or 'selected_topic' not in st.session_state:
            st.warning("⚠️ Please complete the Topic Campaign step first.")
            return
        
        # Display previous content
        with st.expander("📊 Campaign Overview", expanded=False):
            st.write(st.session_state['topic_campaign'])
            st.write("### Selected Topic")
            st.write(st.session_state['selected_topic'])
        
        # Article settings
        st.write("### 📝 Article Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            article_type = st.selectbox(
                "Article Type:",
                list(ArticleDraftGenerator.ARTICLE_TYPES.keys()),
                format_func=lambda x: ArticleDraftGenerator.ARTICLE_TYPES[x],
                help="Select the type of article"
            )
            
            target_length = st.slider(
                "Target Word Count:",
                min_value=500,
                max_value=3000,
                value=1500,
                step=100,
                help="Select target article length"
            )
        
        with col2:
            tone_options = {
                "professional": "Formal and authoritative",
                "conversational": "Friendly and approachable",
                "balanced": "Professional yet accessible",
                "educational": "Instructive and informative"
            }
            
            tone = st.selectbox(
                "Writing Tone:",
                list(tone_options.keys()),
                format_func=lambda x: tone_options[x],
                help="Select the writing tone"
            )
            
            expertise_level = st.select_slider(
                "Expertise Level:",
                options=["Beginner", "Intermediate", "Advanced", "Expert"],
                value="Intermediate",
                help="Select content expertise level"
            )
        
        # Article structure editor
        st.write("### 📋 Article Structure")
        
        # Load default or existing structure
        default_structure = ArticleDraftGenerator.DEFAULT_STRUCTURE
        current_structure = st.session_state.get('article_structure', default_structure)
        
        structure_json = st.text_area(
            "Edit article structure (JSON format):",
            value=json.dumps(current_structure, indent=2),
            height=300,
            help="Customize the article structure"
        )
        
        try:
            article_structure = json.loads(structure_json)
            st.session_state['article_structure'] = article_structure
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON structure. Please check the format.")
            return
        
        # Generate draft
        if st.button("✍️ Generate Draft", help="Click to generate article draft"):
            with st.spinner("Generating article draft..."):
                try:
                    result = await generate_draft(
                        topic=st.session_state['selected_topic'],
                        article_type=article_type,
                        structure=article_structure,
                        research_analysis=st.session_state['research_analysis'],
                        llm_client=llm_client,
                        prompt_handler=prompt_handler,
                        user_email=user_email
                    )
                    
                    if result['success']:
                        # Save draft content
                        content_id = await db_handlers['blog'].save_content(
                            user_email=user_email,
                            content_type='draft',
                            content=result['draft'],
                            metadata={
                                'topic': st.session_state['selected_topic'],
                                'article_type': article_type,
                                'structure': article_structure,
                                'target_length': target_length,
                                'tone': tone,
                                'expertise_level': expertise_level,
                                'campaign_id': st.session_state.get('campaign_id'),
                                'research_id': st.session_state.get('research_id')
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
                                'article_type': article_type
                            }
                        )
                        
                        # Display draft
                        st.success("✅ Draft generated successfully!")
                        
                        # Draft sections
                        st.write("### 📄 Article Draft")
                        sections = result['draft'].split('\n\n')
                        
                        for i, section in enumerate(sections):
                            with st.expander(f"Section {i+1}", expanded=i==0):
                                st.write(section)
                                
                                # Section feedback
                                feedback = st.text_area(
                                    "Section Feedback:",
                                    key=f"feedback_{i}",
                                    help="Add notes or feedback for this section"
                                )
                                if feedback:
                                    st.session_state.setdefault('section_feedback', {})[i] = feedback
                        
                        # Draft actions
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("📝 Edit Draft"):
                                st.session_state['editing_mode'] = True
                                st.experimental_rerun()
                        
                        with col2:
                            # Export as Markdown
                            if st.button("📥 Export as Markdown"):
                                markdown_content = f"""---
title: {st.session_state['selected_topic']}
author: {st.session_state.user['name']}
date: {datetime.now().strftime('%Y-%m-%d')}
type: {article_type}
expertise_level: {expertise_level}
---

{result['draft']}
"""
                                st.download_button(
                                    label="💾 Download Markdown",
                                    data=markdown_content,
                                    file_name=f"draft_{content_id}.md",
                                    mime="text/markdown"
                                )
                        
                        with col3:
                            # Export as JSON
                            if st.button("📤 Export as JSON"):
                                export_data = {
                                    'metadata': {
                                        'topic': st.session_state['selected_topic'],
                                        'author': st.session_state.user['name'],
                                        'date': datetime.now().isoformat(),
                                        'article_type': article_type,
                                        'tone': tone,
                                        'expertise_level': expertise_level
                                    },
                                    'structure': article_structure,
                                    'content': result['draft'],
                                    'feedback': st.session_state.get('section_feedback', {})
                                }
                                
                                st.download_button(
                                    label="💾 Download JSON",
                                    data=json.dumps(export_data, indent=2),
                                    file_name=f"draft_{content_id}.json",
                                    mime="application/json"
                                )
                        
                    else:
                        st.error(f"❌ Draft generation failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    logger.error(f"Error in draft generation: {str(e)}")
        
        # Draft history
        with st.expander("📚 Draft History", expanded=False):
            try:
                draft_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='draft',
                    limit=5
                )
                
                if draft_history:
                    for entry in draft_history:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"Draft: {entry['metadata'].get('topic', 'Untitled')}")
                            st.write(f"Created: {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                        with col2:
                            if st.button("Load", key=f"load_{entry['_id']}"):
                                st.session_state['article_draft'] = entry['content']
                                st.session_state['draft_id'] = str(entry['_id'])
                                st.experimental_rerun()
                                
                        with col3:
                            if st.button("Delete", key=f"delete_{entry['_id']}"):
                                try:
                                    await db_handlers['blog'].delete_content(str(entry['_id']))
                                    st.success("✅ Draft deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting draft: {str(e)}")
                        
                        st.markdown("---")
                else:
                    st.info("No previous drafts found.")
                    
            except Exception as e:
                st.error("Failed to load draft history")
                logger.error(f"Error loading draft history: {str(e)}")

        # Help section
        with st.expander("❓ Need Help?", expanded=False):
            st.markdown("""
            ### Writing Guidelines
            1. Start with a strong hook
            2. Use clear, concise language
            3. Include relevant examples
            4. Support claims with data
            5. Maintain consistent tone
            
            ### Structure Tips
            - Use short paragraphs
            - Include subheadings
            - Add transition sentences
            - End with clear CTA
            
            ### Best Practices
            - Research thoroughly
            - Write for your audience
            - Include expert insights
            - Proofread carefully
            
            ### Support
            Contact: content@fairnessfactor.com
            """)

    except Exception as e:
        logger.error(f"Error in article draft page: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    # For testing the page individually
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test_page():
        from utils.mongo_manager import AsyncMongoManager
        from utils.prompt_handler import AsyncPromptHandler
        from llm.llm_client import AsyncLLMClient
        
        mongo_manager = AsyncMongoManager()
        client, db = await mongo_manager.get_connection()
        
        handlers = {
            'blog': None,  # Add your handlers here
            'file': None,
            'analytics': None
        }
        
        await article_draft_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())