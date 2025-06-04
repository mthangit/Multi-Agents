Order Management Chatbot - Project Design Document (A2A Integrated)
1. Project Overview
1.1 Purpose
The Order Management Chatbot is an e-commerce system for managing orders, checking product stock, querying order history, and handling cart and wishlist operations. It provides a conversational chatbot interface and RESTful APIs for frontend and A2A (Agent-to-Agent) integration, leveraging Google’s Agent2Agent protocol for future-proof interoperability with external AI agents. Built with FastAPI, LangGraph, and MySQL, the system is scalable, secure, and extensible.
1.2 Objectives

Enable users to place orders, check stock, view order history, manage carts, and wishlists via chatbot or API.
Provide secure, documented RESTful APIs for frontend and third-party applications.
Support A2A integration with Google’s Agent2Agent protocol for agent-to-agent collaboration (e.g., with payment, inventory, or logistics agents).
Use the provided MySQL schema for data storage.
Leverage LangGraph for conversational state management.
Support Dockerized deployment for scalability.

1.3 Scope

In Scope:
RESTful APIs for order placement, stock checking, order querying, cart, and wishlist management.
Chatbot for order-related tasks (place order, check stock, check orders, manage cart/wishlist).
MySQL integration with provided schema.
API key authentication (extensible to JWT).
A2A-ready design with Agent Card and HTTP-based agent communication.
CORS support for frontend integration.
Dockerized deployment.


Out of Scope:
Payment gateway integration.
User authentication (login/register) beyond user lookup.
Multi-language chatbot support.



2. Requirements
2.1 Functional Requirements

Order Placement:
Users can place orders from cart or by specifying product ID and quantity.
System checks stock (products.stock) and updates invoices and invoice_details.
Orders link to users.id and addresses.id.
A2A: Support delegation to external payment or logistics agents.


Stock Checking:
Query stock by product_id from products.
Return details (name, stock, price, etc.).


Order History:
Retrieve orders by user_id from invoices and invoice_details.


Cart Management:
Add/remove products to/from carts and cart_details.
Support cart-to-order conversion.


Wishlist Management:
Add/remove products to/from wishlist and wishlist_details.


Chatbot Interaction:
Handle intents: place order, check stock, check orders, manage cart/wishlist.

API Access:
RESTful endpoints with JSON format.
Secured with API key (extensible to JWT).


A2A Integration:
Support Google’s Agent2Agent protocol for agent-to-agent communication.
Expose Agent Card (/.well-known/agent.json) for capability discovery.
Documented APIs via Swagger UI.



2.2 Non-Functional Requirements

Performance:
API response time < 500ms for 95% of requests.
Handle 100 concurrent users.


Security:
API key authentication.
Pydantic for input validation.
CORS restricted in production.
A2A: Secure agent communication (OAuth, API key).


Scalability:
Docker-based horizontal scaling.
A2A: Modular agent integration for extensibility.


Maintainability:
Modular code with separation of concerns.
Unit tests for API, chatbot, database, and A2A components.
Comprehensive documentation.


Reliability:
Database transactions for consistency.
Error handling for invalid inputs and A2A failures.



3. System Architecture
3.1 Overview
The system is a web-based application with:

Frontend: Any web/mobile app calling the API.
API Layer: FastAPI for RESTful endpoints.
Chatbot Layer: LangGraph for conversational logic.
A2A Layer: Agent2Agent protocol for agent-to-agent communication.
Database Layer: MySQL with provided schema.
Configuration: Environment variables (.env).
Deployment: Dockerized FastAPI, MySQL, and A2A agents.

3.2 Technology Stack

Backend: Python 3.9, FastAPI, Uvicorn
Chatbot: LangGraph, LangChain, Grok (xAI)
A2A: Google Agent2Agent (HTTP, JSON-RPC, SSE)
Database: MySQL 8.0
Validation: Pydantic
Deployment: Docker, docker-compose
Dependencies: mysql-connector-python, langchain-grok, google-a2a-sdk (future)

3.3 Architecture Diagram
[Frontend/Third-Party Apps]    [External AI Agents]
          |                           |
          | HTTP (JSON)               | A2A (HTTP, JSON-RPC, SSE)
          v                           v
