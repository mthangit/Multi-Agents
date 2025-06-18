#!/usr/bin/env python3
"""
A2A Client for testing Advisor Agent
"""

import asyncio
import sys
from typing import Optional

from a2a.client import A2AClient
from a2a.types import SendMessageRequest


class AdvisorAgentClient:
    """Client for interacting with Advisor Agent via A2A protocol."""
    
    def __init__(self, agent_url: str = "http://localhost:10001"):
        self.agent_url = agent_url
        self.client = A2AClient(agent_url)
    
    async def send_message(self, message: str, stream: bool = False) -> dict:
        """Send a message to the advisor agent."""
        try:
            request = SendMessageRequest(
                message=message,
                stream=stream
            )
            
            if stream:
                print(f"🔄 Streaming request to advisor agent...")
                result_parts = []
                async for event in self.client.send_message_stream(request):
                    if hasattr(event, 'content'):
                        print(f"📝 Update: {event.content}")
                        result_parts.append(event.content)
                    elif hasattr(event, 'task'):
                        print(f"✅ Completed: {event.task.id}")
                        return {
                            "status": "success",
                            "content": "\n".join(result_parts),
                            "task_id": event.task.id
                        }
                        
            else:
                print(f"📨 Sending message to advisor agent...")
                task = await self.client.send_message(request)
                result = await self.client.wait_for_completion(task.id)
                
                return {
                    "status": "success",
                    "content": result.result if hasattr(result, 'result') else str(result),
                    "task_id": task.id
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_agent_info(self) -> dict:
        """Get agent card information."""
        try:
            agent_card = await self.client.get_agent_card()
            return {
                "status": "success",
                "agent_card": agent_card
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
    
    client = AdvisorAgentClient()
    
    print("=" * 60)
    print("🤖 DEMO: ADVISOR AGENT A2A CLIENT")
    print("=" * 60)
    
    # Get agent information
    print("\n📋 Getting agent information...")
    agent_info = await client.get_agent_info()
    if agent_info["status"] == "success":
        card = agent_info["agent_card"]
        print(f"✅ Agent: {card.name}")
        print(f"📝 Description: {card.description}")
        print(f"🛠️ Skills: {len(card.skills)} available")
        for skill in card.skills:
            print(f"   - {skill.name}: {skill.description}")
    else:
        print(f"❌ Failed to get agent info: {agent_info['error']}")
        return
    
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


async def interactive_mode():
    """Interactive chat mode with advisor agent."""
    client = AdvisorAgentClient()
    
    print("=" * 60)
    print("💬 INTERACTIVE MODE: ADVISOR AGENT A2A")
    print("=" * 60)
    print("Commands:")
    print("  - 'exit' or 'quit': Exit")
    print("  - 'info': Show agent information")
    print("  - 'stream <message>': Send streaming message")
    print("  - Or type your eyewear question directly")
    print("─" * 60)
    
    while True:
        try:
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
                    print(f"   Name: {card.name}")
                    print(f"   Version: {card.version}")
                    print(f"   URL: {card.url}")
                    print(f"   Skills: {len(card.skills)}")
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
                    
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


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
            
            print(f"❓ Question: {question}")
            result = await client.send_message(question)
            
            if result["status"] == "success":
                print(f"\n🤖 Answer:")
                print(result["content"])
            else:
                print(f"❌ Error: {result['error']}")
    else:
        # Default to interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main()) 