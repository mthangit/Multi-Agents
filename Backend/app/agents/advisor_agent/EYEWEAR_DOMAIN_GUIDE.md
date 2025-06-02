# 👓 Hướng dẫn Tối ưu cho Domain Tư vấn Mắt Kính

## 🎯 **Domain-Specific Optimization cho Mắt Kính**

### **Đặc điểm Domain:**
- **Technical + Consumer**: Vừa có thuật ngữ y tế, vừa có thông tin sản phẩm
- **Multilingual**: Tiếng Việt + thuật ngữ quốc tế (myopia, astigmatism...)
- **Product Recommendations**: Cần precision cho tư vấn sản phẩm
- **Medical Advisory**: Cần disclaimer và thông tin chính xác
- **Style Consultation**: Thông tin về thời trang, phong cách

## 🧮 **Embedding Strategy cho Eyewear Domain**

### **Model được chọn:**
```python
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"  # 768d
```

**Lý do chọn e5-base:**
✅ **Excellent cho technical terms**: Hiểu được "myopia", "astigmatism", "progressive lens"  
✅ **Strong Vietnamese support**: Tốt cho "cận thị", "loạn thị", "tròng kính đa tròng"  
✅ **Medical domain**: Tốt cho medical terminology  
✅ **Product descriptions**: Hiểu được mô tả sản phẩm chi tiết  

### **Chunking tối ưu:**

```python
CHUNK_SIZE = 700          # Nhỏ hơn cho product specificity
CHUNK_OVERLAP = 120       # Vừa phải cho technical content  
OVERLAP_METHOD = "sentence"  # Preserve technical definitions
```

**Lý do chunking nhỏ:**
- **Product catalogs**: Mỗi sản phẩm có thông tin riêng biệt
- **Technical specs**: Không nên trộn thông số kỹ thuật
- **Precision**: Tránh recommend nhầm sản phẩm

### **Retrieval settings:**

```python
TOP_K_DOCUMENTS = 8       # Tăng để có đa dạng sản phẩm
SIMILARITY_THRESHOLD = 0.68  # Cao hơn cho precision
```

## 📋 **Keywords và Terminology**

### **Các nhóm từ khóa domain:**

#### 1. **Vision Conditions** (Tình trạng mắt)
```python
"cận thị", "myopia", "viễn thị", "hyperopia", 
"loạn thị", "astigmatism", "lão thị", "presbyopia"
```

#### 2. **Lens Types** (Loại tròng kính)
```python
"đơn tròng", "single vision", "đa tròng", "progressive",
"bifocal", "blue light", "photochromic", "transition"
```

#### 3. **Frame Styles** (Kiểu gọng)
```python
"gọng tròn", "round", "gọng vuông", "square",
"aviator", "cat-eye", "rimless", "semi-rimless"
```

#### 4. **Materials** (Vật liệu)
```python
"titan", "titanium", "acetate", "TR90", 
"memory metal", "stainless steel", "coating"
```

## 🤖 **Enhanced RAG Agent Features**

### **1. Intent Detection**
Tự động phân loại câu hỏi:
- **Medical consultation**: "Tôi bị cận thị 3 độ..."
- **Product recommendation**: "Tôi muốn tìm kính chống ánh sáng xanh..."
- **Style consultation**: "Khuôn mặt tròn phù hợp gọng nào?"

### **2. Domain-Specific Prompts**
```python
# Medical consultation prompt
"Bạn là chuyên gia tư vấn mắt kính với kiến thức về:
- Các tật khúc xạ mắt
- Công nghệ tròng kính
- Không thay thế ý kiến bác sĩ..."

# Product recommendation prompt  
"Hãy so sánh ưu nhược điểm các sản phẩm
và đề xuất phù hợp với nhu cầu..."
```

### **3. Response Post-processing**
- **Medical disclaimer**: Tự động thêm cho câu hỏi y tế
- **CTA**: Gợi ý thử tại cửa hàng cho product questions
- **Structured response**: 5-step consultation format

## 📊 **Content Structure Recommendations**

### **Tài liệu nên có:**

#### 1. **Product Catalogs**
```
- Thông số kỹ thuật chi tiết
- Giá cả và phân khúc
- Ưu nhược điểm
- Use cases phù hợp
```

#### 2. **Technical Guides**
```
- Giải thích các tật khúc xạ
- Công nghệ lens (coating, material)
- Hướng dẫn đo mắt
- Cách chăm sóc kính
```

#### 3. **Style Guides**
```
- Phân tích khuôn mặt
- Xu hướng thời trang
- Color matching
- Lifestyle recommendations
```

#### 4. **FAQs**
```
- Câu hỏi thường gặp
- Troubleshooting
- Warranty & service
- Comparison guides
```

## ⚙️ **Setup Optimal cho Eyewear Domain**

