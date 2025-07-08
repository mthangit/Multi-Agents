// Utility functions cho localStorage management

export const STORAGE_KEYS = {
  ALL_PRODUCTS: 'allProducts',
  USER_CART: 'userCart',
  USER_WISHLIST: 'userWishlist'
};

/**
 * Lưu products vào localStorage
 * @param {Array} products - Mảng sản phẩm cần lưu
 */
export const saveProductsToStorage = (products) => {
  try {
    localStorage.setItem(STORAGE_KEYS.ALL_PRODUCTS, JSON.stringify(products));
    console.log("✅ Đã lưu", products.length, "sản phẩm vào localStorage");
  } catch (error) {
    console.error("❌ Lỗi khi lưu vào localStorage:", error);
  }
};

/**
 * Lấy tất cả products từ localStorage
 * @returns {Array} Mảng sản phẩm hoặc mảng rỗng
 */
export const getProductsFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.ALL_PRODUCTS);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error("❌ Lỗi khi đọc từ localStorage:", error);
    return [];
  }
};

/**
 * Tìm product theo ID từ localStorage
 * @param {string|number} productId - ID sản phẩm cần tìm
 * @returns {Object|null} Sản phẩm tìm được hoặc null
 */
export const getProductByIdFromStorage = (productId) => {
  try {
    const products = getProductsFromStorage();
    const product = products.find((product) => 
      product.id === productId || 
      product._id === productId ||
      product.id === parseInt(productId) ||
      product._id === parseInt(productId)
    );
    
    if (product) {
      console.log("🔍 Tìm thấy sản phẩm từ localStorage:", product.name);
    }
    
    return product || null;
  } catch (error) {
    console.error("❌ Lỗi khi tìm sản phẩm trong localStorage:", error);
    return null;
  }
};

/**
 * Thêm products mới vào localStorage (merge với existing)
 * @param {Array} newProducts - Mảng sản phẩm mới cần thêm
 */
export const mergeProductsToStorage = (newProducts) => {
  try {
    const existingProducts = getProductsFromStorage();
    const mergedProducts = [...existingProducts];
    
    newProducts.forEach(newProduct => {
      const exists = existingProducts.some(existing => 
        existing.id === newProduct.id || 
        existing._id === newProduct._id ||
        existing.id === newProduct._id ||
        existing._id === newProduct.id
      );
      
      if (!exists) {
        mergedProducts.push(newProduct);
      }
    });
    
    saveProductsToStorage(mergedProducts);
    console.log("✅ Đã merge", newProducts.length, "sản phẩm mới. Tổng:", mergedProducts.length);
    
    return mergedProducts;
  } catch (error) {
    console.error("❌ Lỗi khi merge sản phẩm:", error);
    return getProductsFromStorage();
  }
};

/**
 * Xóa tất cả products khỏi localStorage
 */
export const clearProductsFromStorage = () => {
  try {
    localStorage.removeItem(STORAGE_KEYS.ALL_PRODUCTS);
    console.log("🗑️ Đã xóa tất cả sản phẩm khỏi localStorage");
  } catch (error) {
    console.error("❌ Lỗi khi xóa localStorage:", error);
  }
};

/**
 * Kiểm tra số lượng products trong localStorage
 * @returns {number} Số lượng sản phẩm
 */
export const getProductsCount = () => {
  try {
    const products = getProductsFromStorage();
    return products.length;
  } catch (error) {
    console.error("❌ Lỗi khi đếm sản phẩm:", error);
    return 0;
  }
}; 