from pdf2docx import Converter

def convert_pdf_to_docx(pdf_file_path: str, docx_file_path: str):
    """
    Converts a PDF file to a DOCX file.

    Args:
        pdf_file_path: The path to the input PDF file.
        docx_file_path: The path to save the output DOCX file.
    """
    try:
        # Create a Converter object
        cv = Converter(pdf_file_path)
        # Convert PDF to DOCX
        cv.convert(docx_file_path, start=0, end=None)
        # Close the converter
        cv.close()
        print(f"Successfully converted '{pdf_file_path}' to '{docx_file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # --- IMPORTANT ---
    # Replace these with the a/tual /aths/to your files
    input_pdf_path = "C:/Users/Admin/KLTN/OrderManagementAgents/shopping_agent/2025_FEB-EHS-Brochure-ENGLISH_20250508120429-trang-1.pdf"  # Example: "C:/Users/YourUser/Documents/report.pdf"
    output_docx_path = "ouput.docx" # Example: "C:/Users/YourUser/Documents/report.docx"
    
    # Check if the placeholder paths have been changed
    if input_pdf_path == "your_input.pdf" or output_docx_path == "your_output.docx":
        print("Please update the input_pdf_path and output_docx_path variables in the script with your actual file paths.")
    else:
        convert_pdf_to_docx(input_pdf_path, output_docx_path)
