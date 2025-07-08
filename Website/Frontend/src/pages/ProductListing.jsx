import { BiFilter } from "react-icons/bi";
import loadingGif from "../assets/loading.gif";
import scroll from "../assets/ico-direct.png";
import bannerImg1 from "../assets/2.jpg";
import bannerImg2 from "../assets/3.jpg";
import bannerImg3 from "../assets/4.jpg";
import handleRightImg from "../assets/ico-handleRight.png";
import handleLeftImg from "../assets/ico-handleLeft.png";

import { Filters, SingleProduct, SortBy, Pagination } from "../components";

import { useProductsContext } from "../contexts";
import { useEffect, useState } from "react";
import { useFilter } from "../hooks/filtersHook";
import { useLocation } from "react-router";
import { getProductsPaginatedService } from "../api/apiServices";

const ProductListing = () => {
  const bannerImages = [bannerImg1, bannerImg2, bannerImg3];
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const handleLeft = () => {
    setCurrentImageIndex(
      (prevIndex) => (prevIndex - 1 + bannerImages.length) % bannerImages.length
    );
  };

  const handleRight = () => {
    setCurrentImageIndex((prevIndex) => (prevIndex + 1) % bannerImages.length);
  };

  const location = useLocation();
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [showScrollArrow, setShowScrollArrow] = useState(false);

  // States cho phân trang
  const [paginatedProducts, setPaginatedProducts] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("");

  const productsPerPage = 16; // Hiển thị 16 sản phẩm mỗi trang (4x4 grid)

  // Load sản phẩm với phân trang
  const loadProducts = async (page = 1, search = "", category = "", brand = "") => {
    try {
      setLoading(true);
      const response = await getProductsPaginatedService(page, productsPerPage, search, category, brand);
      
      if (response.status === 200) {
        const products = response.data.products || [];
        setPaginatedProducts(products);
        setPagination(response.data.pagination);
        
        // Lưu thêm products từ trang này vào localStorage
        if (products.length > 0) {
          try {
            const existingProducts = JSON.parse(localStorage.getItem('allProducts') || '[]');
            
            // Merge products mới với products đã có, tránh duplicate
            const mergedProducts = [...existingProducts];
            products.forEach(newProduct => {
              const exists = existingProducts.some(existing => 
                existing.id === newProduct.id || existing._id === newProduct._id
              );
              if (!exists) {
                mergedProducts.push(newProduct);
              }
            });
            
            localStorage.setItem('allProducts', JSON.stringify(mergedProducts));
            console.log("✅ Đã cập nhật localStorage với", products.length, "sản phẩm mới. Tổng:", mergedProducts.length);
          } catch (error) {
            console.error("Lỗi khi cập nhật localStorage:", error);
          }
        }
      }
    } catch (error) {
      console.error("Lỗi khi load sản phẩm:", error);
      setPaginatedProducts([]);
      setPagination(null);
    } finally {
      setLoading(false);
    }
  };

  // Load sản phẩm lần đầu
  useEffect(() => {
    loadProducts(currentPage, searchTerm, selectedCategory, selectedBrand);
  }, [currentPage, searchTerm, selectedCategory, selectedBrand]);

  // Xử lý thay đổi trang
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    // Scroll lên đầu trang khi chuyển trang
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  useEffect(() => {
    const intervalTimer = setInterval(() => {
      setCurrentImageIndex(
        (prevIndex) => (prevIndex + 1) % bannerImages.length
      );
    }, 4000);

    return () => clearInterval(intervalTimer);
  }, []);

  useEffect(() => {
    if (location?.state?.from === "category") {
      setIsFilterOpen(true);
    }
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };
  
  useEffect(() => {
    const toggleShowArrow = () => {
      if (window.scrollY > 300) {
        setShowScrollArrow(true);
      } else {
        setShowScrollArrow(false);
      }
    };
    window.addEventListener("scroll", toggleShowArrow);

    return () => {
      window.removeEventListener("scroll", toggleShowArrow);
    };
  }, []);

  return (
    <>
      {loading ? (
        <div className="h-[70vh] w-full flex items-center justify-center overflow-hidden ">
          <span>
            <img width={250} src={loadingGif} alt="loading..." />
          </span>
        </div>
      ) : (
        <div>
          <header className="mb-3 relative flex">
            <img
              src={bannerImages[currentImageIndex]}
              alt="bannerImg"
              className="rounded-md w-full min-h-[10rem] object-cover"
            />
            <button
              onClick={handleLeft}
              className="w-7 h-7 m-2 absolute left-0 top-1/2 -translate-y-1/2"
            >
              <img src={handleLeftImg} alt="" />
            </button>
            <button
              onClick={handleRight}
              className="w-7 h-7 m-2 absolute right-0 top-0 top-1/2 -translate-y-1/2"
            >
              <img src={handleRightImg} alt="" />
            </button>
          </header>

          <section className="py-3 flex flex-col md:flex-row gap-2 justify-between">
            <h1 className="text-2xl font-bold">
              Kính
              {pagination && (
                <span className="text-lg text-gray-600 ml-2">
                  ({pagination.total_items} sản phẩm)
                </span>
              )}
            </h1>
            <div className="flex items-center gap-2">
              <Filters
                isFilterOpen={isFilterOpen}
                setIsFilterOpen={setIsFilterOpen}
              />
              <SortBy />
              <button
                className={`flex py-1 px-2 rounded-md shadow-md items-center  gap-1 hover:bg-[--primary-text-color] hover:text-white hover:shadow-lg ${
                  isFilterOpen ? "bg-[--primary-text-color] text-white" : ""
                }`}
                onClick={() => setIsFilterOpen(!isFilterOpen)}
              >
                <BiFilter className="text-lg" />
                <span className="text-sm">Bộ lọc</span>
              </button>
            </div>
          </section>

          {paginatedProducts.length > 0 ? (
            <>
              <main className="relative grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
                {paginatedProducts.map((glass) => (
                  <SingleProduct key={glass._id || glass.id} product={glass} />
                ))}
              </main>
              
              {/* Component phân trang */}
              {pagination && (
                <Pagination
                  currentPage={pagination.current_page}
                  totalPages={pagination.total_pages}
                  onPageChange={handlePageChange}
                  hasNext={pagination.has_next}
                  hasPrev={pagination.has_prev}
                />
              )}
            </>
          ) : (
            <p className="font-sans text-4xl  font-bold uppercase  tracking-wide text-gray-300 text-center w-full py-32">
              Không tìm thấy sản phẩm nào
            </p>
          )}

          <button
            className={`bg-white fixed flex bottom-20 right-0 p-2 rounded-full text-xl shadow-2xl transition-all delay-100 ease-in-out ${
              showScrollArrow ? "block" : "hidden"
            }`}
            style={{ transform: "rotate(90deg)" }}
            onClick={scrollToTop}
          >
            <img
              src={scroll}
              alt=""
              className="w-5 h-5"
              style={{ transform: "rotate(180deg)" }}
            />{" "}
            Về đầu trang
          </button>
        </div>
      )}
    </>
  );
};

export default ProductListing;
