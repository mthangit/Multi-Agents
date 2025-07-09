"""
Simplified Order Agent với LangGraph đơn giản
Chỉ hỗ trợ 5 chức năng cơ bản:
1. Tìm sản phẩm theo ID
2. Tìm sản phẩm theo tên  
3. Lấy thông tin user
4. Lấy lịch sử đơn hàng
5. Tạo đơn hàng trực tiếp
"""

import logging
from typing import Annotated, TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
import json
from decimal import Decimal
from datetime import datetime, date
from src.database.queries.product import ProductQuery
from src.database.queries.user import UserQuery
from src.database.queries.order import OrderQuery
import os
import re

logger = logging.getLogger(__name__)

# ============ CUSTOM JSON ENCODER ============
class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder để xử lý Decimal và datetime"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

def safe_json_dumps(data):
    """Safe JSON dumps with Decimal handling"""
    return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False)

# ============ STATE DEFINITION ============
class SimpleOrderState(TypedDict):
    """State đơn giản cho order agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    current_user_id: int
    # Thêm các field cho format response
    products: List[dict]
    orders: List[dict] 
    user_info: dict
    count: int
    search_type: str
    operation_type: str
    llm_response: str
    formatted_response: dict

# ============ SIMPLIFIED TOOLS ============

@tool
def find_product_by_id(product_id: int) -> str:
    """
    Find product by ID
    Args:
        product_id: ID của sản phẩm cần tìm
    Returns:
        Thông tin sản phẩm dạng string kèm data JSON
    """
    try:
        logger.info(f"🔍 Tìm sản phẩm ID: {product_id}")
        product = ProductQuery().get_product_by_id(product_id)
        if not product:
            return f"❌ Không tìm thấy sản phẩm với ID {product_id}"
        
        # Text hiển thị cho user
        display_text = f"""✅ Sản phẩm tìm thấy:
📦 ID: {product.get('id', 'N/A')}
🏷️ Tên: {product.get('name', 'N/A')}
💰 Giá: {product.get('price', 'N/A'):,} VND
📝 Mô tả: {product.get('description', 'N/A')}
📊 Tồn kho: {product.get('stock', 'N/A')} sản phẩm"""
        
        # Data cho client xử lý
        data_dict = {
            "type": "product_detail",
            "data": product
        }
        
        # Kết hợp với marker
        return f"{display_text}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi tìm sản phẩm ID {product_id}: {e}")
        return f"❌ Lỗi: {str(e)}"

@tool
def find_product_by_name(product_name: str) -> str:
    """
    Find products by name
    Args:
        product_name: Tên sản phẩm cần tìm
    Returns:
        Danh sách sản phẩm dạng string kèm data JSON
    """
    try:
        logger.info(f"🔍 Tìm sản phẩm tên: {product_name}")
        products = ProductQuery().get_product_by_name(product_name)
        if not products:
            return f"❌ Không tìm thấy sản phẩm nào có tên chứa '{product_name}'"
        
        # Text hiển thị cho user
        result = f"✅ Tìm thấy {len(products)} sản phẩm:\n"
        for i, product in enumerate(products[:5], 1):  # Giới hạn 5 sản phẩm
            result += f"\n{i}. 📦 ID: {product.get('id')} | {product.get('name')} | 💰 {product.get('price', 0):,} VND"
        if len(products) > 5:
            result += f"\n... và {len(products) - 5} sản phẩm khác"
        
        # Data cho client xử lý
        data_dict = {
            "type": "product_list",
            "data": products[:5],  # Giới hạn 5 sản phẩm
            "total_count": len(products),
            "search_term": product_name
        }
        
        # Kết hợp với marker
        return f"{result}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi tìm sản phẩm tên '{product_name}': {e}")
        return f"❌ Lỗi: {str(e)}"

@tool
def get_user_info(user_id: int) -> str:
    """
    Get user information by ID
    Args:
        user_id: ID người dùng cần lấy thông tin
    Returns:
        Thông tin người dùng dạng string kèm data JSON
    """
    try:
        logger.info(f"👤 Lấy thông tin user ID: {user_id}")
        user = UserQuery().get_user_by_id(user_id)
        if not user:
            return f"❌ Không tìm thấy người dùng với ID {user_id}"
        
        # Text hiển thị cho user
        display_text = f"""✅ Thông tin người dùng:
