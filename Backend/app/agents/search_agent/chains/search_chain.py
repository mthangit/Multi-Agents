from typing import Dict, List, Any, Optional
import json
import base64

from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
from langchain.schema.runnable import Runnable, RunnableConfig
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.callbacks.base import BaseCallbackHandler

from langgraph.graph import StateGraph, END

from ..prompts.search_prompts import (
    SEARCH_AGENT_PROMPT,
    get_search_prompt_with_analysis
)
from ..tools.search_tools import get_search_tools
from ..models.product import ImageAnalysisResult, SearchResults


class SearchChain:
    """Chain xử lý tìm kiếm sản phẩm kính mắt."""
    
    def __init__(self, api_key=None, streaming=True):
        """Khởi tạo SearchChain.
        
        Args:
            api_key: API key cho mô hình LLM
            streaming: Bật/tắt chế độ streaming
        """
        # Khởi tạo LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key,
            temperature=0.2,
            streaming=streaming
        )
        
        # Khởi tạo công cụ
        self.tools = get_search_tools()
        
        # Xây dựng graph trạng thái
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Xây dựng workflow cho việc tìm kiếm."""
        
        # Định nghĩa các node trong graph
        
        # 1. Node phân tích yêu cầu - xác định cần tìm kiếm gì
        def analyze_request(state: Dict) -> Dict:
            """Phân tích yêu cầu và xác định loại tìm kiếm."""
            query = state.get("query", "")
            image_data = state.get("image_data")
            analysis_result = state.get("analysis_result")
            
            # Tạo prompt phù hợp
            if analysis_result:
                prompt = get_search_prompt_with_analysis(analysis_result)
            else:
                prompt = SEARCH_AGENT_PROMPT
            
            # Tạo agent executor
            prompt_template = ChatPromptTemplate.from_template(prompt)
            agent = create_tool_calling_agent(self.llm, self.tools, prompt_template)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors=True
            )
            
            # Chuẩn bị input
            agent_inputs = {
                "query": query,
                "image_data": image_data,
                "analysis_result": analysis_result
            }
            
            # Lưu callback handler (nếu có)
            callbacks = state.get("callbacks", [])
            
            # Thực thi agent
            result = agent_executor.invoke(
                agent_inputs, 
                config={"callbacks": callbacks}
            )
            
            # Cập nhật state
            state["agent_result"] = result
            state["search_results"] = self._extract_search_results(result)
            
            return state
        
        # 2. Node định dạng kết quả
        def format_results(state: Dict) -> Dict:
            """Định dạng kết quả cuối cùng."""
            search_results = state.get("search_results", {})
            analysis_result = state.get("analysis_result")
            
            # Tạo phản hồi cuối cùng
            final_response = {
                "results": search_results,
                "analysis": analysis_result
            }
            
            # Thêm thông tin output từ agent nếu không có kết quả tìm kiếm
            if not search_results.get("products"):
                if state.get("agent_result", {}).get("output"):
                    final_response["message"] = state["agent_result"]["output"]
            
            state["final_response"] = final_response
            return state
        
        # Tạo workflow
        workflow = StateGraph(state_type=Dict)
        
        # Thêm các node
        workflow.add_node("analyze_request", analyze_request)
        workflow.add_node("format_results", format_results)
        
        # Thêm các cạnh
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "format_results")
        workflow.add_edge("format_results", END)
        
        return workflow.compile()
    
    def _extract_search_results(self, agent_result: Dict) -> Dict:
        """Trích xuất và chuẩn hóa kết quả tìm kiếm từ kết quả của agent."""
        # Mặc định là kết quả trống
        default_result = {
            "products": [],
            "count": 0,
            "summary": "Không tìm thấy sản phẩm phù hợp."
        }
        
        # Trích xuất từ các bước trung gian
        if "intermediate_steps" in agent_result:
            steps = agent_result["intermediate_steps"]
            for step in steps:
                # Chỉ xét các bước có output là dict (kết quả tìm kiếm)
                if len(step) > 1 and isinstance(step[1], dict):
                    result = step[1]
                    # Kiểm tra nếu có trường products (kết quả tìm kiếm)
                    if "products" in result:
                        return result
                    # Hoặc kiểm tra trường summary
                    elif "summary" in result:
                        return result
        
        # Nếu không tìm thấy kết quả trong các bước trung gian, thử từ output
        output = agent_result.get("output", "")
        
        # Tìm kiếm chuỗi JSON trong output
        try:
            # Tìm kiếm từ đầu và cuối của JSON
            json_start = output.find("{")
            json_end = output.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                result = json.loads(json_str)
                
                # Kiểm tra nếu có trường products
                if "products" in result:
                    return result
        except:
            pass
        
        return default_result
    
    async def arun(
        self, 
        query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[Dict] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> Dict:
        """Chạy workflow tìm kiếm (bất đồng bộ).
        
        Args:
            query: Câu truy vấn tìm kiếm
            image_data: Dữ liệu hình ảnh
            analysis_result: Kết quả phân tích khuôn mặt
            callbacks: Các callback handler (cho streaming)
            
        Returns:
            Kết quả tìm kiếm
        """
        initial_state = {
            "query": query,
            "image_data": base64.b64encode(image_data).decode('utf-8') if image_data else None,
            "analysis_result": analysis_result,
            "callbacks": callbacks or []
        }
        
        result = await self.workflow.ainvoke(initial_state)
        return result.get("final_response", {})
    
    def run(
        self, 
        query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[Dict] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> Dict:
        """Chạy workflow tìm kiếm (đồng bộ).
        
        Args:
            query: Câu truy vấn tìm kiếm
            image_data: Dữ liệu hình ảnh
            analysis_result: Kết quả phân tích khuôn mặt
            callbacks: Các callback handler (cho streaming)
            
        Returns:
            Kết quả tìm kiếm
        """
        initial_state = {
            "query": query,
            "image_data": base64.b64encode(image_data).decode('utf-8') if image_data else None,
            "analysis_result": analysis_result,
            "callbacks": callbacks or []
        }
        
        result = self.workflow.invoke(initial_state)
        return result.get("final_response", {}) 