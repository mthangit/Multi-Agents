import React from "react";

const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange, 
  hasNext, 
  hasPrev,
  className = "" 
}) => {
  const handlePrevious = () => {
    if (hasPrev) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (hasNext) {
      onPageChange(currentPage + 1);
    }
  };

  const handlePageClick = (page) => {
    onPageChange(page);
  };

  // Tạo array các số trang để hiển thị
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        pages.push(1, 2, 3, 4, 5);
      } else if (currentPage >= totalPages - 2) {
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        for (let i = currentPage - 2; i <= currentPage + 2; i++) {
          pages.push(i);
        }
      }
    }
    
    return pages;
  };

  if (totalPages <= 1) return null;

  return (
    <div className={`flex justify-center items-center gap-2 mt-6 ${className}`}>
      {/* Nút Previous */}
      <button
        onClick={handlePrevious}
        disabled={!hasPrev}
        className={`px-4 py-2 rounded-md border transition-colors ${
          !hasPrev
            ? "bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200"
            : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400"
        }`}
      >
        Trang trước
      </button>

      {/* Số trang */}
      <div className="flex gap-1">
        {getPageNumbers().map((page) => (
          <button
            key={page}
            onClick={() => handlePageClick(page)}
            className={`w-10 h-10 rounded-md border transition-colors ${
              page === currentPage
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400"
            }`}
          >
            {page}
          </button>
        ))}
      </div>

      {/* Nút Next */}
      <button
        onClick={handleNext}
        disabled={!hasNext}
        className={`px-4 py-2 rounded-md border transition-colors ${
          !hasNext
            ? "bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200"
            : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400"
        }`}
      >
        Trang sau
      </button>

      {/* Thông tin trang */}
      <div className="ml-4 text-sm text-gray-600">
        Trang {currentPage} / {totalPages}
      </div>
    </div>
  );
};

export default Pagination; 