👤 ID: {user.get('id', 'N/A')}
📛 Tên: {user.get('name', 'N/A')}
📧 Email: {user.get('email', 'N/A')}
📞 Điện thoại: {user.get('phone', 'Chưa cập nhật')}
🏠 Địa chỉ: {user.get('address', 'Chưa cập nhật')}"""
        
        # Data cho client xử lý
        data_dict = {
            "type": "user_info",
            "data": user
        }
        
        # Kết hợp với marker
        return f"{display_text}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi lấy thông tin user {user_id}: {e}")
        return f"❌ Lỗi: {str(e)}"

@tool
def get_user_orders(user_id: int, limit: int = 5) -> str:
    """
    Get user order history
    Args:
        user_id: ID người dùng
        limit: Số lượng đơn hàng tối đa (mặc định 5)
    Returns:
        Lịch sử đơn hàng dạng string kèm data JSON
    """
    try:
        logger.info(f"📋 Lấy lịch sử đơn hàng user ID: {user_id}")
        orders = OrderQuery().get_orders_by_user_id(user_id, limit)
        if not orders:
            return f"❌ Người dùng ID {user_id} chưa có đơn hàng nào"
        
        # Text hiển thị cho user
        result = f"✅ Lịch sử {len(orders)} đơn hàng gần nhất:\n"
        for i, order in enumerate(orders, 1):
            result += f"""
{i}. 🆔 Đơn #{order.get('id')} | 💰 {order.get('total_price', 0):,} VND
   📦 {order.get('total_items', 0)} sản phẩm | 📊 {order.get('order_status', 'N/A')}
   💳 {order.get('payment', 'COD')} | 📅 {order.get('created_at', 'N/A')}"""
        
        # Data cho client xử lý
        data_dict = {
            "type": "order_history",
            "data": orders,
            "user_id": user_id,
            "limit": limit
        }
        
        # Kết hợp với marker
        return f"{result}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi lấy lịch sử đơn hàng user {user_id}: {e}")
        return f"❌ Lỗi: {str(e)}"

@tool
def collect_order_info(user_id: int, product_items: str) -> str:
    """
    Thu thập thông tin cần thiết để tạo đơn hàng (bước 1)
    Args:
        user_id: ID người dùng
        product_items: Danh sách sản phẩm dạng JSON string: [{"product_id": 1, "quantity": 2}, ...]
    Returns:
        Thông tin sản phẩm và yêu cầu thông tin giao hàng
    """
    try:
        logger.info(f"📋 Thu thập thông tin đặt hàng cho user {user_id}")
        
        # Parse danh sách sản phẩm
        try:
            items = json.loads(product_items)
        except json.JSONDecodeError:
            return "❌ Danh sách sản phẩm không đúng định dạng JSON"
        if not items:
            return "❌ Danh sách sản phẩm trống!"
        
        # Kiểm tra thông tin sản phẩm và tồn kho
        product_query = ProductQuery()
        order_summary = "📋 **XÁC NHẬN ĐƠN HÀNG:**\n\n"
        total_estimated = 0
        validated_items = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            # Query thông tin sản phẩm
            product = product_query.get_product_by_id(product_id)
            if not product:
                return f"❌ Sản phẩm ID {product_id} không tồn tại!"
            
            # Kiểm tra tồn kho
            stock = product.get('stock', 0)
            if stock < quantity:
                return f"❌ Sản phẩm '{product.get('name')}' chỉ còn {stock} sản phẩm, không đủ cho số lượng {quantity}!"
             
            # Tính tiền
            price = product.get('newPrice', 0)
            subtotal = price * quantity
            total_estimated += subtotal
            validated_items.append(item)
            
            # Thêm vào summary
            order_summary += f"📦 {product.get('name')}\n"
            order_summary += f"   💰 {price:,} VND x {quantity} = {subtotal:,} VND\n"
            order_summary += f"   📊 Tồn kho: {stock} sản phẩm\n\n"
        
        order_summary += f"💰 **TỔNG TIỀN: {total_estimated:,} VND**\n\n"
        
        # Yêu cầu thông tin giao hàng
        order_summary += """🚨 **CẦN THÔNG TIN GIAO HÀNG:**

