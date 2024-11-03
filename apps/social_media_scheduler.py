# apps/social_media_scheduler.py
from .base_app import BaseApp
import streamlit as st
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SocialMediaSchedulerApp(BaseApp):
    def __init__(self):
        super().__init__()
        self.title = "Social Media Scheduler"
        self.description = "Schedule and manage social media posts"
        self.icon = "📱"

    async def initialize(self, handlers: Dict[str, Any]) -> bool:
        try:
            # Initialize any required resources
            return True
        except Exception as e:
            logger.error(f"Social Media Scheduler initialization error: {str(e)}")
            return False

    async def render(self, handlers: Dict[str, Any]):
        st.title(f"{self.icon} {self.title}")
        
        # Sidebar options
        with st.sidebar:
            view = st.radio(
                "View",
                ["Calendar", "Posts", "Analytics", "Settings"]
            )
        
        try:
            if view == "Calendar":
                await self.render_calendar(handlers)
            elif view == "Posts":
                await self.render_posts(handlers)
            elif view == "Analytics":
                await self.render_analytics(handlers)
            elif view == "Settings":
                await self.render_settings(handlers)
                
        except Exception as e:
            logger.error(f"Error rendering {view}: {str(e)}")
            self.show_error(f"An error occurred while loading {view}")

    async def render_calendar(self, handlers: Dict[str, Any]):
        st.header("Content Calendar")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=(datetime.now() + timedelta(days=30)).date()
            )
        
        # Get scheduled posts
        scheduled_posts = await handlers['social'].get_scheduled_posts(
            st.session_state.user['email'],
            start_date,
            end_date
        )
        
        # Display calendar
        if scheduled_posts:
            for post in scheduled_posts:
                with st.expander(f"{post['scheduled_date']} - {post['platform']}"):
                    st.write(post['content'])
                    st.write(f"Status: {post['status']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit", key=f"edit_{post['_id']}"):
                            st.session_state['editing_post'] = post
                    with col2:
                        if st.button("Delete", key=f"delete_{post['_id']}"):
                            if await handlers['social'].delete_post(post['_id']):
                                self.show_success("Post deleted successfully!")
                                st.rerun()
        
        # Add new post button
        if st.button("Schedule New Post"):
            st.session_state['adding_post'] = True
            
        # Post editor
        if st.session_state.get('adding_post') or st.session_state.get('editing_post'):
            await self.render_post_editor(handlers)

    async def render_post_editor(self, handlers: Dict[str, Any]):
        st.subheader("Post Editor")
        
        post = st.session_state.get('editing_post', {})
        
        with st.form("post_editor"):
            platform = st.selectbox(
                "Platform",
                ["LinkedIn", "Twitter", "Facebook"],
                index=["LinkedIn", "Twitter", "Facebook"].index(post.get('platform', 'LinkedIn'))
            )
            
            content = st.text_area(
                "Content",
                value=post.get('content', ''),
                max_chars=280 if platform == 'Twitter' else 1000
            )
            
            scheduled_date = st.date_input(
                "Schedule Date",
                value=datetime.strptime(post.get('scheduled_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
            )
            
            scheduled_time = st.time_input(
                "Schedule Time",
                value=datetime.strptime(post.get('scheduled_time', '09:00'), '%H:%M').time()
            )
            
            if st.form_submit_button("Save Post"):
                try:
                    post_data = {
                        'platform': platform,
                        'content': content,
                        'scheduled_date': scheduled_date.strftime('%Y-%m-%d'),
                        'scheduled_time': scheduled_time.strftime('%H:%M'),
                        'user_email': st.session_state.user['email']
                    }
                    
                    if st.session_state.get('editing_post'):
                        success = await handlers['social'].update_post(
                            st.session_state['editing_post']['_id'],
                            post_data
                        )
                    else:
                        success = await handlers['social'].create_post(post_data)
                    
                    if success:
                        self.show_success("Post saved successfully!")
                        st.session_state.pop('adding_post', None)
                        st.session_state.pop('editing_post', None)
                        st.rerun()
                    else:
                        self.show_error("Failed to save post")
                        
                except Exception as e:
                    logger.error(f"Error saving post: {str(e)}")
                    self.show_error("Error saving post")

    async def render_posts(self, handlers: Dict[str, Any]):
        st.header("Posts")
        
        # Filter options
        status = st.multiselect(
            "Status",
            ["Draft", "Scheduled", "Published", "Failed"],
            default=["Draft", "Scheduled"]
        )
        
        platform = st.multiselect(
            "Platform",
            ["LinkedIn", "Twitter", "Facebook"],
            default=["LinkedIn", "Twitter", "Facebook"]
        )
        
        # Get filtered posts
        posts = await handlers['social'].get_posts(
            st.session_state.user['email'],
            status=status,
            platform=platform
        )
        
        if posts:
            for post in posts:
                with st.expander(f"{post['platform']} - {post['status']}"):
                    st.write(post['content'])
                    st.write(f"Scheduled: {post['scheduled_date']} {post['scheduled_time']}")
        else:
            st.info("No posts found matching the filters.")

    async def render_analytics(self, handlers: Dict[str, Any]):
        st.header("Analytics")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=(datetime.now() - timedelta(days=30)).date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date()
            )
        
        # Get analytics data
        analytics = await handlers['social'].get_analytics(
            st.session_state.user['email'],
            start_date,
            end_date
        )
        
        if analytics:
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Posts", analytics['total_posts'])
            with col2:
                st.metric("Engagement Rate", f"{analytics['engagement_rate']:.2f}%")
            with col3:
                st.metric("Click-through Rate", f"{analytics['ctr']:.2f}%")
            
            # Display charts
            st.subheader("Engagement Over Time")
            st.line_chart(analytics['engagement_data'])
            
            st.subheader("Platform Performance")
            st.bar_chart(analytics['platform_data'])
        else:
            st.info("No analytics data available for the selected date range.")

    async def render_settings(self, handlers: Dict[str, Any]):
        st.header("Settings")
        
        # Platform connections
        st.subheader("Connected Platforms")
        
        platforms = await handlers['social'].get_connected_platforms(
            st.session_state.user['email']
        )
        
        for platform in ['LinkedIn', 'Twitter', 'Facebook']:
            connected = platform in platforms
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{platform}: {'Connected' if connected else 'Not Connected'}")
            with col2:
                if connected:
                    if st.button(f"Disconnect {platform}"):
                        if await handlers['social'].disconnect_platform(
                            st.session_state.user['email'],
                            platform
                        ):
                            self.show_success(f"{platform} disconnected successfully!")
                            st.rerun()
                else:
                    if st.button(f"Connect {platform}"):
                        # Implement OAuth flow
                        pass
        
        # Posting preferences
        st.subheader("Posting Preferences")
        
        with st.form("posting_preferences"):
            default_time = st.time_input(
                "Default Posting Time",
                value=datetime.strptime('09:00', '%H:%M').time()
            )
            
            auto_schedule = st.checkbox(
                "Enable Auto-scheduling",
                help="Automatically schedule posts at optimal times"
            )
            
            if st.form_submit_button("Save Preferences"):
                if await handlers['social'].update_preferences(
                    st.session_state.user['email'],
                    {
                        'default_time': default_time.strftime('%H:%M'),
                        'auto_schedule': auto_schedule
                    }
                ):
                    self.show_success("Preferences saved successfully!")
                else:
                    self.show_error("Failed to save preferences")