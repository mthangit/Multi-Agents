import Invoice from "../pages/admin/invoice/Invoice";
import Customer from "../pages/admin/customer/Customer";
import Dashboard from "../pages/admin/dashboard/Dashboard";
import Product from "../pages/admin/product/Product";

// Không còn private routes nào - tất cả đã chuyển sang public
const privateRoutes = [];

// Chỉ giữ lại admin routes (có thể tùy chọn bỏ authentication sau)
const adminRoutes = [
  {
    path: "/admininvoice",
    element: <Invoice />,
  },
  {
    path: "/admincustomer",
    element: <Customer />,
  },
  {
    path: "/adminproduct/*",
    element: <Product />,
  },
  {
    path: "/admindashboard",
    element: <Dashboard />,
  },
];

export { privateRoutes, adminRoutes };
