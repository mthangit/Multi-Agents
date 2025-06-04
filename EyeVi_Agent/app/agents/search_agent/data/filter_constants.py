"""
Hằng số lọc sản phẩm cho Search Agent.
Tự động tạo từ file filter_base.md
"""

AVAILABLE_COLORS = [
    "Đen", "Gold", "Unknown", "Bạc", "Xám", "Havana", "Xanh dương", "Vàng hồng", 
    "Nâu", "Gunmetal", "Vàng", "Trắng", "Đen Mờ", "Trong suốt", "Đồi mồi", "Đỏ", 
    "Vàng gold", "Hồng", "Xám Trong Suốt", "Be", "Nâu Trong Suốt", "RUTHENIUM", 
    "Bạc & Đen", "Xám Mờ", "Xanh Olive", "Gun Metal", "Khói Trong Suốt", "Xám Đậm", 
    "Xanh lá", "Vàng Nhạt", "Xanh Trong Suốt", "Vàng Hồng Viền Nhựa Xám Trong Suốt", 
    "Rose Golden", "Navy", "Dark havana", "Tím", "Đỏ rượu", "Vàng & Đen", 
    "Vàng Hồng Viền Nhựa Trong Suốt", "Xanh Lá Đậm", "Xanh Dương Mờ", "Ivory", "Nude", 
    "Đen & Trắng", "Xám Khói", "Vàng nhạt", "Vàng gold & Đen", 
    "Vàng Hồng Viền Nhựa Nâu Trong Suốt", "Xám Bạch Kim", "Xanh Mint", "Cam", "Đen & Bạc", 
    "Hồng Trong Suốt", "Gun Metal & Đen", "Đồng", "Xanh Rêu Mờ", "Trà Đen Trong Suốt", 
    "Đen/Bạc", "Đỏ Tía", "Đen & Xám", "Vàng Viền Nhựa Nâu Trong Suốt", "Vàng Viền Đen", 
    "Xanh Dương Nhạt", "Bạc & Havana", "Xanh Navy Trong Suốt", "Đồi mồi & Vàng gold", 
    "Vàng Satin", "Trà", "Xanh Ngọc Lam", "Satin Chrome", "Trắng trong", "Đen/Ruthenium",
    "Xanh Olive Trong Suốt", "Xanh Rêu", "Xám phối", "Bạc & Vàng gold", 
    "Rose Gold & Transparent Grey", "Rose Golden & Transparent Greyish Tawny", 
    "Đen/Vàng", "Gunmetal Mờ", "Bạc Viền Nhựa Đen", "Nâu Nhạt Trong Suốt", "Đồi Mồi", 
    "Vàng Hồng Viền Nhựa Nâu Vàng Trong Suốt", "Vàng Viền Nhựa Đen", 
    "Bạc Viền Nhựa Xanh Olive Trong Suốt", "Bạc Viền Đen", "Bạc Xanh", "Vàng & Havana", 
    "Đen/Đỏ", "Đen & Xanh lá", "Đen & Gun Metal", "Vàng ghồng", "Nylon", "Đem", "Latte", 
    "Hồng & Xanh", "Cam và Xanh", "Trắng ngà", "Xanh Tiffany", "Vàng Hồng", "Xanh đen", 
    "Đen & Cam", "Đen & Vàng", "Đen & Gun Metalfilter_material", "Xám Nhạt", "Đen Nhám", 
    "Vàng Nhạt Mờ", "Shiny Havana", "Đỏ Bordeaux Mờ", "Caramel Trong Suốt", "Cream", "Nâu đậm", 
    "Latte Trong Suốt", "Trà Đen", "Leo Brown On Black", "Hồng & Bạc", "Đồng - Bronze", 
    "Xám & Đỏ", "Cam Hồng Trong Suốt", "Vàng Nhạt/Đỏ Bordeaux", "Bạc & Xanh lá", 
    "Vàng Hồng & Nâu Trong Suốt", "Vàng Hồng & Nâu", "Light Ruthenium", 
    "Havana Black Transparent", "Beige", "Gold & Đen", "Vàng gold & Đồi mồi", "Hồng Opal", 
    "Xanh olive", "Ô liu", "Gunmetal Viền Đen Mờ", "Bạc Viền Nhựa Trong Suốt", 
    "Vàng Hồng Viền Nhựa Đen", "Bạc Viền Nhựa Xanh Lá Trong Suốt", "Satin Jade", 
    "Satin Light Berry", "Ngọc Lục Bảo", "Đen & Vàng gold", "Vàng Viền Nhựa Xám Trong Suốt", 
    "Vàng Hồng Viền Nhựa Nâu Xám Gradient", "Brushed burberry gold", "Vàng hồng & Đen", 
    "Đen & Nâu", "Vintage Check", "Bordeaux", "Opal Crystal", "Ren Đen", 
    "Bạc Viền Nhựa Xám Trong Suốt", "Havana/Vàng", "Đen/Trắng", "Be Trong Suốt", "Xám Opal"
]

