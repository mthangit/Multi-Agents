import logging
from typing import List, Optional

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

from src.database.queries.cart import CartQuery
from src.database.queries.order import OrderQuery
from src.database.queries.product import ProductQuery

logger = logging.getLogger(__name__)

# --- Pydantic Models for Tool Inputs ---

class ProductByIdInput(BaseModel):
    product_id: int = Field(description="The ID of the product.")

class ProductByNameInput(BaseModel):
    name: str = Field(description="The name of the product.")

class AddToCartInput(BaseModel):
    product_id: int = Field(description="The ID of the product to add to the cart.")
    quantity: int = Field(description="The quantity of the product to add.", default=1)
    user_id: int = Field(description="The ID of the user.", default=1)

class UserIdInput(BaseModel):
    user_id: int = Field(description="The ID of the user.", default=1)

class CreateOrderInput(BaseModel):
    user_id: int = Field(description="The ID of the user.", default=1)
    shipping_address: Optional[str] = Field(None, description="The shipping address for the order.")
    phone: Optional[str] = Field(None, description="The contact phone number for the order.")
    payment_method: Optional[str] = Field(None, description="The payment method for the order.")

class OrderByIdInput(BaseModel):
    order_id: int = Field(description="The ID of the order.")

# --- Tool Functions ---

@tool(args_schema=ProductByIdInput)
def find_product_by_id(product_id: int) -> dict:
    """Finds a product by its ID."""
    logger.info(f"Finding product with ID: {product_id}")
    product = ProductQuery().get_product_by_id(product_id)
    if not product:
        return {"error": f"Product with ID {product_id} not found."}
    return product

@tool(args_schema=ProductByNameInput)
def find_product_by_name(name: str) -> List[dict]:
    """Finds products by their name."""
    logger.info(f"Finding products with name: {name}")
    products = ProductQuery().get_product_by_name(name)
    if not products:
        return [{"error": f"No products found with name containing '{name}'."}]
    return products

@tool(args_schema=AddToCartInput)
def add_to_cart(product_id: int, quantity: int, user_id: int = 1) -> dict:
    """Adds a specified quantity of a product to the user's shopping cart."""
    logger.info(f"Adding {quantity} of product {product_id} to cart for user {user_id}.")
    
    stock_info = OrderQuery().check_stock(product_id)
    if not stock_info:
        return {"error": f"Product with ID {product_id} not found."}
    if stock_info['stock'] < quantity:
        return {"error": f"Not enough stock for product {stock_info['name']}. Only {stock_info['stock']} left."}

    success = CartQuery().add_to_cart(user_id, product_id, quantity)
    if not success:
        return {"error": "Failed to add item to cart."}
    
    cart_items = CartQuery().get_cart_items(user_id)
    return {"message": f"Successfully added {quantity} of {stock_info['name']} to cart.", "cart": cart_items}

@tool(args_schema=UserIdInput)
def view_cart(user_id: int = 1) -> List[dict]:
    """Views the items in the user's shopping cart."""
    logger.info(f"Viewing cart for user {user_id}")
    cart_items = CartQuery().get_cart_items(user_id)
    if not cart_items:
        return [{"message": "Your cart is empty."}]
    return cart_items

@tool(args_schema=UserIdInput)
def clear_cart(user_id: int = 1) -> dict:
    """Clears all items from the user's shopping cart."""
    logger.info(f"Clearing cart for user {user_id}")
    success = CartQuery().clear_cart(user_id)
    if not success:
        return {"error": "Failed to clear cart."}
    return {"message": "Your cart has been cleared."}

@tool(args_schema=CreateOrderInput)
def create_order(user_id: int = 1, shipping_address: str = None, phone: str = None, payment_method: str = None) -> dict:
    """
    Creates an order from the user's cart. 
    If shipping_address, phone, or payment_method are not provided, it will ask the user for them.
    """
    logger.info(f"Creating order for user {user_id}")
    cart_items = CartQuery().get_cart_items(user_id)
    if not cart_items:
        return {"error": "Your cart is empty. Please add items before placing an order."}

    missing_info = []
    if not shipping_address:
        missing_info.append("shipping address")
    if not phone:
        missing_info.append("phone number")
    if not payment_method:
        missing_info.append("payment method")

    if missing_info:
        return {"message": f"Please provide your {', '.join(missing_info)} to complete the order."}

    try:
        order_id = OrderQuery().create_order_from_cart(
            user_id=user_id,
            shipping_address=shipping_address,
            phone=phone,
            payment_method=payment_method
        )
        if not order_id:
            return {"error": "Failed to create order."}
        
        order = OrderQuery().get_order_by_id(order_id)
        return {"message": "Order created successfully!", "order": order}
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return {"error": str(e)}

@tool(args_schema=OrderByIdInput)
def get_order_by_id(order_id: int) -> dict:
    """Gets information about an order by its ID."""
    logger.info(f"Getting order with ID: {order_id}")
    order = OrderQuery().get_order_by_id(order_id)
    if not order:
        return {"error": f"Order with ID {order_id} not found."}
    return order

@tool
def test_tool() -> str:
    """A simple test tool that always returns a success message."""
    logger.info("Test tool called successfully!")
    return "Test tool works perfectly!"

# List of all tools for the agent
all_tools = [
    find_product_by_id,
    find_product_by_name,
    add_to_cart,
    view_cart,
    clear_cart,
    create_order,
    get_order_by_id,
    test_tool,
] 