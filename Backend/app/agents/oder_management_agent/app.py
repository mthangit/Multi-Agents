"""
Main entry point for the shopping agent application
"""
import logging
import os
import sys
import uuid
from typing import List, Dict, Any, Optional, Tuple

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
# Import settings
from shopping_agent.config.settings import APP_NAME, DEFAULT_USER_ID, LOG_LEVEL, LOG_FORMAT
from shopping_agent.core.database import init_db
from shopping_agent.agents.root_agent import agent as root_agent

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

def setup_application():
    """Khởi tạo ứng dụng và kiểm tra kết nối database"""
    # Kiểm tra kết nối database
    try:
        init_db()
        logging.info("Database connection established successfully")
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        sys.exit(1)
    
    logging.info("Application setup completed")
    return True

def create_session(user_id: str = DEFAULT_USER_ID, session_id: Optional[str] = None) -> Tuple[Session, InMemorySessionService]:
    """Create a new session"""
    session_service = InMemorySessionService()
    if not session_id:
        session_id = str(uuid.uuid4())
    
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    
    return session, session_service

def run_agent(
    prompt: str, 
    user_id: str = DEFAULT_USER_ID,
    session_id: Optional[str] = None,
    session_state: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Run the agent with a prompt
    
    Args:
        prompt: User prompt
        user_id: User ID
        session_id: Optional session ID
        session_state: Optional initial session state
    
    Returns:
        List of responses
    """
    # Create session and runner
    session, session_service = create_session(user_id, session_id)
    
    # Set initial session state if provided
    if session_state:
        for key, value in session_state.items():
            session.state[key] = value
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    # Create user message
    content = types.Content(
        role='user',
        parts=[types.Part(text=prompt)]
    )
    
    # Run agent
    responses = []
    events = runner.run(
        user_id=user_id,
        session_id=session.session_id,
        new_message=content
    )
    
    # Process events
    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            responses.append(final_response)
    
    return responses

# Web UI using ADK CLI
if __name__ == "__main__":
    # Initialize the application
    setup_application()
    
    # Import required for ADK CLI
    from shopping_agent.agents.root_agent import agent

    # Log ready status
    logging.info(f"Shopping Agent ready. Run 'adk web' to start the web UI.")
    logging.info(f"Or import and use run_agent() function for programmatic access.") 