AVAILABLE_BRANDS = [
    "BOLON", "MOLSION", "RAYBAN", "ANCCI", "AMO", "PUMA", "GUCCI", "BURBERRY", "TOMMY HILFIGER",
    "PRADA", "FLYER", "VERSACE", "SWAROVSKI", "ARMANI EXCHANGE", "MONTBLANC", "ZIOZIA", "OAKLEY",
    "EMPORIO ARMANI", "DOLCE & GABBANA", "REVLON", "TIFFANY & CO.", "YVES SAINT LAURENT", "FOSSIL",
    "VALENTINO RUDY", "HANGTEN", "CARTIER", "BOTTEGA VENETA", "TOMMY JEANS", "GUY LAROCHE", 
    "COACH", "BALENCIAGA", "VOGUE", "REEBOK", "GIORGIO FERRI", "ALAIN DELON", "BVLGARI", "NIKON",
    "MICHAEL KORS", "VUILLET VEGA"
]

AVAILABLE_FRAME_SHAPES = [
    "Vuông", "Chữ nhật", "Mắt mèo", "Phi công", "Tròn", "Unknown", 
    "Đa giác", "Phi hình học", "Oval", "Pillow", "Bướm", "Phantos", 
    "Panthos", "Mask", "Thể thao", "Browline", "Cat-eye", "Wayfarer", 
    "Round", "Oversized", " Vuông", "Wayfare"
]

AVAILABLE_FRAME_MATERIALS = [
    "Kim loại", "Acetate", "Nhựa", "Unknown", "Titanium", "TR90", "Tổng hợp", 
    "Nhựa Injection", " Recycled Acetate", "Thép không gỉ", "B-Titanium", 
    "Nhựa Injected", "TR/Titanium", "Alloy", "Nylon", "Recycled Acetate", "TR", 
    "Nhựa tổng hợp", "Injected", "Nhựa TR90", "O_Matter", "TR/Alloy", "Injection", 
    "Nhựa TR", "O Matter™", "Nhựa Durabio", "Nhựa Propionate", "Kim loại & Injected", 
    "Nhựa Peek", "Kim loại & Nhựa", "Vàng", "C_5", "Polycacbonat", "Propionate", 
    "Polycarbonat", "Đen & Gun Metalfilter_material", "Kim Loại Mạ Vàng"
]

AVAILABLE_GENDERS = [
    "Unisex", "Man", "Woman"
]

AVAILABLE_CATEGORIES = [
    "Kính Mát", "Gọng kính"
]

# Ánh xạ màu tiếng Việt sang tiếng Anh cho tìm kiếm song ngữ
COLOR_MAPPING = {
    "đen": "black", "xanh dương": "blue", "xám": "gray", "bạc": "silver",
    "đỏ": "red", "nâu": "brown", "trắng": "white", "vàng hồng": "rose gold",
    "trong suốt": "transparent", "xanh lá": "green", "hồng": "pink",
    "tím": "purple", "cam": "orange", "vàng": "yellow", "xanh navy": "navy blue",
    "đồi mồi": "tortoise", "vàng gold": "gold"
}


# Hằng số cho shape
AVAILABLE_FRAME_SHAPES = [
    "Vuông", "Tròn", "Oval", "Chữ nhật", "Cat Eye", "Phi công", "Tròn cỡ lớn", 
    "Bán khung", "Không gọng", "Hình thang", "Browline", "Clubmaster"
]

