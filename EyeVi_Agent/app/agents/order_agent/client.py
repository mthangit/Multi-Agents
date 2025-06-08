#!/usr/bin/env python3
"""
A2A Order Agent Client
Simplified client to interact with the A2A Order Management Agent
"""

import asyncio
import logging
import httpx
from typing import Optional, AsyncIterator
from uuid import uuid4

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import SendMessageRequest, SendStreamingMessageRequest, MessageSendParams

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderAgentClient:
    """
    Simple client wrapper for A2A Order Agent interaction
    """
    
    def __init__(self, agent_url: str = "http://localhost:10000", timeout: float = 300.0):
        """
        Initialize the client
        
        Args:
            agent_url: URL of the A2A Order Agent
            timeout: HTTP timeout in seconds
        """
        self.agent_url = agent_url
        self.timeout = timeout
        self.httpx_client = httpx.AsyncClient(timeout=timeout)
        self.a2a_client: Optional[A2AClient] = None
    
    async def connect(self):
        """Connect to the A2A agent"""
        try:
            # Get client from agent card URL
            self.a2a_client = await A2AClient.get_client_from_agent_card_url(
                httpx_client=self.httpx_client,
                base_url=self.agent_url
            )
            logger.info(f"✅ Connected to A2A agent at {self.agent_url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to A2A agent: {e}")
            raise
    
    async def get_agent_info(self):
        """Get agent card information"""
        try:
            resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=self.agent_url
            )
            agent_card = await resolver.get_agent_card()
            return {
                "name": agent_card.name,
                "description": agent_card.description,
                "version": agent_card.version,
                "skills": [
                    {
                        "id": skill.id,
                        "name": skill.name,
                        "description": skill.description,
                        "examples": skill.examples
                    }
                    for skill in agent_card.skills
                ]
            }
        except Exception as e:
            logger.error(f"❌ Failed to get agent info: {e}")
            return None
    
    async def send_message(self, message: str) -> str:
        """
        Send a message and get response (non-streaming)
        
        Args:
            message: Message to send to the agent
            
        Returns:
            Response string from the agent
        """
        if not self.a2a_client:
            await self.connect()
        
        try:
            logger.info(f"📤 Sending message: {message}")
            
            # Create message payload in correct format
            message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [{'type': 'text', 'text': message}],
                    'messageId': uuid4().hex,
                }
            }
            
            request = SendMessageRequest(
                params=MessageSendParams(**message_payload)
            )
            task = await self.a2a_client.send_message(request)
            
            logger.info(f"✅ Task created: {task.id}")
            return f"Task {task.id} created successfully"
            
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return f"Error: {str(e)}"
    
    def _extract_text_from_response(self, event) -> str:
        """
        Extract text content from A2A streaming response.
        
        Args:
            event: A2A streaming response event
            
        Returns:
            Extracted text content or empty string
        """
        try:
            if not hasattr(event, 'root') or not event.root:
                return ""
            
            result = event.root.result
            
            # Handle TaskStatusUpdateEvent
            if hasattr(result, 'kind') and result.kind == 'status-update':
                if hasattr(result, 'status') and result.status:
                    status = result.status
                    if hasattr(status, 'message') and status.message:
                        message_obj = status.message
                        if hasattr(message_obj, 'parts') and message_obj.parts:
                            texts = []
                            for part in message_obj.parts:
                                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                    texts.append(part.root.text)
                            return ' '.join(texts)
            
            # Handle TaskArtifactUpdateEvent
            elif hasattr(result, 'kind') and result.kind == 'artifact-update':
                if hasattr(result, 'artifact') and result.artifact:
                    artifact = result.artifact
                    if hasattr(artifact, 'parts') and artifact.parts:
                        texts = []
                        for part in artifact.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                texts.append(part.root.text)
                        return ' '.join(texts)
            
            # Handle Task object
            elif hasattr(result, 'kind') and result.kind == 'task':
                if hasattr(result, 'artifacts') and result.artifacts:
                    texts = []
                    for artifact in result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                    texts.append(part.root.text)
                    return ' '.join(texts)
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting text from response: {e}")
            return ""

    async def send_message_streaming(self, message: str) -> AsyncIterator[str]:
        """
        Send a message and get streaming response
        
        Args:
            message: Message to send to the agent
            
        Yields:
            Response chunks from the agent
        """
        if not self.a2a_client:
            await self.connect()
        
        try:
            logger.info(f"📤 Sending streaming message: {message}")
            
            # Create message payload in correct format
            message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [{'type': 'text', 'text': message}],
                    'messageId': uuid4().hex,
                }
            }
            
            request = SendStreamingMessageRequest(
                params=MessageSendParams(**message_payload)
            )
            
            async for event in self.a2a_client.send_message_streaming(request):
                logger.debug(f"📡 Received event type: {type(event)}")
                
                # Extract text content from the response
                text_content = self._extract_text_from_response(event)
                
                if text_content and text_content.strip():
                    logger.debug(f"📤 Yielding content: {text_content[:50]}...")
                    yield text_content
                else:
                    logger.debug("📤 No text content found in this event")
                
        except Exception as e:
            logger.error(f"❌ Error in streaming: {e}")
            yield f"Error: {str(e)}"
    
    async def close(self):
        """Close the client connection"""
        if self.httpx_client:
            await self.httpx_client.aclose()
            logger.info("🔌 Client connection closed")

