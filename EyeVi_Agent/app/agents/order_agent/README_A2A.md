# A2A Order Management Agent

A simplified, high-performance order management agent that implements the A2A (Agent-to-Agent) protocol for seamless communication with other AI agents.

## 🚀 Features

### Core Capabilities
- **Product Search**: Find products by name or ID
- **Cart Management**: Add, view, and clear shopping cart items
- **Order Processing**: Create and track orders
- **A2A Protocol**: Full Agent-to-Agent communication support
- **Streaming Responses**: Real-time response streaming
- **ReAct Pattern**: Reasoning and Acting for intelligent decision making

### Technical Features
- Built with **LangGraph** and **LangChain**
- **Google Gemini** LLM integration
- **FastAPI** web framework
- **SQLAlchemy** database integration
- **A2A SDK** for agent communication
- **Async/Await** for high performance

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API key
- A2A SDK installed

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
# Database configuration (optional)
DATABASE_URL=sqlite:///./orders.db
```

### 3. Database Setup (Optional)

If you want to use a database for persistent storage:

```bash
# Initialize database
python -c "from src.database import initialize_database_connections; initialize_database_connections()"
```

## 🏃‍♂️ Running the Agent

### Method 1: Quick Start Script

```bash
chmod +x start_agent.sh
./start_agent.sh [host] [port]
```

Examples:
```bash
./start_agent.sh                    # localhost:10000 (default)
./start_agent.sh localhost 8080     # localhost:8080
./start_agent.sh 0.0.0.0 10000      # All interfaces:10000
```

### Method 2: Direct Python

```bash
python main.py --host localhost --port 10000
```

## 🧪 Testing the Agent

### Enhanced Console Chat (Recommended)

```bash
# Simple launcher - beautiful interactive interface
python chat.py

# Or with custom URL
python console_chat.py http://localhost:10000
```

**Features:**
- 🎨 Beautiful colored interface with Vietnamese support
- 📝 Chat history and message tracking
- 🛠️ Interactive skills display
- 📊 Real-time status information
- 💬 Command system (`/help`, `/history`, `/skills`, `/status`, `/quit`)
- 🔄 Auto-clearing screen for clean experience
- ⌨️ Keyboard shortcuts (Ctrl+C for menu)

### Basic Python Client

```bash
# Interactive chat mode
python client.py chat

# Single question mode
python client.py "Tìm sản phẩm iPhone"
```

### Manual Testing

Once the agent is running, you can:

1. **View Agent Card**: `http://localhost:10000/.well-known/agent.json`
2. **A2A Endpoint**: `http://localhost:10000/`
3. **Direct API**: `http://localhost:10000/chatbot/chat`

## 📡 A2A Protocol Usage

### From Another Agent

```python
from a2a.client import A2AClient
from a2a.types import SendMessageRequest

# Connect to the Order Agent
client = A2AClient("http://localhost:10000")

# Send a message
request = SendMessageRequest(
    message="Tìm sản phẩm iPhone",
    stream=False
)

task = await client.send_message(request)
result = await client.wait_for_completion(task.id)
print(result)
```

### Streaming Example

```python
# Streaming request
stream_request = SendMessageRequest(
    message="Thêm 2 sản phẩm ID 123 vào giỏ hàng",
    stream=True
)

async for event in client.send_message_stream(stream_request):
    if hasattr(event, 'content'):
        print(f"Update: {event.content}")
    elif hasattr(event, 'task'):
        print(f"Completed: {event.task.id}")
        break
```

## 🛠️ Available Tools

The agent supports the following operations:

### Product Operations
- `find_product_by_id(product_id)` - Find product by ID
- `find_product_by_name(name)` - Search products by name

### Cart Operations
- `add_to_cart(product_id, quantity, user_id)` - Add items to cart
- `view_cart(user_id)` - View cart contents
- `clear_cart(user_id)` - Clear all cart items

### Order Operations
- `create_order(user_id, shipping_address, phone, payment_method)` - Create new order
- `get_order_by_id(order_id)` - Get order information

## 💬 Example Conversations

### Vietnamese (Native)
```
User: "Tìm sản phẩm iPhone"
Agent: Tôi đã tìm thấy các sản phẩm iPhone sau: [product list]

User: "Thêm 2 sản phẩm ID 123 vào giỏ hàng"
Agent: Đã thêm 2 sản phẩm vào giỏ hàng thành công!

User: "Tạo đơn hàng"
Agent: Để tạo đơn hàng, tôi cần thông tin địa chỉ, số điện thoại và phương thức thanh toán.
```

### English
```
User: "Find iPhone products"
Agent: I found the following iPhone products: [product list]

User: "Add 2 items with ID 123 to cart"
Agent: Successfully added 2 items to your cart!
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   A2A Client    │───▶│  A2A Server     │───▶│ SimplifiedBot   │
│   (Other Agent) │    │  (main.py)      │    │ (ReAct Agent)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ OrderExecutor   │    │     Tools       │
                       │ (A2A Bridge)    │    │ (Actual Logic)  │
                       └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Agent Card Customization

Edit `main.py` to customize the agent card:

```python
agent_card = AgentCard(
    name='Your Agent Name',
    description='Your agent description',
    skills=[
        AgentSkill(
            id='your_skill',
            name='Your Skill',
            description='Skill description',
            examples=['Example 1', 'Example 2']
        )
    ]
)
```

### Tool Customization

Add new tools in `src/chatbot/tools.py`:

```python
@tool
def your_new_tool(param: str) -> dict:
    """Your tool description."""
    # Your logic here
    return {"result": "success"}

# Add to all_tools list
all_tools.append(your_new_tool)
```

## 🐛 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Make sure your `.env` file contains the API key
   - Check the key is valid and has proper permissions

2. **"Database connection failed"**
   - The agent will continue to work without database
   - Check database URL in `.env` if persistence is needed

3. **"Agent not responding"**
   - Check if the agent is running on the correct port
   - Verify firewall settings
   - Check logs for detailed error messages

### Logs

The agent provides detailed logging. Check console output for:
- Agent startup information
- Request processing details
- Error messages with stack traces

## 📈 Performance

- **Response Time**: < 2 seconds for simple queries
- **Streaming**: Real-time updates during processing
- **Concurrency**: Supports multiple simultaneous requests
- **Memory**: Optimized for low memory usage

## 🔒 Security

- Environment variables for sensitive data
- Request validation
- Error handling to prevent information leakage
- Async timeout protection

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `python test_a2a_client.py`
5. Submit a pull request

## 📄 License

[Your License Here]

## 🤝 Support

For questions or issues:
- Check the troubleshooting section
- Review logs for error details
- Create an issue with reproduction steps

---

**Built with ❤️ using A2A Protocol, LangGraph, and Google Gemini** 