[FastAPI - RESTful API & A2A Endpoint]
          |
          | LangGraph (Chatbot Logic)
          v
[MySQL Database]

4. Project Structure
4.1 Directory Structure
order_management/
├── src/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── order.py
│   │   │   ├── stock.py
│   │   │   ├── cart.py
│   │   │   ├── wishlist.py
│   │   │   ├── chat.py
│   │   │   ├── a2a.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   ├── a2a_auth.py
│   │   ├── models/
│   │   │   ├── order.py
│   │   │   ├── stock.py
│   │   │   ├── cart.py
│   │   │   ├── wishlist.py
│   │   │   ├── chat.py
│   │   │   ├── a2a.py
│   │   ├── main.py
│   ├── chatbot/
│   │   ├── nodes/
│   │   │   ├── welcome.py
│   │   │   ├── place_order.py
│   │   │   ├── check_stock.py
│   │   │   ├── check_order.py
│   │   │   ├── manage_cart.py
│   │   │   ├── manage_wishlist.py
│   │   ├── graph.py
│   │   ├── state.py
│   ├── database/
│   │   ├── schema.sql
│   │   ├── queries/
│   │   │   ├── order.py
│   │   │   ├── stock.py
│   │   │   ├── cart.py
│   │   │   ├── wishlist.py
│   │   ├── connection.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── logging.py
│   │   ├── a2a_config.py
│   ├── utils/
│   │   ├── helpers.py
│   │   ├── a2a_helpers.py
│   ├── tests/
│   │   ├── api/
│   │   │   ├── test_order.py
│   │   │   ├── test_stock.py
│   │   │   ├── test_cart.py
│   │   │   ├── test_wishlist.py
│   │   │   ├── test_a2a.py
│   │   ├── chatbot/
│   │   │   ├── test_graph.py
│   │   ├── database/
│   │   │   ├── test_queries.py
├── docs/
│   ├── api.md
│   ├── a2a_integration.md
│   ├── setup.md
│   ├── architecture.md
├── scripts/
│   ├── migrate_db.sh
│   ├── seed_data.sql
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile

4.2 File Descriptions

src/api/: FastAPI application.
endpoints/a2a.py: A2A-specific endpoints (e.g., /.well-known/agent.json).
middleware/a2a_auth.py: A2A authentication (OAuth, API key).
models/a2a.py: Pydantic models for A2A messages and tasks.


src/chatbot/: LangGraph chatbot.
graph.py: Includes A2A task delegation nodes.


src/database/: Database interactions.
schema.sql: Provided schema.


src/config/: Configuration.
a2a_config.py: A2A settings (Agent Card, remote agent endpoints).


src/utils/: Utilities.
a2a_helpers.py: A2A message formatting and task management.


docs/: Documentation.
a2a_integration.md: A2A setup and usage guide.



5. Detailed Design
5.1 Database Schema
The MySQL schema includes:

products: Product details (_id, name, price, stock, etc.).
users: User accounts (id, name, email, etc.).
addresses: User addresses.
carts, cart_details: Shopping cart.
invoices, invoice_details: Orders.
wishlist, wishlist_details: Wishlist.

Schema: See src/database/schema.sql (previously provided).
5.2 API Endpoints
FastAPI endpoints:

POST /order:
Request: { "user_id": int, "address_id": int, "cart_id": int, "payment_method": str }
Response: Invoice details.
A2A: Delegate payment to external agent.


GET /stock/{product_id}:
Response: Product details.
A2A: Query external inventory agent.


GET /orders/{user_id}:
Response: List of invoices.
A2A: Query logistics agent for status.


POST /cart, DELETE /cart/{cart_id}/item/{product_id}:
Manage cart.
A2A: Suggest products via recommendation agent.


POST /wishlist:
Manage wishlist.
A2A: Share with marketing agent.


POST /chat:
Request: { "message": str, "user_id": int }
Response: { "response": str }
A2A: Delegate tasks to remote agents.


GET /.well-known/agent.json:
Response: Agent Card (JSON) describing capabilities.
A2A: Enable discovery by external agents.


