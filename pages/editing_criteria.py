# pages/editing_criteria.py
import streamlit as st
import asyncio
from typing import Dict, Any, Optional
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class EditingCriteria:
    """Editing criteria categories and defaults"""
    
    TONE_AND_VOICE = {
        "professional": "Maintain professional language while being approachable",
        "brand_voice": "Align with Fairness Factor's advocacy tone",
        "consistency": "Ensure consistent voice throughout the article",
        "engagement": "Keep readers engaged and interested"
    }
    
    CONTENT_QUALITY = {
        "accuracy": "Verify all facts and statistics",
        "clarity": "Ensure clear explanation of complex topics",
        "relevance": "Maintain focus on employee advocacy",
        "evidence": "Support claims with credible sources",
        "completeness": "Cover all essential aspects of the topic"
    }
    
    STRUCTURE = {
        "flow": "Ensure logical progression of ideas",
        "paragraphs": "Maintain appropriate paragraph length",
        "transitions": "Use smooth transitions between sections",
        "hierarchy": "Clear heading structure and organization"
    }
    
    SEO_OPTIMIZATION = {
        "keywords": "Include relevant keywords naturally",
        "readability": "Optimize for web reading",
        "headers": "Use proper header hierarchy",
        "meta_elements": "Optimize title and meta description"
    }
    
    LEGAL_COMPLIANCE = {
        "accuracy": "Ensure legal information is accurate",
        "disclaimers": "Include necessary disclaimers",
        "citations": "Properly cite legal sources",
        "currency": "Verify information is up-to-date"
    }

