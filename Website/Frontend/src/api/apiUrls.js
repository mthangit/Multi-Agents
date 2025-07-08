const baseUrl = "https://eyevi-backend.devsecopstech.click";

//auth url
export const SIGNUP_URL = `${baseUrl}/signup`;
export const LOGIN_URL = `${baseUrl}/login`;

//products url

export const PRODUCTS_URL = `${baseUrl}/all-products/paginated?page=5&limit=26`;
export const PRODUCTS_PAGINATED_URL = `${baseUrl}/all-products/paginated`;

//category url
export const CATEGORIES_URL = `${baseUrl}/categories`;

//cart url
export const CART_URL = `${baseUrl}/user/cart`;

//wishlist url
export const WISHLIST_URL = `${baseUrl}/user/wishlist`;

// checkout url
export const CHECKOUT_URL = `${baseUrl}/user/checkout`;

export const ALL_USER = `${baseUrl}/admin/getUser`;
export const ALL_INVOICE = `${baseUrl}/admin/getInvoices`;

// Orders URL - từ host agent (không cần xác thực)
const hostAgentUrl = "http://eyevi.devsecopstech.click:8000";
export const ORDERS_URL = `${baseUrl}/orders`;
export const USER_ORDERS_URL = `${baseUrl}/orders/user`;
export const ORDER_DETAILS_URL = `${baseUrl}/orders`;
