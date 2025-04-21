import streamlit as st
import uuid
import yaml
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.bedrock_agent import agents_helper
from src.ui.config import bot_configs
from src.ui.ui_utils import invoke_agent
import logging
logger = logging.getLogger(__name__)

def initialize_chat_state():
    """Initialize chat state if it doesn't exist"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

def display_chat_messages():
    """Display all chat messages"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_input(user_input: str):
    """Process user input and generate response"""
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # TODO: Replace this with your actual bot response logic
    response = f"This is a sample response to: {user_input}"
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})

def experimental_interface():
    """Main chat interface"""
    initialize_chat_state()
    
    # Create main chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Messages area
    with st.container():
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        display_chat_messages()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    with st.container():
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        cols = st.columns([6, 1])
        
        # Text input in first column
        with cols[0]:
            user_input = st.text_input(
                "Message",
                key="chat_input",
                label_visibility="collapsed",
                placeholder="Type your message here..."
            )
        
        # Send button in second column
        with cols[1]:
            send_button = st.button("Send", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle send button click
        if send_button and user_input:
            handle_user_input(user_input)
            # Clear input
            st.session_state.chat_input = ""
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def initialize_session():
    """Initialize session state and bot configuration."""

    # Refresh agent IDs and aliases
    for idx, config in enumerate(bot_configs):
        try:
            agent_id = agents_helper.get_agent_id_by_name(config['agent_name'])
            agent_alias_id = agents_helper.get_agent_latest_alias_id(agent_id)
            bot_configs[idx]['agent_id'] = agent_id
            bot_configs[idx]['agent_alias_id'] = agent_alias_id
        except Exception as e:
            logger.error(f"Could not find agent named:{config['agent_name']}, skipping...")
            continue

    # Get bot configuration
    bot_name = os.environ.get('BOT_NAME', 'Marketing Planning Agent')
    bot_config = next((config for config in bot_configs if config['bot_name'] == bot_name), None)
    
    if bot_config:
        st.session_state['bot_config'] = bot_config
        # logger.info(st.session_state['bot_config'])
        # Initialize session ID and message history
        st.session_state['session_id'] = str(uuid.uuid4())
        st.session_state.messages = []

        # Add initial bot message
        start_prompt = bot_config.get('start_prompt')
        initial_message = f"Hi Use this example prompt in the chat input to test: '{start_prompt}'"
        st.session_state.messages.append({
            "role": "assistant",
            "content": initial_message
        })
        
        # Load tasks if any
        task_yaml_content = {}
        if 'tasks' in bot_config:
            with open(bot_config['tasks'], 'r') as file:
                task_yaml_content = yaml.safe_load(file)
        st.session_state['task_yaml_content'] = task_yaml_content

        # Initialize session ID and message history
        st.session_state['session_id'] = str(uuid.uuid4())

def chat_interface():
    # Display chat interface
    st.subheader(st.session_state['bot_config']['bot_name'])

    # Show message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    # placeholder = st.session_state['bot_config'].get('start_prompt', " ")
    placeholder = "Enter your question"
    user_query = st.chat_input(placeholder=placeholder)
    # logger.info(placeholder)
    # logger.info(user_query)
    if user_query:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Get and display assistant response
        response = ""
        with st.chat_message("assistant"):
            try:
                session_id = st.session_state['session_id']
                response = st.write_stream(invoke_agent(
                    user_query, 
                    session_id, 
                    st.session_state['task_yaml_content']
                ))
            except Exception as e:
                logger.error(f"Error: {e}")  # Keep logging for debugging
                st.error(f"An error occurred: {str(e)}")  # Show error in UI
                response = "I encountered an error processing your request. Please try again."

        # Update chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Reset input
        # user_query = st.chat_input(placeholder=" ", key="user_input")

    # Update session count
    st.session_state['count'] = st.session_state.get('count', 1) + 1

def main():
    """Main application flow."""
    initialize_session()
    """Main UI function"""
    chat_interface()

if __name__ == "__main__":
    main()
