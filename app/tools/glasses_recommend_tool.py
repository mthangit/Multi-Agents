from typing import Dict, Any, List
from app.tools.base_tool import BaseTool
from app.models.clip_model import CLIPModel

class GlassesRecommendTool(BaseTool):
    """Tool đề xuất kính mắt phù hợp"""
    
    def __init__(self):
        super().__init__(
            name="glasses_recommend",
            description="Đề xuất kính mắt phù hợp dựa trên khuôn mặt và sở thích"
        )
        self.clip_model = CLIPModel()
        
    async def execute(self, face_image: str = None, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Đề xuất kính mắt phù hợp"""
        try:
            recommendations = []
            
            # Nếu có ảnh khuôn mặt, phân tích để đề xuất
            if face_image:
                face_analysis = await self.clip_model.analyze_face(face_image)
                
                # Dựa vào hình dạng khuôn mặt để đề xuất
                face_shape = face_analysis.get("shape", "")
                if face_shape == "oval":
                    recommendations.extend([
                        {"style": "aviator", "reason": "Phù hợp với khuôn mặt oval"},
                        {"style": "cat-eye", "reason": "Tạo điểm nhấn cho khuôn mặt oval"}
                    ])
                elif face_shape == "round":
                    recommendations.extend([
                        {"style": "rectangular", "reason": "Tạo sự cân đối cho khuôn mặt tròn"},
                        {"style": "square", "reason": "Tạo góc cạnh cho khuôn mặt tròn"}
                    ])
                    
            # Thêm đề xuất dựa trên sở thích
            if preferences:
                if preferences.get("style") == "casual":
                    recommendations.append({
                        "style": "round",
                        "reason": "Phù hợp với phong cách casual"
                    })
                elif preferences.get("style") == "formal":
                    recommendations.append({
                        "style": "rectangular",
                        "reason": "Phù hợp với phong cách formal"
                    })
                    
            return {
                "success": True,
                "recommendations": recommendations,
                "total": len(recommendations)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 