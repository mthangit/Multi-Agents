import React, { Fragment, useState, useEffect } from "react";

import { useProductsContext } from "../../contexts";
import AddressCard from "./AddressCard";
import AddressForm from "./AddressForm";

const Address = ({ isEdit }) => {
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [editAddress, setEditAddress] = useState(null);
  const { addressList, getAddressesService } = useProductsContext();

  useEffect(() => {
    // Gọi API để lấy danh sách địa chỉ khi component được tạo
    const fetchAddresses = async () => {
      try {
        await getAddressesService();
      } catch (error) {
        console.error("Error fetching addresses:", error);
      }
    };
    
    fetchAddresses();
  }, [getAddressesService]);

  return (
    <>
      {!isEdit && <h1 className="text-2xl font-bold">Địa chỉ</h1>}
      {showAddressForm && !editAddress ? (
        <AddressForm
          setShowAddressForm={setShowAddressForm}
          editAddress={editAddress}
          setEditAddress={setEditAddress}
        />
      ) : (
        <div className="flex flex-col items-start ">
          <button
            className="btn-rounded-primary text-sm "
            onClick={() => {
              setShowAddressForm(true);
              setEditAddress(false);
            }}
          >
            + Thêm địa chỉ mới
          </button>
        </div>
      )}
      <div className="flex flex-col gap-2">
        {addressList && addressList.length > 0 ? (
          addressList.map((address) => (
            <Fragment key={address.id}>
              {showAddressForm && editAddress?.id === address.id ? (
                <AddressForm
                  setShowAddressForm={setShowAddressForm}
                  editAddress={editAddress}
                  setEditAddress={setEditAddress}
                />
              ) : (
                <AddressCard
                  address={address}
                  isEdit={isEdit}
                  editAddress={editAddress}
                  setEditAddress={setEditAddress}
                  setShowAddressForm={setShowAddressForm}
                />
              )}
            </Fragment>
          ))
        ) : (
          <p className="text-gray-500 mt-4">Bạn chưa có địa chỉ nào. Vui lòng thêm địa chỉ mới.</p>
        )}
      </div>
    </>
  );
};

export default Address;
