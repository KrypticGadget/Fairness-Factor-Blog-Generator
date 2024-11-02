import streamlit as st
import json
from llm.topic_campaign import generate_topic_campaign

def topic_campaign_page():
    st.title("Generate Fair Fight Topic Campaign")
    
    # Add a text area to view and edit the prompt
    with open("prompts/topic_campaign.txt", "r") as f:
        prompt_text = f.read()
    prompt_text = st.text_area("Edit the prompt:", value=prompt_text, height=200)

    # Save the edited prompt  
    if st.button("Save Prompt"):
        with open("prompts/topic_campaign.txt", "w") as f:
            f.write(prompt_text)
        st.success("Prompt saved successfully!")

    if 'research_analysis' not in st.session_state:
        st.warning("Please complete the Topic Research step first.")
        return
    
    st.write("Research Analysis:")
    st.write(st.session_state['research_analysis'])
    
    if st.button("Generate Topic Campaign"):
        with st.spinner("Generating topic campaign..."):
            topic_campaign = generate_topic_campaign(st.session_state['research_analysis'])
        st.session_state['topic_campaign'] = topic_campaign
        with open("output/topic_campaign.json", "w") as f:
            json.dump(topic_campaign, f)  
        st.write("Generated Topic Campaign:")
        st.write(topic_campaign)
    
    if 'topic_campaign' in st.session_state:
        selected_topic = st.selectbox("Select a topic for the Fair Fight blog article:", st.session_state['topic_campaign'].split('\n'))  
        if selected_topic:
            st.session_state['selected_topic'] = selected_topic
if __name__ == "__main__":
    topic_campaign_page()