# Convenient functions for quick usage
async def ask_agent(message: str, agent_url: str = "http://localhost:10000") -> str:
    """
    Quick function to ask the agent a question
    
    Args:
        message: Question to ask
        agent_url: Agent URL
        
    Returns:
        Agent response
    """
    client = OrderAgentClient(agent_url)
    try:
        response = await client.send_message(message)
        return response
    finally:
        await client.close()

async def chat_with_agent(agent_url: str = "http://localhost:10000"):
    """
    Interactive chat session with the agent
    """
    client = OrderAgentClient(agent_url)
    
    try:
        # Connect and show agent info
        await client.connect()
        agent_info = await client.get_agent_info()
        
        if agent_info:
            print(f"\n🤖 Connected to: {agent_info['name']}")
            print(f"📝 Description: {agent_info['description']}")
            print(f"🛠️ Available skills:")
            for skill in agent_info['skills']:
                print(f"  • {skill['name']}: {skill['description']}")
                if skill['examples']:
                    print(f"    Examples: {', '.join(skill['examples'][:2])}...")
        
        print(f"\n💬 Chat với agent (gõ 'quit' để thoát, 'help' để xem hướng dẫn)")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                message = input("\n👤 You: ").strip()
                
                if message.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if message.lower() == 'help':
                    print("""
🔧 Available commands:
• "Tìm sản phẩm iPhone" - Search for products
• "Thêm 2 sản phẩm ID 123 vào giỏ hàng" - Add to cart
• "Xem giỏ hàng" - View cart
• "Tạo đơn hàng" - Create order
• "quit" - Exit chat
                    """)
                    continue
                
                if not message:
                    continue
                
                # Send message with streaming
                print("🤖 Agent: ", end="", flush=True)
                response_parts = []
                
                async for chunk in client.send_message_streaming(message):
                    if chunk and chunk.strip():
                        print(chunk, end="", flush=True)
                        response_parts.append(chunk)
                
                print()  # New line after streaming is complete
                
                if not response_parts:
                    print("📋 No response received from agent.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    finally:
        await client.close()

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "chat":
            # Interactive chat mode
            agent_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:10000"
            print(f"🚀 Starting chat with agent at {agent_url}")
            asyncio.run(chat_with_agent(agent_url))
        else:
            # Single message mode
            message = " ".join(sys.argv[1:])
            print(f"🤔 Asking: {message}")
            response = asyncio.run(ask_agent(message))
            print(f"🤖 Response: {response}")
    else:
        print("""
🤖 A2A Order Agent Client

Usage:
  python client.py chat                    # Interactive chat
  python client.py chat http://localhost:10000  # Chat with custom URL
  python client.py "Tìm sản phẩm iPhone"  # Single question

Examples:
  python client.py chat
  python client.py "Xem giỏ hàng của tôi"
  python client.py "Thêm 2 sản phẩm ID 123 vào giỏ hàng"
        """) 