async def generate_editing_suggestions(
    draft: str,
    criteria: Dict[str, Dict[str, str]],
    section_feedback: Dict[int, str],
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate editing suggestions based on criteria"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Format editing prompt
        editing_prompt = await prompt_handler.format_prompt(
            'editing_criteria',
            {
                'article_draft': draft,
                'editing_criteria': json.dumps(criteria, indent=2),
                'section_feedback': json.dumps(section_feedback, indent=2)
            }
        )
        
        if not editing_prompt:
            raise ValueError("Failed to format editing prompt")

        # Generate suggestions
        suggestions = await llm_client.generate_response(
            system_prompt=(
                "You are an expert editor for Fairness Factor, providing detailed "
                "suggestions to improve blog articles. Focus on maintaining professional "
                "tone while ensuring content is engaging and aligned with Fairness "
                "Factor's mission of employee advocacy."
            ),
            user_prompt=editing_prompt,
            max_tokens=2000,
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
    """Editing Criteria Page Handler"""
    try:
        # Check user authentication
        if 'user' not in st.session_state or not st.session_state.user:
            st.warning("Please log in to access this page.")
            return

        user_email = st.session_state.user['email']
        
        st.title("Fairness Factor Blog Editing Criteria")
        
        # Check prerequisites
        if 'article_draft' not in st.session_state:
            st.warning("⚠️ Please generate an article draft first.")
            return
        
        # Display draft
        with st.expander("📄 Article Draft", expanded=False):
            st.write(st.session_state['article_draft'])
        
        # Editing criteria sections
        st.write("### 📝 Editing Criteria")
        
        editing_criteria = {}
        section_feedback = {}
        
        # Tabs for different criteria categories
        tabs = st.tabs([
            "Tone & Voice",
            "Content Quality",
            "Structure",
            "SEO Optimization",
            "Legal Compliance",
            "Custom Criteria"
        ])
        
        # Tone & Voice
        with tabs[0]:
            st.markdown("#### Tone and Voice Criteria")
            editing_criteria['tone_and_voice'] = {}
            
            for key, default in EditingCriteria.TONE_AND_VOICE.items():
                value = st.text_area(
                    f"{key.replace('_', ' ').title()}:",
                    value=default,
                    key=f"tone_{key}",
                    help=f"Edit criteria for {key.replace('_', ' ')}"
                )
                editing_criteria['tone_and_voice'][key] = value
        
        # Content Quality
        with tabs[1]:
            st.markdown("#### Content Quality Criteria")
            editing_criteria['content_quality'] = {}
            
            for key, default in EditingCriteria.CONTENT_QUALITY.items():
                value = st.text_area(
                    f"{key.replace('_', ' ').title()}:",
                    value=default,
                    key=f"quality_{key}",
                    help=f"Edit criteria for {key.replace('_', ' ')}"
                )
                editing_criteria['content_quality'][key] = value
        
        # Structure
        with tabs[2]:
            st.markdown("#### Structure Criteria")
            editing_criteria['structure'] = {}
            
            for key, default in EditingCriteria.STRUCTURE.items():
                value = st.text_area(
                    f"{key.replace('_', ' ').title()}:",
                    value=default,
                    key=f"structure_{key}",
                    help=f"Edit criteria for {key.replace('_', ' ')}"
                )
                editing_criteria['structure'][key] = value
        
        # SEO Optimization
        with tabs[3]:
            st.markdown("#### SEO Optimization Criteria")
            editing_criteria['seo_optimization'] = {}
            
            for key, default in EditingCriteria.SEO_OPTIMIZATION.items():
                value = st.text_area(
                    f"{key.replace('_', ' ').title()}:",
                    value=default,
                    key=f"seo_{key}",
                    help=f"Edit criteria for {key.replace('_', ' ')}"
                )
                editing_criteria['seo_optimization'][key] = value
        
        # Legal Compliance
        with tabs[4]:
            st.markdown("#### Legal Compliance Criteria")
            editing_criteria['legal_compliance'] = {}
            
            for key, default in EditingCriteria.LEGAL_COMPLIANCE.items():
                value = st.text_area(
                    f"{key.replace('_', ' ').title()}:",
                    value=default,
                    key=f"legal_{key}",
                    help=f"Edit criteria for {key.replace('_', ' ')}"
                )
                editing_criteria['legal_compliance'][key] = value
        
        # Custom Criteria
        with tabs[5]:
            st.markdown("#### Custom Criteria")
            custom_criteria = st.text_area(
                "Add any additional editing criteria:",
                value="",
                height=200,
                help="Enter any custom editing criteria not covered above"
            )
            if custom_criteria:
                editing_criteria['custom'] = {'additional': custom_criteria}
        
        # Section-specific feedback
        st.write("### 📑 Section-Specific Feedback")
        sections = st.session_state['article_draft'].split('\n\n')
        
        for i, section in enumerate(sections):
            with st.expander(f"Section {i+1}", expanded=False):
                st.write(section)
                feedback = st.text_area(
                    "Feedback for this section:",
                    key=f"section_feedback_{i}",
                    help="Enter specific feedback for this section"
                )
                if feedback:
                    section_feedback[i] = feedback
        
        # Generate suggestions
        if st.button("🔍 Generate Editing Suggestions", help="Click to generate editing suggestions"):
            with st.spinner("✍️ Generating editing suggestions..."):
                try:
                    result = await generate_editing_suggestions(
                        draft=st.session_state['article_draft'],
                        criteria=editing_criteria,
                        section_feedback=section_feedback,
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
                                'criteria': editing_criteria,
                                'section_feedback': section_feedback,
                                'generated_at': datetime.now().isoformat()
                            }
                        )
                        
                        # Update session state
                        st.session_state['editing_suggestions'] = result['suggestions']
                        st.session_state['editing_id'] = content_id
                        
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            user_email=user_email,
                            activity_type='editing_suggestions',
                            metadata={
                                'content_id': content_id,
                                'draft_id': st.session_state['draft_id']
                            }
                        )
                        
                        # Display suggestions
                        st.success("✅ Editing suggestions generated successfully!")
                        
                        # Suggestions display
                        st.write("### 📋 Editing Suggestions")
                        suggestions_sections = result['suggestions'].split('\n\n')
                        
                        for i, suggestion in enumerate(suggestions_sections):
                            with st.expander(f"Suggestion {i+1}", expanded=i==0):
                                st.write(suggestion)
                                
                                # Implementation status
                                status = st.selectbox(
                                    "Implementation Status:",
                                    ["Pending", "In Progress", "Implemented", "Rejected"],
                                    key=f"status_{i}"
                                )
                                if status != "Pending":
                                    st.session_state.setdefault('implementation_status', {})[i] = status
                                
                                # Feedback on suggestion
                                feedback = st.text_area(
                                    "Feedback on this suggestion:",
                                    key=f"suggestion_feedback_{i}"
                                )
                                if feedback:
                                    st.session_state.setdefault('suggestion_feedback', {})[i] = feedback
                        
                        # Export suggestions
                        if st.button("📤 Export Editing Package"):
                            export_data = {
                                'original_draft': st.session_state['article_draft'],
                                'editing_criteria': editing_criteria,
                                'suggestions': result['suggestions'],
                                'section_feedback': section_feedback,
                                'implementation_status': st.session_state.get('implementation_status', {}),
                                'suggestion_feedback': st.session_state.get('suggestion_feedback', {}),
                                'metadata': {
                                    'generated_at': datetime.now().isoformat(),
                                    'draft_id': st.session_state['draft_id']
                                }
                            }
                            
                            st.download_button(
                                label="📥 Download Editing Package",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"editing_suggestions_{content_id}.json",
                                mime="application/json"
                            )
                        
                    else:
                        st.error(f"❌ Failed to generate suggestions: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    logger.error(f"Error in editing suggestions generation: {str(e)}")
        
        # Suggestions history
        with st.expander("📚 Editing History", expanded=False):
            try:
                suggestions_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='editing_suggestions',
                    limit=5
                )
                
                if suggestions_history:
                    for entry in suggestions_history:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"Suggestions from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                        with col2:
                            if st.button("Load", key=f"load_{entry['_id']}"):
                                st.session_state['editing_suggestions'] = entry['content']
                                st.session_state['editing_id'] = str(entry['_id'])
                                st.experimental_rerun()
                                
                        with col3:
                            if st.button("Delete", key=f"delete_{entry['_id']}"):
                                try:
                                    await db_handlers['blog'].delete_content(str(entry['_id']))
                                    st.success("✅ Suggestions deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting suggestions: {str(e)}")
                        
                        st.markdown("---")
                else:
                    st.info("No previous editing suggestions found.")
                    
            except Exception as e:
                st.error("Failed to load editing history")
                logger.error(f"Error loading editing history: {str(e)}")

        # Help section
        with st.expander("❓ Need Help?", expanded=False):
            st.markdown("""
            ### Editing Guidelines
            1. Focus on clarity and consistency
            2. Ensure brand voice alignment
            3. Verify all facts and statistics
            4. Optimize for readability
            5. Maintain professional tone
            
            ### Best Practices
            - Review each section carefully
            - Consider reader perspective
            - Check for logical flow
            - Verify source citations
            - Ensure legal accuracy
            
            ### Support
            Contact: editing@fairnessfactor.com
            """)

    except Exception as e:
        logger.error(f"Error in editing criteria page: {str(e)}")
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
        
        await editing_criteria_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())