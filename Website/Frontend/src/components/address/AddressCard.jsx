import { useProductsContext } from "../../contexts";

const AddressCard = ({
  address,
  isEdit,
  showInput = true,
  editAddress,
  setEditAddress,
  setShowAddressForm,
}) => {
  const { id, name, phone, address: addressLine, city, country, is_default } = address;
  const { currentAddress, setCurrentAddress, updateAddress, deleteAddress } =
    useProductsContext();
  return (
    <label
      className={`flex ${
        id === currentAddress?.id && isEdit ? "bg-gray-100" : "bg-gray-50"
      }  items-center gap-2 shadow-sm p-4 rounded-sm cursor-pointer`}
    >
      {showInput && (
        <input
          type="radio"
          name="address"
          id=""
          className="accent-current me-2"
          checked={id === currentAddress?.id}
          onChange={() => setCurrentAddress(address)}
        />
      )}
      <div>
        <h3 className="text-lg font-semibold break-all">{name}</h3>
        <p className="text-sm text-gray-500 break-all">
          {addressLine}
        </p>
        <p className="text-sm text-gray-500 break-all">
          {city}, {country}
        </p>
        <p className="text-sm text-gray-500">
          Số điện thoại:
          <span className="font-semibold ps-1 break-all">{phone}</span>
        </p>
        {is_default && (
          <p className="text-sm text-green-600 font-semibold">Địa chỉ mặc định</p>
        )}
        {isEdit && (
          <div className="flex gap-3 py-2">
            <button
              className="text-blue-500 font-bold"
              onClick={() => {
                setEditAddress(address);
                setShowAddressForm(true);
              }}
            >
              Chỉnh sửa
            </button>
            <button
              className="text-blue-600 font-bold"
              onClick={() => deleteAddress(id)}
            >
              Xóa
            </button>
          </div>
        )}
      </div>
    </label>
  );
};
export default AddressCard;
