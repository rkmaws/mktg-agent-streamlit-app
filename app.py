import streamlit as st
from src.ui import demo_ui
from src.utils import cognito_auth_helper
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logs go to stdout
)

logger = logging.getLogger(__name__)

def content_section():
    st.header("AWS Agentic AI Demo powered by Amazon Bedrock Agents", divider="rainbow")
    demo_ui.main()

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        logger.info("authenticated not in session state")
        st.session_state.authenticated = False
        # logger.info(st.session_state)

    if not st.session_state.authenticated:
        # Get the authorization code from query parameters
        code = st.query_params.get('code')
        
        if code:
            try:
                auth = cognito_auth_helper.CognitoAuth()
                # Exchange the code for tokens
                tokens = auth.exchange_code_for_tokens(code)
                if tokens and 'id_token' in tokens:
                    user_info = auth.verify_token(tokens['id_token'])
                    # logger.info(user_info)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        # Clear the code from URL
                        st.query_params.clear()
                        return True
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                return False
        
        # If not authenticated, show login page
        st.write("Please login to continue")
        auth = cognito_auth_helper.CognitoAuth()
        login_url = auth.get_login_url()
        logger.info(login_url)
        st.markdown(f"[Login with Cognito]({login_url})")
        return False
    
    return True

# this one uses primitives, works on local host, not working with cloudfront deployment
def main2():
    # Check authentication before proceeding
    # logger.info(st.session_state)
    auth_section()
    logger.info("authenticated")

    st.set_page_config(
    page_title="AWS",
    page_icon="👋",
    layout="wide"
    )

    st.write("Welcome! You are authenticated.")
    st.header("AWS Agentic AI Demo powered by Amazon Bedrock Agents", divider="rainbow")
    demo_ui.main()

# this one is based on the 3p library
def main():
    # Initialise CognitoAuthenticator
    st.set_page_config(
        page_title="AWS Agentic AI for Marketing",
        page_icon="👋",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown("""
        <style>
            div.block-container {
                padding-top: 1rem;
            }
            div.stHeader {
                background-color: transparent;
            }
            header {
                background-color: transparent;
            }
            
            /* Chat container styles */
            .chat-container {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 80px);
                overflow: hidden;
            }
            
            /* Messages area */
            .chat-messages {
                flex-grow: 1;
                overflow-y: auto;
                padding-bottom: 100px;
            }
            
            /* Input area */
            .chat-input {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 1rem;
                background: white;
                border-top: 1px solid #ddd;
                z-index: 1000;
            }

            /* Ensure stMarkdown containers don't add extra margins */
            .element-container {
                margin-bottom: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    auth = cognito_auth_helper.CognitoAuth()
    authenticator = auth.get_authenticator()

    # Authenticate user, and stop here if not logged in
    is_logged_in = authenticator.login()
    if not is_logged_in:
        st.stop()

    def logout():
        authenticator.logout()

    with st.sidebar:
        st.text(f"Welcome,\n{authenticator.get_email()}")
        st.button("Logout", "logout_btn", on_click=logout)

    content_section()

if __name__ == "__main__":
    main()