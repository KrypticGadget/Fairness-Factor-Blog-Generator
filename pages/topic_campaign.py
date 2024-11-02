# pages/topic_campaign.py
import streamlit as st
import asyncio
import json
from typing import Dict, Any, Optional
from llm.llm_client import AsyncLLMClient
from utils.prompt_handler import AsyncPromptHandler
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def check_page_access(page_name: str) -> bool:
    """Check if user has access to requested page"""
    if not st.session_state.authenticated:
        return False
        
    required_pages = {
        'Topic Research': ['user', 'admin'],
        'Topic Campaign': ['user', 'admin'],
        'Article Draft': ['user', 'admin'],
        'Editing Criteria': ['user', 'admin'],
        'Final Article': ['user', 'admin'],
        'Image Description': ['user', 'admin'],
        'SEO Generation': ['user', 'admin']
    }
    
    user_role = st.session_state.user.get('role', 'user')
    return user_role in required_pages.get(page_name, [])

logger = logging.getLogger(__name__)

class CampaignGenerator:
    """Handles campaign generation and validation"""
    
    CAMPAIGN_TYPES = {
        "standard": "Regular blog content campaign",
        "series": "Multi-part article series",
        "themed": "Theme-based content campaign",
        "seasonal": "Seasonal or timely campaign"
    }
    
    @staticmethod
    def validate_campaign(campaign: str) -> bool:
        """Validate campaign content"""
        if not campaign or len(campaign.strip()) < 100:
            return False
        return True

