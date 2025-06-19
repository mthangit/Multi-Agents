#!/usr/bin/env python3
"""
A2A Client for testing Search Agent
"""

import asyncio
import sys
import base64
from typing import Optional
from pathlib import Path

from a2a.client import A2AClient
from a2a.types import SendMessageRequest


class SearchAgentClient:
    """Client for interacting with Search Agent via A2A protocol."""
    
    def __init__(self, agent_url: str = "http://localhost:10002"):
        self.agent_url = agent_url
        self.client = A2AClient(agent_url)
    
    async def send_message(self, message: str, stream: bool = False) -> dict:
        """Send a message to the search agent."""
        try:
            request = SendMessageRequest(
                message=message,
                stream=stream
            )
            
            if stream:
                print(f"🔄 Streaming search request...")
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
                print(f"🔍 Sending search request...")
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
    
    async def search_by_text(self, query: str, stream: bool = False) -> dict:
        """Search products by text query."""
        return await self.send_message(query, stream=stream)
    
    async def search_by_image(self, image_path: str, description: str = "", stream: bool = False) -> dict:
        """Search products by image."""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Encode to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create message with image data
            message = f"{description} data:image/jpeg;base64,{image_b64}"
            
            return await self.send_message(message, stream=stream)
            
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Error loading image: {str(e)}"
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


async def demo_text_search():
    """Demo text search queries for testing the search agent."""
    
    demo_questions = [
        "Tìm kính mát GUCCI cho nam",
        "Kính mát thể thao màu đen",
        "Gọng vuông titan cho khuôn mặt tròn",
        "Kính chống ánh sáng xanh cho dân văn phòng",
        "Kính thời trang nữ màu hồng"
    ]
    
    client = SearchAgentClient()
    
    print("=" * 60)
    print("🔍 DEMO: SEARCH AGENT A2A CLIENT - TEXT SEARCH")
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
    
    print(f"\n🎯 Testing with {len(demo_questions)} demo text searches:")
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n" + "─" * 50)
        print(f"🔍 [{i}] {question}")
        print("─" * 50)
        
        # Send search request
        result = await client.search_by_text(question, stream=False)
        
        if result["status"] == "success":
            print(f"🎯 Search Results:")
            print(result["content"])
            print(f"\n📊 Task ID: {result['task_id']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Small delay between requests
        await asyncio.sleep(1)


async def demo_image_search():
    """Demo image search if sample images are available."""
    
    client = SearchAgentClient()
    
    print("=" * 60)
    print("🖼️  DEMO: SEARCH AGENT A2A CLIENT - IMAGE SEARCH")
    print("=" * 60)
    
    # Look for sample images in current directory
    sample_images = []
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    current_dir = Path('.')
    for ext in image_extensions:
        sample_images.extend(current_dir.glob(f'*{ext}'))
        sample_images.extend(current_dir.glob(f'**/*{ext}'))  # Recursive search
    
    if not sample_images:
        print("⚠️  No sample images found in current directory")
        print("💡 To test image search:")
        print("   1. Place some eyewear images in the current directory")
        print("   2. Run the demo again")
        return
    
    # Test with first few images found
    test_images = sample_images[:3]
    
    print(f"📷 Found {len(sample_images)} images, testing with {len(test_images)}:")
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n" + "─" * 50)
        print(f"🖼️  [{i}] {image_path.name}")
        print("─" * 50)
        
        # Send image search request
        result = await client.search_by_image(
            str(image_path), 
            description="Tìm sản phẩm tương tự với hình ảnh này", 
            stream=False
        )
        
        if result["status"] == "success":
            print(f"🎯 Image Search Results:")
            print(result["content"])
            print(f"\n📊 Task ID: {result['task_id']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Small delay between requests
        await asyncio.sleep(2)


async def interactive_mode():
    """Interactive search mode with search agent."""
    client = SearchAgentClient()
    
    print("=" * 60)
    print("💬 INTERACTIVE MODE: SEARCH AGENT A2A")
    print("=" * 60)
    print("Commands:")
    print("  - 'exit' or 'quit': Exit")
    print("  - 'info': Show agent information")
    print("  - 'stream <query>': Send streaming search")
    print("  - 'image <path>': Search by image")
    print("  - Or type your search query directly")
    print("─" * 60)
    
    while True:
        try:
            user_input = input("\n🔍 Search: ").strip()
            
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
                    print(f"   Input modes: {', '.join(card.defaultInputModes)}")
                else:
                    print(f"❌ Error getting agent info: {agent_info['error']}")
                    
            elif user_input.lower().startswith('stream '):
                query = user_input[7:]  # Remove 'stream ' prefix
                print("🔄 Streaming mode...")
                result = await client.search_by_text(query, stream=True)
                if result["status"] == "error":
                    print(f"❌ Error: {result['error']}")
                    
            elif user_input.lower().startswith('image '):
                image_path = user_input[6:].strip()  # Remove 'image ' prefix
                print(f"🖼️  Searching by image: {image_path}")
                result = await client.search_by_image(image_path)
                
                if result["status"] == "success":
                    print(f"\n🎯 Image Search Results:")
                    print(result["content"])
                else:
                    print(f"❌ Error: {result['error']}")
                    
            else:
                # Regular text search
                print("🔍 Đang tìm kiếm...")
                result = await client.search_by_text(user_input)
                
                if result["status"] == "success":
                    print(f"\n🎯 Kết quả tìm kiếm:")
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
            await demo_text_search()
        elif sys.argv[1] == "image":
            await demo_image_search()
        elif sys.argv[1] == "chat":
            await interactive_mode()
        else:
            # Single search query mode
            query = " ".join(sys.argv[1:])
            client = SearchAgentClient()
            
            print(f"🔍 Search Query: {query}")
            result = await client.search_by_text(query)
            
            if result["status"] == "success":
                print(f"\n🎯 Search Results:")
                print(result["content"])
            else:
                print(f"❌ Error: {result['error']}")
    else:
        # Default to interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main()) 