### **Environment Variables:**
```bash
# Domain-specific settings
export COLLECTION_NAME="eyewear_advisor"
export EMBEDDING_MODEL="intfloat/multilingual-e5-base"
export CHUNK_SIZE="700"
export CHUNK_OVERLAP="120"
export OVERLAP_METHOD="sentence"

# Retrieval tuning
export TOP_K_DOCUMENTS="8"
export SIMILARITY_THRESHOLD="0.68"

# Response tuning
export GEMINI_TEMPERATURE="0.2"  # Cao hơn cho creativity
export ENABLE_PRODUCT_RECOMMENDATIONS="true"
export ENABLE_TECHNICAL_ADVICE="true"
```

### **Data Organization:**
```
data/
├── product_catalogs/
│   ├── frames/
│   │   ├── metal_frames.pdf
│   │   ├── plastic_frames.pdf
│   │   └── designer_frames.pdf
│   └── lenses/
│       ├── single_vision.pdf
│       ├── progressive.pdf
│       └── specialty_lenses.pdf
├── technical_guides/
│   ├── vision_conditions.pdf
│   ├── lens_technology.pdf
│   └── fitting_guide.pdf
├── style_guides/
│   ├── face_shape_analysis.pdf
│   ├── fashion_trends.pdf
│   └── color_guide.pdf
└── faqs/
    ├── common_questions.pdf
    └── troubleshooting.pdf
```

## 🎯 **Query Examples và Expected Behavior**

### **Medical Consultation:**
```
Q: "Tôi bị cận thị 3 độ, nên dùng loại tròng nào?"
Expected:
- Giải thích cận thị 3 độ
- Đề xuất tròng đơn hoặc aspheric
- Lưu ý về index và độ mỏng
- Medical disclaimer
```

### **Product Recommendation:**
```
Q: "Tôi cần kính chống ánh sáng xanh để làm việc máy tính"
Expected:
- So sánh các loại blue light filter
- Đề xuất sản phẩm cụ thể
- Thông tin giá cả
- Gợi ý thử tại cửa hàng
```

### **Style Consultation:**
```
Q: "Khuôn mặt vuông nên đeo gọng gì?"
Expected:
- Phân tích đặc điểm khuôn mặt vuông
- Đề xuất kiểu gọng phù hợp (oval, round)
- Gợi ý màu sắc
- Ví dụ sản phẩm cụ thể
```

## 📈 **Metrics để Theo dõi**

### **Retrieval Quality:**
```python
{
    "intent_detection_accuracy": 0.92,  # % phân loại đúng intent
    "product_precision": 0.87,          # % recommend đúng sản phẩm
    "technical_accuracy": 0.89,         # % thông tin kỹ thuật chính xác
    "response_completeness": 0.84       # % response đầy đủ thông tin
}
```

### **Domain-specific Metrics:**
- **Medical disclaimer coverage**: 100% cho medical questions
- **Product recommendation rate**: % queries được suggest sản phẩm
- **Style advice quality**: User feedback score
- **Technical term coverage**: % thuật ngữ được handle đúng

## 🚀 **Advanced Features**

### **1. Multi-stage Retrieval:**
```python
# Stage 1: Broad retrieval
retrieval_stage1 = search_products(query, top_k=15, threshold=0.6)

# Stage 2: Product filtering  
filtered_products = filter_by_specs(retrieval_stage1, user_requirements)

# Stage 3: Final ranking
final_recommendations = rank_by_suitability(filtered_products)
```

### **2. Contextual Product Matching:**
```python
# Thêm user context vào embedding
enhanced_query = f"""
User profile: {age}, {gender}, {lifestyle}
Vision condition: {prescription}
Budget range: {budget}
Style preference: {style}
Original query: {query}
"""
```

### **3. Seasonal/Trend Awareness:**
```python
# Adjust recommendations based on trends
if is_trending("blue_light_protection"):
    boost_blue_light_products(recommendations)
    
if season == "summer":
    boost_sunglasses(recommendations)
```

## 💡 **Best Practices**

### **Content Creation:**
1. **Structured data**: JSON metadata cho products
2. **Consistent terminology**: Dùng thuật ngữ chuẩn
3. **Multi-language**: Dual Vietnamese-English terms
4. **Regular updates**: Cập nhật xu hướng và sản phẩm mới

### **System Maintenance:**
1. **A/B test prompts**: Test different consultation styles
2. **Monitor intent accuracy**: Track classification performance  
3. **Update keywords**: Thêm terms mới theo trend
4. **User feedback loop**: Collect và improve từ feedback

---

## 🎯 **Quick Start cho Eyewear Domain:**

```bash
# 1. Setup environment
export EMBEDDING_MODEL="intfloat/multilingual-e5-base"
export COLLECTION_NAME="eyewear_advisor"
export CHUNK_SIZE="700" 
export TOP_K_DOCUMENTS="8"

# 2. Organize data theo structure trên
mkdir -p data/{product_catalogs,technical_guides,style_guides,faqs}

# 3. Ingest data
python ingest_data.py --clear

# 4. Test với câu hỏi domain-specific
python main.py demo
```

---

**🎯 Domain này tối ưu cho:**
- Tư vấn tật khúc xạ và giải pháp
- Đề xuất sản phẩm kính mắt
- Tư vấn phong cách và thời trang
- Hướng dẫn kỹ thuật và chăm sóc
- Customer support chuyên sâu 