async def generate_campaign(
    research_analysis: str,
    campaign_type: str,
    additional_notes: str,
    llm_client: AsyncLLMClient,
    prompt_handler: AsyncPromptHandler,
    user_email: str
) -> Dict[str, Any]:
    """Generate topic campaign asynchronously"""
    try:
        # Check user authentication
        if not user_email:
            raise ValueError("User not authenticated")

        # Format campaign prompt
        campaign_prompt = await prompt_handler.format_prompt(
            'topic_campaign',
            {
                'research_analysis': research_analysis,
                'campaign_type': campaign_type,
                'additional_notes': additional_notes
            }
        )
        
        if not campaign_prompt:
            raise ValueError("Failed to format campaign prompt")

        # Generate campaign
        campaign = await llm_client.generate_response(
            system_prompt=(
                "You are an AI strategist creating content campaigns for Fairness Factor. "
                "Focus on employee advocacy topics that align with the company's mission. "
                f"Generate a {campaign_type} campaign that addresses key workplace issues."
            ),
            user_prompt=campaign_prompt,
            max_tokens=1500,
            user_email=user_email
        )
        
        if not CampaignGenerator.validate_campaign(campaign):
            raise ValueError("Generated campaign does not meet minimum requirements")
        
        return {
            'success': True,
            'campaign': campaign
        }
    except Exception as e:
        logger.error(f"Error generating campaign: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def topic_campaign_page(db_handlers, llm_client, prompt_handler):
    """Topic Campaign Page Handler"""
    try:
        # Check authentication and access
        if not st.session_state.authenticated:
            st.warning("Please log in to access this page")
            st.stop()
            return
            
        if not check_page_access('Topic Campaign'):
            st.error("You don't have permission to access this page")
            st.stop()
            return

        user_email = st.session_state.user['email']
        
        # Check prerequisites
        if 'research_analysis' not in st.session_state:
            st.warning("⚠️ Please complete the Topic Research step first")
            st.stop()
            return

        # Log page access
        await db_handlers['analytics'].log_activity(
            user_email=user_email,
            activity_type='page_access',
            metadata={'page': 'Topic Campaign'}
        )

        # Existing page code continues here...
        
        # Display research analysis
        with st.expander("📊 Research Analysis", expanded=False):
            st.write(st.session_state['research_analysis'])
        
        # Campaign settings
        st.write("### 📋 Campaign Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_type = st.selectbox(
                "Campaign Type:",
                list(CampaignGenerator.CAMPAIGN_TYPES.keys()),
                format_func=lambda x: CampaignGenerator.CAMPAIGN_TYPES[x],
                help="Select the type of content campaign"
            )
            
            target_audience = st.multiselect(
                "Target Audience:",
                ["Employees", "HR Professionals", "Business Leaders", "Legal Professionals"],
                default=["Employees"],
                help="Select target audience segments"
            )
        
        with col2:
            campaign_duration = st.selectbox(
                "Campaign Duration:",
                ["1 month", "3 months", "6 months", "12 months"],
                help="Select campaign duration"
            )
            
            content_frequency = st.selectbox(
                "Content Frequency:",
                ["Weekly", "Bi-weekly", "Monthly"],
                help="Select content publication frequency"
            )
        
        # Additional notes
        additional_notes = st.text_area(
            "Additional Notes:",
            help="Add any specific requirements or focus areas for the campaign"
        )
        
        # Generate campaign
        if st.button("🚀 Generate Campaign", help="Click to generate topic campaign"):
            with st.spinner("✍️ Generating campaign..."):
                try:
                    result = await generate_campaign(
                        research_analysis=st.session_state['research_analysis'],
                        campaign_type=campaign_type,
                        additional_notes=additional_notes,
                        llm_client=llm_client,
                        prompt_handler=prompt_handler,
                        user_email=user_email
                    )
                    
                    if result['success']:
                        # Save campaign content
                        content_id = await db_handlers['blog'].save_content(
                            user_email=user_email,
                            content_type='campaign',
                            content=result['campaign'],
                            metadata={
                                'research_id': st.session_state['research_id'],
                                'campaign_type': campaign_type,
                                'target_audience': target_audience,
                                'campaign_duration': campaign_duration,
                                'content_frequency': content_frequency,
                                'additional_notes': additional_notes
                            }
                        )
                        
                        # Update session state
                        st.session_state['topic_campaign'] = result['campaign']
                        st.session_state['campaign_id'] = content_id
                        
                        # Log activity
                        await db_handlers['analytics'].log_activity(
                            user_email=user_email,
                            activity_type='campaign_generation',
                            metadata={
                                'content_id': content_id,
                                'campaign_type': campaign_type
                            }
                        )
                        
                        # Display campaign
                        st.success("✅ Campaign generated successfully!")
                        
                        # Campaign overview
                        st.write("### 📑 Campaign Overview")
                        campaign_sections = result['campaign'].split('\n\n')
                        
                        for i, section in enumerate(campaign_sections):
                            with st.expander(f"Section {i+1}", expanded=i==0):
                                st.write(section)
                                
                                # Add implementation status
                                status = st.selectbox(
                                    "Implementation Status:",
                                    ["Planned", "In Progress", "Completed", "On Hold"],
                                    key=f"status_{i}"
                                )
                                if status != "Planned":
                                    st.session_state.setdefault('campaign_status', {})[i] = status
                        
                        # Topic selection
                        st.write("### 🎯 Topic Selection")
                        topics = [line.strip() for line in result['campaign'].split('\n') 
                                if line.strip() and not line.startswith('#')]
                        
                        selected_topic = st.selectbox(
                            "Select a topic for your next article:",
                            topics,
                            help="Choose the topic you want to write about"
                        )
                        
                        if selected_topic:
                            st.session_state['selected_topic'] = selected_topic
                            
                            # Save selected topic
                            await db_handlers['blog'].update_content(
                                content_id,
                                {'metadata.selected_topic': selected_topic}
                            )
                        
                        # Export campaign
                        if st.button("📤 Export Campaign"):
                            export_data = {
                                'campaign': result['campaign'],
                                'metadata': {
                                    'campaign_type': campaign_type,
                                    'target_audience': target_audience,
                                    'campaign_duration': campaign_duration,
                                    'content_frequency': content_frequency,
                                    'selected_topic': selected_topic,
                                    'status': st.session_state.get('campaign_status', {})
                                }
                            }
                            
                            st.download_button(
                                label="📥 Download Campaign",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"campaign_{content_id}.json",
                                mime="application/json"
                            )
                        
                    else:
                        st.error(f"❌ Campaign generation failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    logger.error(f"Error in campaign generation: {str(e)}")
        
        # Campaign history
        with st.expander("📚 Campaign History", expanded=False):
            try:
                campaign_history = await db_handlers['blog'].get_user_content(
                    user_email=user_email,
                    content_type='campaign',
                    limit=5
                )
                
                if campaign_history:
                    for entry in campaign_history:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"Campaign from {entry['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"Type: {entry['metadata'].get('campaign_type', 'Unknown')}")
                            
                        with col2:
                            if st.button("Load", key=f"load_{entry['_id']}"):
                                st.session_state['topic_campaign'] = entry['content']
                                st.session_state['campaign_id'] = str(entry['_id'])
                                st.experimental_rerun()
                                
                        with col3:
                            if st.button("Delete", key=f"delete_{entry['_id']}"):
                                try:
                                    await db_handlers['blog'].delete_content(str(entry['_id']))
                                    st.success("✅ Campaign deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting campaign: {str(e)}")
                        
                        st.markdown("---")
                else:
                    st.info("No previous campaigns found.")
                    
            except Exception as e:
                st.error("Failed to load campaign history")
                logger.error(f"Error loading campaign history: {str(e)}")

        # Help section
        with st.expander("❓ Need Help?", expanded=False):
            st.markdown("""
            ### Campaign Guidelines
            1. Focus on employee advocacy themes
            2. Consider current workplace trends
            3. Address common pain points
            4. Include actionable insights
            5. Maintain consistent messaging
            
            ### Best Practices
            - Plan content calendar
            - Define clear objectives
            - Consider audience needs
            - Track engagement metrics
            - Adjust based on feedback
            
            ### Support
            Contact: content@fairnessfactor.com
            """)

    except Exception as e:
        logger.error(f"Error in topic campaign page: {str(e)}")
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
        
        await topic_campaign_page(
            handlers,
            AsyncLLMClient(),
            AsyncPromptHandler(db)
        )
    
    asyncio.run(test_page())