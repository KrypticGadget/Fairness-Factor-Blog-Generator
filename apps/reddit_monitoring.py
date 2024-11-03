# apps/reddit_monitoring.py
from .base_app import BaseApp
import streamlit as st
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)

class RedditMonitoringApp(BaseApp):
    def __init__(self):
        super().__init__()
        self.title = "Reddit Monitoring"
        self.description = "Monitor and analyze Reddit discussions"
        self.icon = "🔍"

    async def initialize(self, handlers: Dict[str, Any]) -> bool:
        try:
            # Initialize any required resources
            return True
        except Exception as e:
            logger.error(f"Reddit Monitoring initialization error: {str(e)}")
            return False

    async def render(self, handlers: Dict[str, Any]):
        st.title(f"{self.icon} {self.title}")
        
        # Sidebar options
        with st.sidebar:
            view = st.radio(
                "View",
                ["Dashboard", "Subreddit Analysis", "Keyword Tracking", "Sentiment Analysis", "Settings"]
            )
        
        try:
            if view == "Dashboard":
                await self.render_dashboard(handlers)
            elif view == "Subreddit Analysis":
                await self.render_subreddit_analysis(handlers)
            elif view == "Keyword Tracking":
                await self.render_keyword_tracking(handlers)
            elif view == "Sentiment Analysis":
                await self.render_sentiment_analysis(handlers)
            elif view == "Settings":
                await self.render_settings(handlers)
                
        except Exception as e:
            logger.error(f"Error rendering {view}: {str(e)}")
            self.show_error(f"An error occurred while loading {view}")

    async def render_dashboard(self, handlers: Dict[str, Any]):
        st.header("Dashboard")
        
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
        
        # Get dashboard data
        dashboard_data = await handlers['reddit'].get_dashboard_data(
            st.session_state.user['email'],
            start_date,
            end_date
        )
        
        if dashboard_data:
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Mentions", dashboard_data['total_mentions'])
            with col2:
                st.metric("Sentiment Score", f"{dashboard_data['sentiment_score']:.2f}")
            with col3:
                st.metric("Engagement Rate", f"{dashboard_data['engagement_rate']:.2f}%")
            with col4:
                st.metric("Trending Topics", dashboard_data['trending_topics'][0])
            
            # Display charts
            st.subheader("Mentions Over Time")
            fig = px.line(dashboard_data['mentions_over_time'], x='date', y='mentions')
            st.plotly_chart(fig)
            
            st.subheader("Sentiment Distribution")
            fig = px.pie(dashboard_data['sentiment_distribution'], values='count', names='sentiment')
            st.plotly_chart(fig)
            
            st.subheader("Top Subreddits")
            fig = px.bar(dashboard_data['top_subreddits'], x='subreddit', y='mentions')
            st.plotly_chart(fig)
        else:
            st.info("No dashboard data available for the selected date range.")

    async def render_subreddit_analysis(self, handlers: Dict[str, Any]):
        st.header("Subreddit Analysis")
        
        # Subreddit selector
        subreddit = st.text_input("Enter Subreddit Name", value="FairnessFactor")
        
        if st.button("Analyze Subreddit"):
            with st.spinner("Analyzing subreddit..."):
                try:
                    analysis = await handlers['reddit'].analyze_subreddit(subreddit)
                    
                    if analysis:
                        st.subheader("Subreddit Overview")
                        st.write(f"Subscribers: {analysis['subscribers']}")
                        st.write(f"Active Users: {analysis['active_users']}")
                        st.write(f"Posts per Day: {analysis['posts_per_day']}")
                        
                        st.subheader("Top Posts")
                        for post in analysis['top_posts']:
                            with st.expander(post['title']):
                                st.write(f"Score: {post['score']}")
                                st.write(f"Comments: {post['num_comments']}")
                                st.write(f"URL: {post['url']}")
                        
                        st.subheader("Topic Distribution")
                        fig = px.pie(analysis['topic_distribution'], values='count', names='topic')
                        st.plotly_chart(fig)
                        
                        st.subheader("User Activity")
                        fig = px.bar(analysis['user_activity'], x='hour', y='activity')
                        st.plotly_chart(fig)
                    else:
                        st.warning("Unable to analyze subreddit. Please check the subreddit name and try again.")
                        
                except Exception as e:
                    logger.error(f"Subreddit analysis error: {str(e)}")
                    self.show_error("Error analyzing subreddit")

    async def render_keyword_tracking(self, handlers: Dict[str, Any]):
        st.header("Keyword Tracking")
        
        # Get tracked keywords
        tracked_keywords = await handlers['reddit'].get_tracked_keywords(st.session_state.user['email'])
        
        # Display tracked keywords
        st.subheader("Tracked Keywords")
        for keyword in tracked_keywords:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(keyword)
            with col2:
                if st.button("Remove", key=f"remove_{keyword}"):
                    if await handlers['reddit'].remove_tracked_keyword(st.session_state.user['email'], keyword):
                        self.show_success(f"Removed '{keyword}' from tracking")
                        st.rerun()
        
        # Add new keyword
        new_keyword = st.text_input("Add New Keyword")
        if st.button("Add Keyword"):
            if await handlers['reddit'].add_tracked_keyword(st.session_state.user['email'], new_keyword):
                self.show_success(f"Added '{new_keyword}' to tracking")
                st.rerun()
        
        # Keyword mentions
        st.subheader("Keyword Mentions")
        selected_keyword = st.selectbox("Select Keyword", tracked_keywords)
        if selected_keyword:
            mentions = await handlers['reddit'].get_keyword_mentions(st.session_state.user['email'], selected_keyword)
            if mentions:
                df = pd.DataFrame(mentions)
                st.dataframe(df)
            else:
                st.info(f"No mentions found for '{selected_keyword}'")

    async def render_sentiment_analysis(self, handlers: Dict[str, Any]):
        st.header("Sentiment Analysis")
        
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
        
        # Get sentiment data
        sentiment_data = await handlers['reddit'].get_sentiment_data(
            st.session_state.user['email'],
            start_date,
            end_date
        )
        
        if sentiment_data:
            st.subheader("Overall Sentiment")
            fig = px.pie(sentiment_data['overall'], values='count', names='sentiment', title="Overall Sentiment Distribution")
            st.plotly_chart(fig)
            
            st.subheader("Sentiment Over Time")
            fig = px.line(sentiment_data['over_time'], x='date', y=['positive', 'neutral', 'negative'], title="Sentiment Over Time")
            st.plotly_chart(fig)
            
            st.subheader("Top Positive Comments")
            for comment in sentiment_data['top_positive']:
                st.write(f"Score: {comment['score']}")
                st.write(comment['text'])
                st.write("---")
            
            st.subheader("Top Negative Comments")
            for comment in sentiment_data['top_negative']:
                st.write(f"Score: {comment['score']}")
                st.write(comment['text'])
                st.write("---")
        else:
            st.info("No sentiment data available for the selected date range.")

    async def render_settings(self, handlers: Dict[str, Any]):
        st.header("Settings")
        
        # Reddit API settings
        st.subheader("Reddit API Settings")
        with st.form("reddit_api_settings"):
            client_id = st.text_input("Client ID", type="password")
            client_secret = st.text_input("Client Secret", type="password")
            user_agent = st.text_input("User Agent")
            
            if st.form_submit_button("Save API Settings"):
                if await handlers['reddit'].update_api_settings(
                    st.session_state.user['email'],
                    {
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'user_agent': user_agent
                    }
                ):
                    self.show_success("Reddit API settings saved successfully!")
                else:
                    self.show_error("Failed to save Reddit API settings")
        
        # Monitoring settings
        st.subheader("Monitoring Settings")
        with st.form("monitoring_settings"):
            update_frequency = st.selectbox(
                "Update Frequency",
                ["Hourly", "Daily", "Weekly"]
            )
            
            max_posts = st.number_input(
                "Maximum Posts to Monitor",
                min_value=100,
                max_value=1000,
                value=500,
                step=100
            )
            
            if st.form_submit_button("Save Monitoring Settings"):
                if await handlers['reddit'].update_monitoring_settings(
                    st.session_state.user['email'],
                    {
                        'update_frequency': update_frequency,
                        'max_posts': max_posts
                    }
                ):
                    self.show_success("Monitoring settings saved successfully!")
                else:
                    self.show_error("Failed to save monitoring settings")