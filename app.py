import streamlit as st
import os
from PIL import Image
import fitz  # PyMuPDF
from io import BytesIO
import base64

# Set page configuration
st.set_page_config(
    page_title="Image Converter & Compressor",
    page_icon="🖼️",
    layout="wide"
)

# Title and description
st.title("🖼️ Image Converter & Compressor")
st.markdown("Convert images to PDF, PDF to images, and compress/resize images")

# Function to convert image to PDF
def image_to_pdf(image_file, quality=95):
    try:
        image = Image.open(image_file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        pdf_buffer = BytesIO()
        image.save(pdf_buffer, format='PDF', quality=quality)
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        st.error(f"Error converting image to PDF: {str(e)}")
        return None

# Function to convert PDF to images
def pdf_to_images(pdf_file, dpi=150):
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor for higher quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            img = Image.open(BytesIO(img_data))
            images.append(img)
        
        pdf_document.close()
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {str(e)}")
        return None

# Function to compress image
def compress_image(image, quality=85, max_size=None):
    try:
        if max_size:
            # Calculate new dimensions while maintaining aspect ratio
            width, height = image.size
            if width > max_size[0] or height > max_size[1]:
                ratio = min(max_size[0]/width, max_size[1]/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        output_buffer = BytesIO()
        
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        output_buffer.seek(0)
        
        return output_buffer
    except Exception as e:
        st.error(f"Error compressing image: {str(e)}")
        return None

# Function to get file size
def get_file_size(file_buffer):
    file_buffer.seek(0, 2)  # Seek to end
    size = file_buffer.tell()
    file_buffer.seek(0)  # Reset to beginning
    return size

# Function to format file size
def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    else:
        return f"{size_bytes/(1024*1024):.2f} MB"

# Function to create download link
def get_download_link(file_buffer, filename, file_format):
    b64 = base64.b64encode(file_buffer.getvalue()).decode()
    href = f'<a href="data:application/{file_format};base64,{b64}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Download {filename}</a>'
    return href

# Sidebar for navigation
st.sidebar.title("Navigation")
option = st.sidebar.radio(
    "Choose Conversion Type:",
    ["Image to PDF", "PDF to Images", "Compress Image", "Resize Image"]
)

# Main content area
if option == "Image to PDF":
    st.header("📄 Convert Image to PDF")
    
    uploaded_files = st.file_uploader(
        "Choose images to convert to PDF",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Uploaded Images")
            for uploaded_file in uploaded_files:
                st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
                st.write(f"Size: {format_file_size(len(uploaded_file.getvalue()))}")
        
        with col2:
            st.subheader("PDF Options")
            pdf_quality = st.slider("PDF Quality", 50, 100, 95)
            
            if st.button("Convert to PDF"):
                if len(uploaded_files) == 1:
                    # Single image to PDF
                    pdf_buffer = image_to_pdf(uploaded_files[0], pdf_quality)
                    if pdf_buffer:
                        st.success("Conversion successful!")
                        st.markdown(get_download_link(pdf_buffer, "converted.pdf", "pdf"), unsafe_allow_html=True)
                else:
                    # Multiple images to single PDF
                    pdf_buffer = BytesIO()
                    images = []
                    
                    for uploaded_file in uploaded_files:
                        image = Image.open(uploaded_file)
                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        images.append(image)
                    
                    if images:
                        images[0].save(pdf_buffer, format='PDF', save_all=True, append_images=images[1:])
                        pdf_buffer.seek(0)
                        st.success("Conversion successful!")
                        st.markdown(get_download_link(pdf_buffer, "converted_images.pdf", "pdf"), unsafe_allow_html=True)

elif option == "PDF to Images":
    st.header("🖼️ Convert PDF to Images")
    
    uploaded_pdf = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_pdf:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("PDF Info")
            st.write(f"File: {uploaded_pdf.name}")
            st.write(f"Size: {format_file_size(len(uploaded_pdf.getvalue()))}")
            
            dpi = st.slider("Image Quality (DPI)", 72, 300, 150)
            output_format = st.selectbox("Output Format", ["JPEG", "PNG"])
        
        with col2:
            if st.button("Convert PDF to Images"):
                images = pdf_to_images(uploaded_pdf, dpi)
                if images:
                    st.success(f"Converted {len(images)} pages successfully!")
                    
                    for i, image in enumerate(images):
                        st.subheader(f"Page {i+1}")
                        st.image(image, use_column_width=True)
                        
                        # Convert to desired format
                        img_buffer = BytesIO()
                        if output_format == "JPEG":
                            if image.mode == 'RGBA':
                                image = image.convert('RGB')
                            image.save(img_buffer, format='JPEG', quality=95)
                            ext = "jpg"
                        else:
                            image.save(img_buffer, format='PNG')
                            ext = "png"
                        
                        img_buffer.seek(0)
                        filename = f"page_{i+1}.{ext}"
                        st.markdown(get_download_link(img_buffer, filename, ext), unsafe_allow_html=True)

elif option == "Compress Image":
    st.header("📉 Compress Image")
    
    uploaded_image = st.file_uploader("Choose an image to compress", type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'])
    
    if uploaded_image:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Image")
            original_image = Image.open(uploaded_image)
            st.image(original_image, caption="Original", use_column_width=True)
            original_size = len(uploaded_image.getvalue())
            st.write(f"Original Size: {format_file_size(original_size)}")
        
        with col2:
            st.subheader("Compression Settings")
            quality = st.slider("Compression Quality", 10, 100, 85)
            
            # Target size selection
            target_size = st.selectbox(
                "Target Size",
                ["No specific target", "Under 100KB", "Under 500KB", "Under 1MB", "Under 5MB"]
            )
            
            if st.button("Compress Image"):
                compressed_buffer = compress_image(original_image, quality)
                
                if compressed_buffer:
                    compressed_size = get_file_size(compressed_buffer)
                    compression_ratio = (original_size - compressed_size) / original_size * 100
                    
                    st.subheader("Compressed Image")
                    compressed_image = Image.open(compressed_buffer)
                    st.image(compressed_image, caption="Compressed", use_column_width=True)
                    st.write(f"Compressed Size: {format_file_size(compressed_size)}")
                    st.write(f"Reduction: {compression_ratio:.1f}%")
                    
                    st.markdown(get_download_link(compressed_buffer, "compressed_image.jpg", "jpeg"), unsafe_allow_html=True)

elif option == "Resize Image":
    st.header("📏 Resize Image")
    
    uploaded_image = st.file_uploader("Choose an image to resize", type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'])
    
    if uploaded_image:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Image")
            original_image = Image.open(uploaded_image)
            st.image(original_image, caption="Original", use_column_width=True)
            original_size = len(uploaded_image.getvalue())
            original_width, original_height = original_image.size
            st.write(f"Original Size: {format_file_size(original_size)}")
            st.write(f"Dimensions: {original_width} x {original_height}")
        
        with col2:
            st.subheader("Resize Settings")
            
            resize_method = st.radio(
                "Resize Method",
                ["Percentage", "Specific Dimensions", "Preset Sizes"]
            )
            
            if resize_method == "Percentage":
                scale_percent = st.slider("Scale Percentage", 10, 200, 50)
                new_width = int(original_width * scale_percent / 100)
                new_height = int(original_height * scale_percent / 100)
            
            elif resize_method == "Specific Dimensions":
                col_a, col_b = st.columns(2)
                with col_a:
                    new_width = st.number_input("Width", min_value=1, max_value=5000, value=original_width)
                with col_b:
                    new_height = st.number_input("Height", min_value=1, max_value=5000, value=original_height)
            
            else:  # Preset Sizes
                preset = st.selectbox(
                    "Choose Preset Size",
                    ["Small (800x600)", "Medium (1024x768)", "Large (1920x1080)", "Custom"]
                )
                
                if preset == "Small (800x600)":
                    new_width, new_height = 800, 600
                elif preset == "Medium (1024x768)":
                    new_width, new_height = 1024, 768
                elif preset == "Large (1920x1080)":
                    new_width, new_height = 1920, 1080
                else:
                    new_width = st.number_input("Custom Width", min_value=1, max_value=5000, value=800)
                    new_height = st.number_input("Custom Height", min_value=1, max_value=5000, value=600)
            
            maintain_aspect = st.checkbox("Maintain Aspect Ratio", value=True)
            
            if maintain_aspect and resize_method != "Percentage":
                ratio = original_width / original_height
                if new_width / new_height > ratio:
                    new_width = int(new_height * ratio)
                else:
                    new_height = int(new_width / ratio)
            
            quality = st.slider("Output Quality", 10, 100, 85)
            
            if st.button("Resize Image"):
                resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                resized_buffer = BytesIO()
                if resized_image.mode == 'RGBA':
                    resized_image = resized_image.convert('RGB')
                
                resized_image.save(resized_buffer, format='JPEG', quality=quality, optimize=True)
                resized_buffer.seek(0)
                
                resized_size = get_file_size(resized_buffer)
                
                st.subheader("Resized Image")
                st.image(resized_image, caption=f"Resized to {new_width} x {new_height}", use_column_width=True)
                st.write(f"New Size: {format_file_size(resized_size)}")
                st.write(f"New Dimensions: {new_width} x {new_height}")
                
                st.markdown(get_download_link(resized_buffer, "resized_image.jpg", "jpeg"), unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("### 💡 Tips:")
st.markdown("""
- For best PDF quality, use high-resolution images
- Higher DPI settings in PDF to image conversion result in better quality but larger files
- Experiment with compression quality to find the right balance between size and quality
- Maintain aspect ratio when resizing to avoid distortion
""")

if __name__ == "__main__":
    pass