# Hằng số cho kích thước mặt
AVAILABLE_FACE_SIZES = ["Mặt nhỏ", "Mặt trung bình", "Mặt to"]

# Các thuộc tính có thể lọc trực tiếp trong Qdrant
QDRANT_FILTERABLE_FIELDS = ["color", "brand", "category", "gender", "frameMaterial"]

def get_filter_options():
    """
    Tạo tùy chọn lọc cho giao diện người dùng.
    
    Returns:
        dict: Dictionary chứa các tùy chọn lọc sẵn sàng cho UI
    """
    return {
        "colors": sorted([{"value": color, "label": color} for color in AVAILABLE_COLORS], key=lambda x: x["label"]),
        "brands": sorted([{"value": brand, "label": brand} for brand in AVAILABLE_BRANDS], key=lambda x: x["label"]),
        "frame_shapes": sorted([{"value": shape, "label": shape} for shape in AVAILABLE_FRAME_SHAPES], key=lambda x: x["label"]),
        "genders": [{"value": gender, "label": gender} for gender in AVAILABLE_GENDERS],
        "categories": [{"value": cat, "label": cat} for cat in AVAILABLE_CATEGORIES],
        "frame_materials": sorted([{"value": material, "label": material} for material in AVAILABLE_FRAME_MATERIALS], key=lambda x: x["label"]),
        "face_sizes": [{"value": size, "label": size} for size in AVAILABLE_FACE_SIZES]
    }

def get_normalized_value(field_name, value):
    """
    Chuẩn hóa giá trị đầu vào cho các trường lọc.
    
    Args:
        field_name: Tên trường cần chuẩn hóa giá trị
        value: Giá trị cần chuẩn hóa
    
    Returns:
        Giá trị đã chuẩn hóa
    """
    if not value:
        return None
        
    value_lower = str(value).lower()
    
    if field_name == "color":
        for color in AVAILABLE_COLORS:
            if color.lower() == value_lower:
                return color
        # Không tìm thấy màu khớp chính xác, thử tìm màu chứa chuỗi con
        for color in AVAILABLE_COLORS:
            if value_lower in color.lower():
                return color
    
    elif field_name == "brand":
        for brand in AVAILABLE_BRANDS:
            if brand.lower() == value_lower:
                return brand
        # Không tìm thấy thương hiệu khớp chính xác, thử tìm thương hiệu chứa chuỗi con
        for brand in AVAILABLE_BRANDS:
            if value_lower in brand.lower():
                return brand
    
    elif field_name == "frame_shape":
        for shape in AVAILABLE_FRAME_SHAPES:
            if shape.lower() == value_lower:
                return shape
        # Kiểm tra các từ đồng nghĩa
        shape_synonyms = {
            "square": "Vuông",
            "round": "Tròn",
            "rectangle": "Chữ nhật",
            "aviator": "Phi công",
            "cat eye": "Cat Eye",
            "mắt mèo": "Cat Eye",
            "không viền": "Không gọng"
        }
        if value_lower in shape_synonyms:
            return shape_synonyms[value_lower]
    
    elif field_name == "gender":
        gender_mapping = {
            "nam": "Man",
            "men": "Man", 
            "male": "Man",
            "nữ": "Woman", 
            "women": "Woman",
            "female": "Woman",
            "unisex": "Unisex"
        }
        if value_lower in gender_mapping:
            return gender_mapping[value_lower]
    
    elif field_name == "category":
        for category in AVAILABLE_CATEGORIES:
            if category.lower() == value_lower:
                return category
        # Kiểm tra từ đồng nghĩa
        category_synonyms = {
            "kính râm": "Kính Mát",
            "sunglasses": "Kính Mát",
            "gọng": "Gọng kính",
            "eyeglasses": "Gọng kính",
            "mắt kính": "Gọng kính"
        }
        if value_lower in category_synonyms:
            return category_synonyms[value_lower]
            
    # Trả về giá trị gốc nếu không tìm thấy giá trị chuẩn hóa
    return value 