Để hoàn tất đơn hàng, vui lòng cung cấp:
📍 **Địa chỉ giao hàng**: Ví dụ: "123 Nguyễn Trãi, Quận 1, TP.HCM"
📞 **Số điện thoại**: Ví dụ: "0901234567"
💳 **Hình thức thanh toán**: 
   - "COD" (Thanh toán khi nhận hàng)
   - "Banking" (Chuyển khoản ngân hàng)

📝 **Ví dụ trả lời:** "Giao đến 123 Nguyễn Trãi, TP.HCM, số điện thoại 0901234567, thanh toán COD"
"""
        
        # Data cho client xử lý
        data_dict = {
            "type": "order_info_request",
            "data": {
                "items": validated_items,
                "estimated_total": total_estimated,
                "user_id": user_id,
                "products_info": [product_query.get_product_by_id(item['product_id']) for item in validated_items]
            }
        }
        
        return f"{order_summary}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi thu thập thông tin đặt hàng user {user_id}: {e}")
        return f"❌ Lỗi: {str(e)}"

@tool
def create_order_directly(user_id: int, product_items: str, shipping_address: str, phone: str, payment_method: str) -> str:
    """
    Tạo đơn hàng với thông tin đầy đủ (bước 2 - sau khi đã thu thập thông tin)
    Args:
        user_id: ID người dùng
        product_items: Danh sách sản phẩm dạng JSON string: [{"product_id": 1, "quantity": 2}, ...]
        shipping_address: Địa chỉ giao hàng (BẮT BUỘC)
        phone: Số điện thoại liên lạc (BẮT BUỘC)
        payment_method: Phương thức thanh toán (COD hoặc Banking - BẮT BUỘC)
    Returns:
        Kết quả tạo đơn hàng dạng string kèm data JSON
    """
    try:
        logger.info(f"🛍️ Tạo đơn hàng với thông tin đầy đủ cho user {user_id}")
        
        # Kiểm tra thông tin bắt buộc
        if not shipping_address or not shipping_address.strip():
            return "❌ Thiếu địa chỉ giao hàng! Vui lòng cung cấp địa chỉ giao hàng."
        
        if not phone or not phone.strip():
            return "❌ Thiếu số điện thoại! Vui lòng cung cấp số điện thoại liên lạc."
        
        # Kiểm tra phương thức thanh toán hợp lệ
        valid_payment_methods = ["COD", "Banking"]
        if not payment_method or payment_method not in valid_payment_methods:
            return f"❌ Phương thức thanh toán không hợp lệ! Chỉ chấp nhận: {', '.join(valid_payment_methods)}"
        
        # Parse danh sách sản phẩm
        try:
            items = json.loads(product_items)
        except json.JSONDecodeError:
            return "❌ Danh sách sản phẩm không đúng định dạng JSON"
        if not items:
            return "❌ Danh sách sản phẩm trống!"
        
        # TẠO ĐƠN HÀNG VỚI THÔNG TIN ĐÃ VALIDATE
        logger.info("🛍️ Tạo đơn hàng với thông tin đầy đủ...")
        order_id = OrderQuery().create_order(
            user_id=user_id,
            items=items,
            shipping_address=shipping_address.strip(),
            phone=phone.strip(),
            payment_method=payment_method
        )
        
        if not order_id:
            return "❌ Không thể tạo đơn hàng. Vui lòng thử lại."
        
        # LẤY THÔNG TIN ĐƠN HÀNG ĐÃ TẠO
        order = OrderQuery().get_order_by_id(order_id)
        
        # Tính tổng tiền để hiển thị
        total_estimated = sum(item.get('newPrice', 0) * item.get('quantity', 1) for item in order.get('items', []))
        
        # Text hiển thị cho user
        display_text = f"""✅ **ĐƠN HÀNG ĐƯỢC TẠO THÀNH CÔNG!**

🆔 Mã đơn hàng: #{order_id}
💰 Tổng tiền: {order.get('total_price', 0):,} VND
📦 Tổng số sản phẩm: {order.get('total_items', 0)}
🚚 Địa chỉ giao hàng: {order.get('shipping_address', 'N/A')}
📞 Số điện thoại: {order.get('phone', 'N/A')}
💳 Phương thức thanh toán: {order.get('payment', 'COD')}
📊 Trạng thái: {order.get('order_status', 'pending')}