POST /a2a/task:
Request: A2A task object (e.g., { "task_id": str, "type": "payment", "data": {...} }).
Response: Task status or artifact.
A2A: Handle incoming tasks from remote agents.


GET /health:
Response: { "status": "healthy" }.



Authentication:

API key via api-key header.
A2A: OAuth or API key for agent-to-agent communication.

5.3 A2A Integration
The system is designed to support Google’s Agent2Agent protocol:

Agent Card (/.well-known/agent.json):{
  "name": "OrderManagementAgent",
  "version": "1.0.0",
  "capabilities": [
    {"type": "order_placement", "description": "Place e-commerce orders"},
    {"type": "stock_check", "description": "Check product stock"},
    {"type": "order_query", "description": "Query order history"},
    {"type": "cart_management", "description": "Manage user cart"},
    {"type": "wishlist_management", "description": "Manage user wishlist"}
  ],
  "endpoint": "/a2a/task",
  "auth": ["api_key", "oauth2"],
  "supported_formats": ["text", "json", "form"]
}


Task Management:
Tasks defined as JSON objects with task_id, type, data, and status.
Support short tasks (immediate) and long tasks (SSE updates).


Collaboration:
Chatbot delegates tasks (e.g., payment) to remote agents via POST /a2a/task.
External agents call POST /a2a/task to request services (e.g., order status).


Security:
Use OAuth or API key for A2A authentication.
Validate incoming A2A messages with Pydantic.



5.4 Chatbot Design (LangGraph)
5.4.1 State Definition
class ChatbotState(TypedDict):
    messages: List[HumanMessage | AIMessage]
    intent: str
    user_id: int
    product_id: str
    quantity: int
    cart_id: int
    address_id: int
    a2a_task_id: str

5.4.2 Nodes

welcome: Prompts user for action.
place_order: Processes orders, delegates payment to A2A agent.
check_stock: Queries stock, optionally via A2A.
check_order: Lists orders, queries logistics via A2A.
manage_cart, manage_wishlist: Manage cart/wishlist, use A2A for recommendations.
a2a_delegate: Handles A2A task creation and response.

5.4.3 Edges

From welcome, route based on intent.
A2A tasks transition to a2a_delegate node.

5.4.4 Intent Detection

Keyword-based (e.g., "order" → place_order).
Future: NLP for improved detection.

5.5 Database Queries
Key functions:

check_stock(product_id): Query products by _id.
place_order(user_id, address_id, cart_id): Create invoices, update products.stock.
check_order(user_id): Query invoices.
manage_cart, manage_wishlist: Update respective tables.
A2A: Queries may be delegated to external agents.

