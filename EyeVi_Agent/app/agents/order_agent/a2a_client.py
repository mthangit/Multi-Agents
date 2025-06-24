#!/usr/bin/env python3
"""
A2A Client for testing Advisor Agent
"""

import asyncio
import sys
from typing import Optional, Any
import httpx
from uuid import uuid4

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import SendMessageRequest, SendStreamingMessageRequest, MessageSendParams


class AdvisorAgentClient:
    """Client for interacting with Advisor Agent via A2A protocol."""
    
    def __init__(self, base_url: str = "http://localhost:10000"):
        self.base_url = base_url
        self.httpx_client = None
        self.client = None
        self.agent_card = None
        self._initialized = False

    async def initialize(self):
        """Initialize the A2A client with proper agent card."""
        if self._initialized:
            return
            
        print(f"🔄 Connecting to agent at: {self.base_url}")
        self.httpx_client = httpx.AsyncClient()
        
        # Initialize A2ACardResolver to fetch agent card
        resolver = A2ACardResolver(
            httpx_client=self.httpx_client,
            base_url=self.base_url
        )
        
        # Fetch agent card
        self.agent_card = await resolver.get_agent_card()
        
        # Initialize A2A client with agent card
        self.client = A2AClient(
            httpx_client=self.httpx_client,
            agent_card=self.agent_card
        )
        
        # Display agent info immediately
        print(f"✅ Connected to: {self.agent_card.name}")
        print(f"📝 Description: {self.agent_card.description}")
        print(f"🔗 URL: {self.agent_card.url}")
        if hasattr(self.agent_card, 'skills') and self.agent_card.skills:
            print(f"🛠️ Available skills: {len(self.agent_card.skills)}")
            for skill in self.agent_card.skills:
                print(f"   - {skill.name}: {skill.description}")
        else:
            print("🛠️ No specific skills listed")
        print("─" * 50)
        
        self._initialized = True

    async def close(self):
        """Close the httpx client."""
        if self.httpx_client:
            await self.httpx_client.aclose()

    async def send_message(self, message: str, stream: bool = False) -> dict:
        """Send a message to the advisor agent."""
        if not self.client:
            await self.initialize()
            
        # try:
            # Prepare message payload according to A2A format
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': message}
                ],
                'messageId': uuid4().hex,
            },
        }
        
        if stream:
            print(f"🔄 Streaming request to advisor agent...")
            
            # Create streaming request
            streaming_request = SendStreamingMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            stream_response = self.client.send_message_streaming(streaming_request)
            result_parts = []
            
            async for chunk in stream_response:
                chunk_data = chunk.model_dump(mode='json', exclude_none=True)
                print(f"📝 Chunk: {chunk_data}")
                
                # Extract content from chunk
                if 'result' in chunk_data:
                    result = chunk_data['result']
                    if 'parts' in result:
                        for part in result['parts']:
                            if part.get('type') == 'text':
                                result_parts.append(part.get('text', ''))
            
            return {
                "status": "success",
                "content": "\n".join(result_parts),
                "task_id": streaming_request.id
            }
                    
        else:
            print(f"📨 Sending message to advisor agent...")
            
            # Create non-streaming request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            response = await self.client.send_message(request=request, http_kwargs={"timeout": None})
            response_data = response.model_dump(mode='json', exclude_none=True)
            
            # Extract content from response
            content = ""
            if 'result' in response_data:
                result = response_data['result']
                if 'parts' in result:
                    for part in result['parts']:
                        if part.get('kind') == 'text':
                            content += part.get('text', '')
            
            return {
                "status": "success",
                "content": content,
                "task_id": request.id,
                "raw_response": response_data
            }
                
        # except Exception as e:
        #     return {
        #         "status": "error",
        #         "error": str(e)
        #     }

    async def get_agent_info(self) -> dict:
        """Get agent card information."""
        if not self.client:
            await self.initialize()
            
        try:
            # Use the already fetched agent card
            return {
                "status": "success",
                "agent_card": {
                    "name": self.agent_card.name,
                    "version": self.agent_card.version,
                    "description": self.agent_card.description,
                    "url": self.agent_card.url,
                    "skills": [
                        {
                            "name": skill.name,
                            "description": skill.description
                        } for skill in self.agent_card.skills
                    ] if hasattr(self.agent_card, 'skills') and self.agent_card.skills else []
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


async def demo_queries():
    """Demo queries for testing the advisor agent."""
    
    demo_questions = [
        "Tôi bị cận thị 2.5 độ, nên chọn loại tròng kính nào?",
        "Kính chống ánh sáng xanh có thực sự hiệu quả không?",
        "Khuôn mặt tròn phù hợp với kiểu gọng nào?",
        "So sánh tròng kính đa tròng và đơn tròng?",
        "Chất liệu gọng titan có ưu điểm gì?"
    ]
    
    print("=" * 60)
    print("🤖 DEMO: ADVISOR AGENT A2A CLIENT")
    print("=" * 60)
    
    client = AdvisorAgentClient()
    
    try:
        # Initialize and fetch agent info automatically
        await client.initialize()
        
        print(f"\n🎯 Testing with {len(demo_questions)} demo questions:")
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n" + "─" * 50)
            print(f"❓ [{i}] {question}")
            print("─" * 50)
            
            # Send message
            result = await client.send_message(question, stream=False)
            
            if result["status"] == "success":
                print(f"🤖 Advisor Agent Response:")
                print(result["content"])
                print(f"\n📊 Task ID: {result['task_id']}")
            else:
                print(f"❌ Error: {result['error']}")
            
            # Small delay between requests
            await asyncio.sleep(1)
            
    finally:
        await client.close()


async def interactive_mode():
    """Interactive chat mode with advisor agent."""
    print("=" * 60)
    print("💬 INTERACTIVE MODE: ADVISOR AGENT A2A")
    print("=" * 60)
    
    client = AdvisorAgentClient()
    
    # try:
        # Initialize and fetch agent info automatically
    await client.initialize()
    
    print("\nCommands:")
    print("  - 'exit' or 'quit': Exit")
    print("  - 'info': Show agent information")
    print("  - 'stream <message>': Send streaming message")
    print("  - Or type your eyewear question directly")
    print("─" * 60)
    while True:
        # try:
            user_input = input("\n💬 Bạn: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Tạm biệt!")
                break
                
            elif user_input.lower() == 'info':
                agent_info = await client.get_agent_info()
                if agent_info["status"] == "success":
                    card = agent_info["agent_card"]
                    print(f"\n📋 Agent Information:")
                    print(f"   Name: {card['name']}")
                    print(f"   Version: {card['version']}")
                    print(f"   URL: {card['url']}")
                    print(f"   Skills: {len(card['skills'])}")
                else:
                    print(f"❌ Error getting agent info: {agent_info['error']}")
                    
            elif user_input.lower().startswith('stream '):
                message = user_input[7:]  # Remove 'stream ' prefix
                print("🔄 Streaming mode...")
                result = await client.send_message(message, stream=True)
                if result["status"] == "error":
                    print(f"❌ Error: {result['error']}")
                    
            else:
                # Regular message
                print("🤖 Đang tư vấn...")
                result = await client.send_message(user_input)
                
                if result["status"] == "success":
                    print(f"\n🤖 Chuyên gia tư vấn:")
                    print(result["content"])
                else:
                    print(f"❌ Error: {result['error']}")
                        
    #         except KeyboardInterrupt:
    #             print("\n👋 Tạm biệt!")
    #             break
    #         except Exception as e:
    #             print(f"❌ Unexpected error: {e}")
                
    # finally:
    #     await client.close()


async def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            await demo_queries()
        elif sys.argv[1] == "chat":
            await interactive_mode()
        else:
            # Single question mode
            question = " ".join(sys.argv[1:])
            client = AdvisorAgentClient()
            
            try:
                await client.initialize()
                print(f"\n❓ Question: {question}")
                result = await client.send_message(question)
                
                if result["status"] == "success":
                    print(f"\n🤖 Answer:")
                    print(result["content"])
                else:
                    print(f"❌ Error: {result['error']}")
            finally:
                await client.close()
    else:
        # Default to interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main()) 