🎉 Cảm ơn bạn đã đặt hàng! Đơn hàng sẽ được xử lý trong thời gian sớm nhất."""
        
        # Data cho client xử lý
        data_dict = {
            "type": "order_created",
            "data": {
                "order": order,
                "items": items,
                "estimated_total": total_estimated
            }
        }
        
        # Kết hợp với marker
        return f"{display_text}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi tạo đơn hàng cho user {user_id}: {e}")
        return f"❌ Lỗi: {str(e)}"
    
@tool
def update_order_info(order_id: int, shipping_address: str, phone: str, payment_method: str) -> str:
    """
    Update order information
    Args:
        order_id: ID đơn hàng cần cập nhật
        shipping_address: Địa chỉ giao hàng mới
        phone: Số điện thoại liên lạc mới
        payment_method: Phương thức thanh toán mới (COD hoặc Banking)
    Returns:
        Kết quả cập nhật đơn hàng dạng string kèm data JSON
    """
    try:
        logger.info(f"🔄 Cập nhật thông tin đơn hàng ID: {order_id}")
        
        # Kiểm tra phương thức thanh toán hợp lệ
        valid_payment_methods = ["COD", "Banking"]
        if payment_method not in valid_payment_methods:
            return f"❌ Phương thức thanh toán không hợp lệ! Chỉ chấp nhận: {', '.join(valid_payment_methods)}"
        
        order = OrderQuery().get_order_by_id(order_id)
        if not order:
            return f"❌ Đơn hàng ID {order_id} không tồn tại!"
        
        # Cập nhật thông tin đơn hàng
        OrderQuery().update_order(
            order_id=order_id,
            shipping_address=shipping_address,
            phone=phone,    
            payment_method=payment_method
        )
        
        # Lấy thông tin đơn hàng sau khi cập nhật
        updated_order = OrderQuery().get_order_by_id(order_id)
        
        # Text hiển thị cho user
        display_text = f"""✅ Đơn hàng ID {order_id} đã được cập nhật thành công!

