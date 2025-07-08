import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { HiOutlineShoppingBag } from "react-icons/hi";
import { BsBookmarkHeart, BsFillBookmarkHeartFill } from "react-icons/bs";

import {
  useAuthContext,
  useCartContext,
  useProductsContext,
  useWishlistContext,
} from "../contexts";
import { getProductByIdService, getWebProductDetailsService } from "../api/apiServices";
import { StarRating, Similar } from "../components";
import { notify } from "../utils/utils";

{
  /* product rating start */
}
// import { RatingList } from "../components/rating/RatingList";

const ProductDetails = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { productId } = useParams();
  const { token } = useAuthContext();
  const { getProductById, allProducts } = useProductsContext();
  
  // Parse productId thành number nếu cần
  const parsedProductId = isNaN(productId) ? productId : parseInt(productId);
  const { addProductToCart, disableCart } = useCartContext();
  const { addProductToWishlist, deleteProductFromWishlist, disableWish } =
    useWishlistContext();
  const [loading, setLoading] = useState(false);
  const [productDetails, setProductDetails] = useState(null);
  const [error, setError] = useState(null);
  
  // Fallback sản phẩm từ context (nếu có)
  const localProduct = getProductById(parsedProductId);

  useEffect(() => {
    const fetchProductDetails = async () => {
      console.log("🚀 ProductDetails mounted với productId:", productId);
      console.log("🔍 LocalProduct từ context:", localProduct);
      
      setLoading(true);
      setError(null);
      
      try {
        // Thử lấy từ API backend chính trước
        console.log("🔍 Đang lấy chi tiết sản phẩm từ API backend...");
        const response = await getWebProductDetailsService(productId);
        
        if (response.status === 200 && response.data) {
          setProductDetails(response.data);
          console.log("✅ Đã lấy chi tiết sản phẩm từ backend API:", response.data);
        } else {
          throw new Error("Không có dữ liệu sản phẩm");
        }
      } catch (apiError) {
        console.warn("⚠️ Lỗi API backend, fallback to local:", apiError.message);
        
        // Nếu có local product, sử dụng nó
        if (localProduct) {
          setProductDetails(localProduct);
          console.log("✅ Sử dụng sản phẩm từ local context");
        } else {
          // Không có local product, báo lỗi
          setError("Không tìm thấy sản phẩm");
          console.error("❌ Không tìm thấy sản phẩm nào");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProductDetails();
  }, [productId, localProduct]);

  // Sử dụng productDetails từ API hoặc fallback local product
  const product = productDetails;

  // Sử dụng image_url nếu có, fallback sang image
  const productImage = product?.image_url || product?.images?.[0] || product?.image;

  // Loading state
  if (loading) {
    return (
      <div className="min-h-[60vh] flex justify-center items-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải chi tiết sản phẩm...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !product) {
    return (
      <div className="min-h-[60vh] flex justify-center items-center">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Không tìm thấy sản phẩm</h2>
          <p className="text-gray-600 mb-4">{error || "Sản phẩm bạn tìm không tồn tại hoặc đã bị xóa"}</p>
          <button
            onClick={() => navigate("/")}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Về trang chủ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="md:min-h-[60vh] flex justify-center items-center pt-5 sm:pt-3 pb-2 relative">
        <main className="grid grid-rows-1 sm:grid-cols-2 gap-2 sm:gap-10 ">
          <section className="relative p-7 bg-white  flex items-center justify-center rounded-lg">
            <img
              src={productImage}
              alt={product?.name || "Product"}
              className="w-full object-contain max-w-xs"
            />
          </section>

          <section className="p-7 px-10 rounded-md shadow-sm bg-white/[0.6] flex flex-col gap-3 sm:gap-5 ">
            <div className="flex flex-col gap-2">
              <h1 className=" text-2xl sm:text-4xl font-bold">
                {product?.name}
              </h1>
              <p className=" text-gray-600 text-sm sm:text-base">
                {product?.description}
              </p>
              <div className="flex items-center gap-1">
                <StarRating />

                <span className="text-xs text-gray-400">
                  ({product?.rating}) Rating
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-2  ">
              <h2 className="  text-lg font-semibold">Thông tin sản phẩm</h2>
              <ul className="flex gap-5">
                <div>
                  <li>
                    <span className="text-gray-500 text-sm">Thương hiệu: </span>
                    {product?.brand}
                  </li>
                  <li>
                    <span className="text-gray-500 text-sm">Thể loại: </span>
                    {product?.category}
                  </li>
                </div>
                <div>
                  <li>
                    <span className="text-gray-500 text-sm">Giới tính: </span>
                    {product?.gender}
                  </li>
                  <li>
                    <span className="text-gray-500 text-sm">Trọng lượng: </span>
                    {product?.weight}
                  </li>
                </div>
              </ul>
            </div>

            <div className="flex gap-2 items-center pb-10 sm:pb-0">
              Price:
              {/* <span className="ms-1 text-xl sm:text-2xl text-red-800">
                {product?.newPrice}VNĐ
              </span> */}
              <span className="text-red-800 ms-1 text-xl sm:text-2xl ">
                {" "}
                {new Intl.NumberFormat("vi-VN", {
                  style: "currency",
                  currency: "VND",
                }).format(product?.newPrice)}
              </span>
              {/* <span className="text-sm text-gray-600 line-through">
                {product?.price}VNĐ
              </span> */}
              <span className="text-gray-600 line-through text-sm">
                {" "}
                {product?.price && new Intl.NumberFormat("vi-VN", {
                  style: "currency",
                  currency: "VND",
                }).format(product.price)}
              </span>
            </div>

            <div className={`w-full   flex gap-4 items-center   flex-wrap  `}>
              <button
                className="btn-rounded-secondary flex items-center gap-2 text-sm disabled:cursor-not-allowed"
                disabled={disableCart}
                onClick={() => {
                  if (!token) {
                    navigate("/login", { state: { from: location.pathname } });
                    notify("warn", "Đăng nhập để tiếp tục");
                  } else {
                    if (!product?.inCart) {
                      addProductToCart(product);
                    } else {
                      navigate("/cart");
                    }
                  }
                }}
              >
                <HiOutlineShoppingBag />{" "}
                {product?.inCart ? "Đến giỏ hàng" : "Thêm vào giỏ hàng"}
              </button>

              <button
                className="btn-rounded-primary rounded-full flex items-center gap-2 text-sm disabled:cursor-not-allowed"
                disabled={disableWish}
                onClick={() => {
                  if (!token) {
                    navigate("/login", { state: { from: location.pathname } });
                    notify("warn", "Đăng nhập để tiếp tục");
                  } else {
                    if (product?.inWish) {
                      deleteProductFromWishlist(product.id);
                    } else {
                      addProductToWishlist(product);
                    }
                  }
                }}
              >
                {product?.inWish ? (
                  <>
                    <BsFillBookmarkHeartFill />
                    <span>Xóa khỏi Yêu thích</span>
                  </>
                ) : (
                  <>
                    {" "}
                    <BsBookmarkHeart /> <span>Yêu thích</span>
                  </>
                )}{" "}
              </button>
            </div>
          </section>
        </main>
      </div>
      {/* product rating start */}
      {/* <div>
        <RatingList currentProductId={productId}></RatingList>
        </div> */}
      {/* product rating end */}

      {/* <section>
        <Similar />
        </section> */}

      <section className="w-full">
        <hr className="w-full" />
        <br />
        <h1 className=" text-2xl sm:text-4xl font-bold">Đánh giá sản phẩm</h1>

        <div className="flex p-6 rounded-md shadow-sm bg-white">
          <div>
            <b className="ms-1 text-xl sm:text-2xl text-blue-800">
              {product?.rating}
            </b>{" "}
            out of 5
            <div className="flex items-center gap-1">
              <StarRating />
            </div>
          </div>
          {/* </div>
          <div data-toggle="buttons">
             <label className="btn-third text-lg text-center bg-white">
              <input type="radio" name="rate" id="all"/>ALL
             </label> */}
          <button className="btn-third text-lg text-center bg-white rounded-md ml-2 px-2">
            All
          </button>
          <button className="btn-third text-lg text-center bg-white rounded-md ml-2 px-2">
            5 Stars
          </button>
          <button className="btn-third text-lg text-center bg-white rounded-md ml-2 px-2">
            4 Stars
          </button>
          <button className="btn-third text-lg text-center bg-white rounded-md ml-2 px-2">
            3 Stars
          </button>
          <button className="btn-third text-lg text-center bg-white rounded-md ml-2 px-2">
            2 Stars
          </button>
          <button className="btn-third text-lg text-center bg-white rounded-md ml-2 px-2">
            1 Star
          </button>
        </div>
        {/*  */}
        <div className="p-4 rounded-md shadow-sm bg-white mt-2">
          <b>user.username</b>
          <div className="flex items-center gap-1">
            <StarRating />
          </div>
          <div>
            Kính đẹp lắm nha, anh chị em nên mua á, tui rất thích vì người yêu
            tui khen tui slay.
          </div>
        </div>
        <div className="p-4 rounded-md shadow-sm bg-white  mt-2">
          <b>user.username</b>
          <div className="flex items-center gap-1">
            <StarRating />
          </div>
          <div>Mê luôn ý, tuyệt vời.</div>
        </div>
      </section>

      <br />
      <div className="w-full flex justify-center overflow-hidden ">
        <>
          <Similar currentProductCategory={product?.category} />
        </>
      </div>
    </div>
  );
};

export default ProductDetails;