Sample Query (src/database/queries/order.py):
def place_order(user_id: int, address_id: int, cart_id: int) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT product_id, quantity FROM cart_details WHERE cart_id = %s", (cart_id,))
        items = cursor.fetchall()
        if not items:
            return {"status": "error", "message": "Cart is empty"}
        total_items = sum(item["quantity"] for item in items)
        total_price = 0
        for item in items:
            cursor.execute("SELECT price, stock FROM products WHERE _id = %s", (item["product_id"],))
            product = cursor.fetchone()
            if not product or product["stock"] < item["quantity"]:
                return {"status": "error", "message": f"Insufficient stock for product {item['product_id']}"}
            total_price += product["price"] * item["quantity"]
        cursor.execute(
            "INSERT INTO invoices (user_id, address_id, total_items, actual_price, total_price, payment_method) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, address_id, total_items, total_price, total_price, "cod")
        )
        invoice_id = cursor.lastrowid
        for item in items:
            cursor.execute(
                "INSERT INTO invoice_details (invoice_id, product_id, quantity, price) "
                "VALUES (%s, %s, %s, (SELECT price FROM products WHERE _id = %s))",
                (invoice_id, item["product_id"], item["quantity"], item["product_id"])
            )
            cursor.execute("UPDATE products SET stock = stock - %s WHERE _id = %s", (item["quantity"], item["product_id"]))
        cursor.execute("DELETE FROM cart_details WHERE cart_id = %s", (cart_id,))
        conn.commit()
        return {"status": "success", "message": f"Order placed, invoice ID: {invoice_id}"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

6. Implementation Details
6.1 Dependencies
fastapi==0.115.0
uvicorn==0.30.6
mysql-connector-python==9.0.0
pydantic==2.9.2
langchain==0.3.0
langchain-grok==0.1.0
langgraph==0.2.14
google-a2a-sdk==0.1.0  # Future dependency

6.2 Environment Variables
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=order_management
API_KEY=your-secret-api-key
XAI_API_KEY=your_xai_api_key
A2A_AGENT_ENDPOINT=https://api.example.com/a2a/task
A2A_AUTH_TOKEN=your-a2a-token

6.3 Sample API Implementation (src/api/endpoints/a2a.py)
from fastapi import APIRouter, Header
from src.api.models.a2a import AgentCard, A2ATaskRequest, A2ATaskResponse
from src.utils.a2a_helpers import create_task, get_task_status

router = APIRouter(prefix="/a2a", tags=["A2A"])

@router.get("/.well-known/agent.json", response_model=AgentCard)
async def get_agent_card():
    return AgentCard(
        name="OrderManagementAgent",
        version="1.0.0",
        capabilities=[
            {"type": "order_placement", "description": "Place e-commerce orders"},
            {"type": "stock_check", "description": "Check product stock"},
            # Other capabilities
        ],
        endpoint="/a2a/task",
        auth=["api_key", "oauth2"],
        supported_formats=["text", "json", "form"]
    )

@router.post("/task", response_model=A2ATaskResponse)
async def handle_a2a_task(task: A2ATaskRequest, api_key: str = Header(None)):
    validate_a2a_auth(api_key)
    if task.type == "order_placement":
        # Delegate to order placement logic
        result = place_order(task.data["user_id"], task.data["address_id"], task.data["cart_id"])
        return A2ATaskResponse(task_id=task.task_id, status="completed", result=result)
    # Handle other task types
    raise HTTPException(status_code=400, detail="Unsupported task type")

6.4 Sample Chatbot A2A Integration (src/chatbot/nodes/a2a_delegate.py)
from src.chatbot.state import ChatbotState
from src.utils.a2a_helpers import create_task
from langchain_core.messages import AIMessage

def a2a_delegate_node(state: ChatbotState) -> ChatbotState:
    if state["intent"] == "place_order" and state["payment_method"] == "external":
        task = create_task(
            task_type="payment",
            data={
                "invoice_id": state["invoice_id"],
                "total_price": state["total_price"],
                "user_id": state["user_id"]
            }
        )
        state["a2a_task_id"] = task["task_id"]
        state["messages"].append(AIMessage(content="Payment processing delegated to external agent."))
    return state

7. Deployment
7.1 Local Development

Install dependencies: pip install -r requirements.txt
Set up .env with MySQL, API, and A2A keys.
Initialize database: mysql -u your_username -p < src/database/schema.sql
Run API: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Access Swagger UI: http://localhost:8000/docs
Access Agent Card: http://localhost:8000/.well-known/agent.json

7.2 Docker Deployment

Build and run: docker-compose up --build
Access API at http://localhost:8000.

7.3 Cloud Deployment

Push Docker image to registry (e.g., Docker Hub).
Deploy on AWS ECS, GCP Cloud Run, or Kubernetes.
Configure A2A endpoints for external agent access.

8. Testing

Unit Tests: Use pytest in src/tests/.
API Tests: Test endpoints with httpx.
A2A Tests: Mock A2A tasks and validate Agent Card.
Chatbot Tests: Validate LangGraph transitions with A2A delegation.
Database Tests: Mock database queries.

9. Future Improvements

Implement JWT authentication for APIs.
Add rate limiting with slowapi.
Enhance chatbot with NLP intent detection.
Support order cancellation and updates.
Integrate A2A with Google ADK for full agent development.
Add monitoring with Prometheus/Grafana.
Expand A2A capabilities (e.g., logistics, marketing agents).

10. Conclusion
This updated design document integrates Google’s Agent2Agent (A2A) protocol into the Order Management Chatbot, enabling future-proof agent-to-agent collaboration. The system supports e-commerce features (order placement, cart/wishlist management) with a scalable API and conversational chatbot, ready for frontend and A2A integration. The modular design ensures easy extension for new A2A capabilities as the protocol matures.