📋 **THÔNG TIN ĐƠN HÀNG MỚI:**
🆔 Mã đơn hàng: #{order_id}
📊 Trạng thái: {updated_order.get('order_status', 'pending')}
🚚 Địa chỉ giao hàng: {updated_order.get('shipping_address', 'N/A')}
📞 Số điện thoại: {updated_order.get('phone', 'N/A')}
💳 Phương thức thanh toán: {updated_order.get('payment', 'COD')}"""
        
        # Data cho client xử lý
        data_dict = {
            "type": "order_updated",
            "data": {
                "order_id": order_id,
                "updated_order": updated_order
            }
        }
        
        # Kết hợp với marker
        return f"{display_text}\n\n[DATA_MARKER]{safe_json_dumps(data_dict)}[/DATA_MARKER]"
        
    except Exception as e:
        logger.error(f"Lỗi cập nhật thông tin đơn hàng ID {order_id}: {e}")
        return f"❌ Lỗi: {str(e)}"

# ============ HELPER FUNCTIONS ============

def parse_agent_response(response: str) -> dict:
    """
    Parse agent response để tách text và data
    Args:
        response: Response từ agent
    Returns:
        Dict chứa text và data
    """
    # Tìm data marker
    data_pattern = r'\[DATA_MARKER\](.*?)\[/DATA_MARKER\]'
    data_match = re.search(data_pattern, response, re.DOTALL)
    
    if data_match:
        # Tách text và data
        text_content = response.replace(data_match.group(0), '').strip()
        try:
            data_content = json.loads(data_match.group(1))
        except json.JSONDecodeError:
            data_content = None
        
        return {
            "text": text_content,
            "data": data_content,
            "has_data": True
        }
    else:
        return {
            "text": response,
            "data": None,
            "has_data": False
        }

# ============ SIMPLIFIED LANGGRAPH AGENT ============

class SimplifiedOrderAgent:
    """Agent đơn giản cho quản lý đơn hàng"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        
        # 6 tools cơ bản với tên chuẩn
        self.tools = [
            find_product_by_id, 
            find_product_by_name,
            get_user_info,
            get_user_orders,
            collect_order_info,
            create_order_directly,
            update_order_info
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Tạo workflow đơn giản
        self.graph = self._create_simple_graph()
    
    def _create_simple_graph(self) -> StateGraph:
        """Tạo workflow LangGraph với 3 nodes: assistant, tools, format_response"""
        workflow = StateGraph(SimpleOrderState)
        
        # 3 nodes: assistant, tools, và format_response
        workflow.add_node("assistant", self._assistant_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("format_response", self._format_response_node)
        
        # Flow mới: START → assistant → tools → assistant → format_response → END
        workflow.add_edge(START, "assistant")
        workflow.add_conditional_edges(
            "assistant",
            self._should_use_tools,
            {
                "tools": "tools",
                "format": "format_response"
            }
        )
        workflow.add_edge("tools", "assistant")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    def _assistant_node(self, state: SimpleOrderState):
        """Node chính xử lý chat"""
        messages = state["messages"]
        
        # Thêm system message đơn giản
        if not messages or not any(isinstance(msg, AIMessage) for msg in messages):
            system_prompt = """
            Bạn là trợ lý đơn hàng thông minh. Bạn có thể:

🔍 Tìm sản phẩm theo ID: find_product_by_id(product_id)
🔍 Tìm sản phẩm theo tên: find_product_by_name(product_name)  
👤 Lấy thông tin user: get_user_info(user_id)
📋 Lấy lịch sử đơn hàng: get_user_orders(user_id, limit)
📝 Thu thập thông tin đặt hàng: collect_order_info(user_id, product_items)
🛍️ Tạo đơn hàng với thông tin đầy đủ: create_order_directly(user_id, product_items, shipping_address, phone, payment_method)
🔄 Cập nhật thông tin đơn hàng: update_order_info(order_id, shipping_address, phone, payment_method)

📝 LƯU Ý QUAN TRỌNG:
- Nếu người dùng KHÔNG cung cấp user_id cụ thể, hãy sử dụng user_id = 1 làm mặc định
- Khi người dùng hỏi "thông tin của tôi", "đơn hàng của tôi" mà không nói rõ ID → dùng user_id = 1
- Chỉ khi người dùng nói rõ "user 5", "người dùng 10" thì mới dùng ID đó
- Khi gọi tool, bạn có thể thêm text bổ sung thân thiện trước khi gọi tool

🎯 HƯỚNG DẪN TRÍCH XUẤT THÔNG TIN TỪ USER MESSAGE:

1. 🔍 TÌMKIẾM SẢN PHẨM:
   - "sản phẩm ID 5", "product 10", "sp 15" → product_id = số
   - "tìm iPhone", "sản phẩm tên Laptop", "có Samsung nào không" → product_name = tên
   - "xem sản phẩm 123" → find_product_by_id(123)
   - "tìm điện thoại" → find_product_by_name("điện thoại")

2. 👤 THÔNG TIN USER:
   - "thông tin tôi", "profile của tôi" → get_user_info(1)
   - "user 5", "người dùng 10", "khách hàng 15" → get_user_info(số)
   - "tôi là ai", "tài khoản của tôi" → get_user_info(1)

3. 📋 LỊCH SỬ ĐƠN HÀNG:
   - "đơn hàng của tôi", "lịch sử mua hàng" → get_user_orders(1)
   - "5 đơn hàng gần nhất", "10 đơn cuối" → get_user_orders(1, số)
   - "đơn hàng user 5" → get_user_orders(5)

4. 🛍️ TẠO ĐƠN HÀNG (FLOW MỚI - 2 BƯỚC BẮT BUỘC):
   
   ⚠️ **QUY TẮC QUAN TRỌNG:** MỌI ĐƠN HÀNG ĐỀU PHẢI HỎI THÔNG TIN ĐẦY ĐỦ!
   
   BƯỚC 1: collect_order_info(user_id, product_items)
   - YÊU CẦU user cung cấp: số lượng sản phẩm, địa chỉ, số điện thoại, hình thức thanh toán
   
   BƯỚC 2: create_order_directly(user_id, product_items, shipping_address, phone, payment_method) 
   - CHỈ gọi SAU KHI user đã cung cấp đầy đủ thông tin
   - Tất cả thông tin đều BẮT BUỘC: product_items, shipping_address, phone, payment_method
   - Hình thức thanh toán CHỈ chấp nhận: "COD" hoặc "Banking"
      
   Ví dụ flow đúng:
   User: "đặt 2 sản phẩm ID 1"
   → Gọi collect_order_info(1, '[{"product_id": 1, "quantity": 2}]')
   → Hệ thống hỏi: số lượng sản phẩm, địa chỉ, SĐT, hình thức thanh toán
   User: "Mua 1 sản phẩm, giao đến 123 Nguyễn Trãi, SĐT 0901234567, thanh toán COD"
   → Gọi create_order_directly(1, '[{"product_id": 1, "quantity": 2}]', "123 Nguyễn Trãi", "0901234567", "COD")

5. 🔄 CẬP NHẬT ĐƠN HÀNG:
   - "cập nhật đơn 123", "sửa đơn hàng 456" → order_id = số
   - "đổi địa chỉ giao hàng" → shipping_address = địa chỉ mới
   - "cập nhật số điện thoại" → phone = số mới
   - "đổi phương thức thanh toán" → payment_method = phương thức mới

6. 📞 TRÍCH XUẤT THÔNG TIN LIÊN HỆ:
   - Số điện thoại: 09xx, 08xx, 07xx, 03xx, 05xx + 8 chữ số
   - Địa chỉ: "đến", "giao", "địa chỉ", "tại" + thông tin sau đó
   - Phương thức thanh toán CHỈ 2 LOẠI:
     * "COD" (thanh toán khi nhận hàng, tiền mặt) 
     * "Banking" (chuyển khoản ngân hàng)

Ví dụ trích xuất từ user message:
- "Giao đến 123 Nguyễn Trãi, SĐT 0901234567, thanh toán COD"
- "Địa chỉ 456 Lê Lợi, phone 0987654321, chuyển khoản" → Banking
- "456 Trần Hưng Đạo, 0912345678, COD"

HƯỚNG DẪN TRẢ LỜI:
- Khi gọi tool, bạn có thể thêm text bổ sung thân thiện như "Tôi sẽ tìm sản phẩm cho bạn", "Đây là thông tin sản phẩm:", v.v.
- Sau đó gọi tool để lấy thông tin chi tiết
- Đảm bảo trả lời đầy đủ thông tin, trả về thêm DATA_MARKER để client xử lý
- Luôn trả lời bằng tiếng Việt và thân thiện!

🚫 QUY TẮC BẢNG MAT KHAI BÁNG THÔNG TIN VỚI USER:
- TUYỆT ĐỐI KHÔNG hiển thị các ID (product_id, user_id, order_id) khi giao tiếp với user
- Chỉ sử dụng ID để gọi tool bên trong, không bao giờ hiển thị trong câu trả lời
- Luôn dùng thông tin dễ hiểu: tên sản phẩm, tên khách hàng, địa chỉ, số điện thoại
- Khi xác nhận đơn hàng: "Xác nhận đặt 2 chiếc iPhone 15 Pro Max (500,000 VND/chiếc)"
- Không nói: "Xác nhận đặt product_id 5 cho user_id 1"
"""
            
            messages = [AIMessage(content=system_prompt)] + messages
        
        response = self.llm_with_tools.invoke(messages)
        
        # Trả về response nguyên bản (có thể cả content và tool calls)
        return {"messages": [response]}
    
    def _tools_node(self, state: SimpleOrderState):
        """Node thực thi tools"""
        messages = state["messages"]
        last_message = messages[-1]
        
        results = []
        for tool_call in last_message.tool_calls:
            try:
                # Tìm tool function
                tool_func = next(
                    tool for tool in self.tools 
                    if tool.name == tool_call["name"]
                )
                
                # Gọi tool
                result = tool_func.invoke(tool_call["args"])
                results.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    )
                )
            except Exception as e:
                logger.error(f"Lỗi tool {tool_call['name']}: {e}")
                results.append(
                    ToolMessage(
                        content=f"❌ Lỗi: {str(e)}",
                        tool_call_id=tool_call["id"]
                    )
                )
        
        return {"messages": results}
    
    def _format_response_node(self, state: SimpleOrderState):
        """Node format kết quả cuối cùng theo chuẩn"""
        messages = state["messages"]
        
        # Parse thông tin từ messages
        products = []
        orders = []
        user_info = {}
        count = 0
        search_type = "general"
        operation_type = "general"
        llm_response = ""
        
        # Tìm AI response và tool responses
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.content:
                llm_response = msg.content
            elif isinstance(msg, ToolMessage) and msg.content:
                # Parse tool response để tách data
                parsed = parse_agent_response(msg.content)
                if parsed["has_data"] and parsed["data"]:
                    data_type = parsed["data"].get("type")
                    data_content = parsed["data"].get("data")
                    
                    if data_type == "product_detail":
                        products = [data_content]
                        count = 1
                        search_type = "product_detail"
                        operation_type = "find_product"
                    elif data_type == "product_list":
                        products = data_content
                        count = parsed["data"].get("total_count", len(data_content))
                        search_type = "product_search"
                        operation_type = "find_product"
                    elif data_type == "user_info":
                        user_info = data_content
                        count = 1
                        search_type = "user_info"
                        operation_type = "get_user"
                    elif data_type == "order_history":
                        orders = data_content
                        count = len(data_content)
                        search_type = "order_history"
                        operation_type = "get_orders"
                    elif data_type == "order_created":
                        orders = [data_content.get("order", {})]
                        count = 1
                        search_type = "order_created"
                        operation_type = "create_order"
                    elif data_type == "order_updated":
                        orders = [data_content.get("updated_order", {})]
                        count = 1
                        search_type = "order_updated"
                        operation_type = "update_order"
                    elif data_type == "order_info_request":
                        # Đây là bước thu thập thông tin, chưa tạo đơn hàng
                        products = data_content.get("products_info", [])
                        count = len(data_content.get("items", []))
                        search_type = "order_info_request"
                        operation_type = "collect_order_info"
        
        # Tạo formatted response theo chuẩn
        formatted_response = {
            "products": products,
            "orders": orders,
            "user_info": user_info,
            "count": count,
            "llm_response": llm_response,
            "search_type": search_type,
            "operation_type": operation_type
        }
        
        return {
            "products": products,
            "orders": orders,
            "user_info": user_info,
            "count": count,
            "search_type": search_type,
            "operation_type": operation_type,
            "llm_response": llm_response,
            "formatted_response": formatted_response
        }
    
    def _should_use_tools(self, state: SimpleOrderState) -> Literal["tools", "format"]:
        """Quyết định có dùng tools không"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return "format"
    
    def chat(self, message: str, user_id: int = 1) -> dict:
        """Chat với agent - trả về format chuẩn"""
        try:
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "current_user_id": user_id,
                "products": [],
                "orders": [],
                "user_info": {},
                "count": 0,
                "search_type": "general",
                "operation_type": "general",
                "llm_response": "",
                "formatted_response": {}
            }
            
            # Chạy workflow
            result = self.graph.invoke(initial_state)
            
            # Trả về formatted response từ state
            return result.get("formatted_response", {
                "products": [],
                "orders": [],
                "user_info": {},
                "count": 0,
                "llm_response": "Xin lỗi, tôi không hiểu câu hỏi của bạn.",
                "search_type": "general",
                "operation_type": "general"
            })
            
        except Exception as e:
            logger.error(f"Lỗi chat: {e}")
            return {
                "products": [],
                "orders": [],
                "user_info": {},
                "count": 0,
                "llm_response": f"❌ Có lỗi xảy ra: {str(e)}",
                "search_type": "error",
                "operation_type": "error"
            }

# ============ INSTANCE CREATOR ============

# Test function
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    agent = SimplifiedOrderAgent()
    
    # Test chat
    print("🤖 Simplified Order Agent sẵn sàng!")
    print("📝 Thử: 'tìm sản phẩm tên iphone' hoặc 'lấy thông tin user 1'")
    
    while True:
        user_input = input("\n👤 Bạn: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            break
        
        response = agent.chat(user_input)
        print(f"🤖 Bot Response:")
        print(f"   📝 Text: {response.get('llm_response', 'No response')}")
        print(f"   📊 Type: {response.get('operation_type', 'unknown')}")
        print(f"   🔢 Count: {response.get('count', 0)}")
        if response.get('products'):
            print(f"   📦 Products: {len(response['products'])} items")
        if response.get('orders'):
            print(f"   🛍️ Orders: {len(response['orders'])} items")
        if response.get('user_info'):
            print(f"   👤 User Info: Available") 