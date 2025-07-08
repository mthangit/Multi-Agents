import Mockman from "mockman-js";

import { 
  Login, 
  ProductDetails, 
  ProductListing, 
  Signup,
  Cart, 
  Wishlist, 
  Checkout, 
  Profile, 
  Orders 
} from "../pages";
import { PaymentResult } from "../components";

const authRoutes = [
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/signup",
    element: <Signup />,
  },
];

const contentRoutes = [
  {
    path: "/products",
    element: <ProductListing />,
  },
  {
    path: "/product/:productId",
    element: <ProductDetails />,
  },
  {
    path: "/mockman",
    element: <Mockman />,
  },
  // Các routes trước đây yêu cầu authentication, giờ public
  {
    path: "/cart",
    element: <Cart />,
  },
  {
    path: "/wishlist",
    element: <Wishlist />,
  },
  {
    path: "/checkout",
    element: <Checkout />,
  },
  {
    path: "/orders",
    element: <Orders />,
  },
  {
    path: "/profile",
    element: <Profile />,
  },
  {
    path: "/payment-result",
    element: <PaymentResult />,
  },
];

export { authRoutes, contentRoutes };
