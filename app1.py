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
st.title("🖼️ Advanced Image Converter & Compressor")
st.markdown("Convert images to PDF, compress PDF size, PDF to images, and compress/resize images")

# Function to convert image to PDF with size options
def image_to_pdf(image_file, quality=95, pdf_size=None, compress_pdf=False):
    try:
        image = Image.open(image_file)
        
        # Resize image if pdf_size is specified
        if pdf_size:
            if pdf_size == "A4":
                target_size = (2480, 3508)  # A4 at 300 DPI
            elif pdf_size == "Letter":
                target_size = (2550, 3300)  # Letter at 300 DPI
            elif pdf_size == "Small":
                target_size = (1240, 1754)  # A4 at 150 DPI
            else:  # Original
                target_size = image.size
            
            # Resize maintaining aspect ratio
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        pdf_buffer = BytesIO()
        
        # Save as PDF with compression options
        if compress_pdf:
            # Convert to RGB if needed
            rgb_image = image.convert('RGB')
            # Save with optimization
            rgb_image.save(pdf_buffer, format='PDF', quality=quality, optimize=True)
        else:
            image.save(pdf_buffer, format='PDF', quality=quality)
        
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        st.error(f"Error converting image to PDF: {str(e)}")
        return None

# Function to compress existing PDF
def compress_pdf_file(pdf_file, quality_level="Medium"):
    try:
        # Open the PDF
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        # Create output PDF
        output_buffer = BytesIO()
        output_pdf = fitz.open()
        
        # Quality settings
        quality_settings = {
            "Low": 0.3,
            "Medium": 0.6,
            "High": 0.8,
            "Very High": 1.0
        }
        
        compression_quality = quality_settings.get(quality_level, 0.6)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Get the page as image with compression
            mat = fitz.Matrix(compression_quality, compression_quality)
            pix = page.get_pixmap(matrix=mat)
            
            # Create new page
            new_page = output_pdf.new_page(width=page.rect.width, height=page.rect.height)
            
            # Insert compressed image
            img_data = pix.tobytes("png")
            new_page.insert_image(new_page.rect, stream=img_data)
        
        # Save compressed PDF
        output_pdf.save(output_buffer)
        output_pdf.close()
        pdf_document.close()
        
        output_buffer.seek(0)
        return output_buffer
    except Exception as e:
        st.error(f"Error compressing PDF: {str(e)}")
        return None

# Function to convert PDF to images
def pdf_to_images(pdf_file, dpi=150, output_format="JPEG"):
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            
            if output_format == "JPEG":
                img_data = pix.tobytes("jpeg")
            else:
                img_data = pix.tobytes("png")
                
            img = Image.open(BytesIO(img_data))
            images.append(img)
        
        pdf_document.close()
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {str(e)}")
        return None

# Function to compress image
def compress_image(image, quality=85, max_size=None, output_format="JPEG"):
    try:
        if max_size:
            width, height = image.size
            if width > max_size[0] or height > max_size[1]:
                ratio = min(max_size[0]/width, max_size[1]/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        output_buffer = BytesIO()
        
        # Handle transparency
        if image.mode in ('RGBA', 'LA') and output_format == "JPEG":
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        if output_format == "JPEG":
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        else:
            image.save(output_buffer, format='PNG', optimize=True)
        
        output_buffer.seek(0)
        return output_buffer
    except Exception as e:
        st.error(f"Error compressing image: {str(e)}")
        return None

# Function to get file size
def get_file_size(file_buffer):
    file_buffer.seek(0, 2)
    size = file_buffer.tell()
    file_buffer.seek(0)
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
    if file_format == "pdf":
        mime_type = "application/pdf"
    elif file_format == "jpg":
        mime_type = "image/jpeg"
    else:
        mime_type = f"image/{file_format}"
    
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; margin: 5px;">📥 Download {filename}</a>'
    return href

# Sidebar for navigation
st.sidebar.title("Navigation")
option = st.sidebar.radio(
    "Choose Conversion Type:",
    ["Image to PDF", "Compress PDF", "PDF to Images", "Compress Image", "Resize Image"]
)

# Main content area
if option == "Image to PDF":
    st.header("📄 Convert Image to PDF with Size Control")
    
    uploaded_files = st.file_uploader(
        "Choose images to convert to PDF",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Uploaded Images")
            for uploaded_file in uploaded_files:
                st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
                st.write(f"Size: {format_file_size(len(uploaded_file.getvalue()))}")
        
        with col2:
            st.subheader("PDF Settings")
            
            # PDF Size Options
            pdf_size = st.selectbox(
                "PDF Page Size",
                ["Original", "A4", "Letter", "Small"],
                help="Choose the output PDF page size"
            )
            
            # Compression Options
            compress_pdf = st.checkbox("Enable PDF Compression", value=True)
            pdf_quality = st.slider("PDF Quality", 20, 100, 85)
            
            st.markdown("---")
            st.subheader("Size Information")
            
            if st.button("🚀 Convert to PDF", use_container_width=True):
                with st.spinner("Converting images to PDF..."):
                    if len(uploaded_files) == 1:
                        # Single image to PDF
                        pdf_buffer = image_to_pdf(uploaded_files[0], pdf_quality, pdf_size, compress_pdf)
                        if pdf_buffer:
                            original_size = len(uploaded_files[0].getvalue())
                            pdf_size_bytes = get_file_size(pdf_buffer)
                            
                            st.success("✅ Conversion successful!")
                            
                            col_size1, col_size2 = st.columns(2)
                            with col_size1:
                                st.metric("Original Size", format_file_size(original_size))
                            with col_size2:
                                st.metric("PDF Size", format_file_size(pdf_size_bytes))
                            
                            st.markdown(get_download_link(pdf_buffer, "converted.pdf", "pdf"), unsafe_allow_html=True)
                    else:
                        # Multiple images to single PDF
                        pdf_buffer = BytesIO()
                        images = []
                        
                        for uploaded_file in uploaded_files:
                            image = Image.open(uploaded_file)
                            
                            # Apply size settings to each image
                            if pdf_size:
                                if pdf_size == "A4":
                                    target_size = (2480, 3508)
                                elif pdf_size == "Letter":
                                    target_size = (2550, 3300)
                                elif pdf_size == "Small":
                                    target_size = (1240, 1754)
                                else:
                                    target_size = image.size
                                
                                image.thumbnail(target_size, Image.Resampling.LANCZOS)
                            
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            images.append(image)
                        
                        if images:
                            images[0].save(
                                pdf_buffer, 
                                format='PDF', 
                                save_all=True, 
                                append_images=images[1:],
                                quality=pdf_quality,
                                optimize=compress_pdf
                            )
                            pdf_buffer.seek(0)
                            
                            total_original_size = sum(len(f.getvalue()) for f in uploaded_files)
                            pdf_size_bytes = get_file_size(pdf_buffer)
                            
                            st.success("✅ Conversion successful!")
                            
                            col_size1, col_size2 = st.columns(2)
                            with col_size1:
                                st.metric("Total Original Size", format_file_size(total_original_size))
                            with col_size2:
                                st.metric("PDF Size", format_file_size(pdf_size_bytes))
                                reduction = (total_original_size - pdf_size_bytes) / total_original_size * 100
                                st.metric("Size Reduction", f"{reduction:.1f}%")
                            
                            st.markdown(get_download_link(pdf_buffer, "converted_images.pdf", "pdf"), unsafe_allow_html=True)

elif option == "Compress PDF":
    st.header("📉 Compress PDF File Size")
    
    uploaded_pdf = st.file_uploader("Choose a PDF file to compress", type=['pdf'])
    
    if uploaded_pdf:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Original PDF")
            st.write(f"**File:** {uploaded_pdf.name}")
            original_size = len(uploaded_pdf.getvalue())
            st.write(f"**Size:** {format_file_size(original_size)}")
            
            # Display PDF info
            try:
                pdf_document = fitz.open(stream=uploaded_pdf.getvalue(), filetype="pdf")
                st.write(f"**Pages:** {len(pdf_document)}")
                pdf_document.close()
            except:
                st.write("**Pages:** Unable to read")
        
        with col2:
            st.subheader("Compression Settings")
            
            compression_level = st.selectbox(
                "Compression Level",
                ["Low", "Medium", "High", "Very High"],
                index=1,
                help="Higher compression = smaller file size but lower quality"
            )
            
            st.markdown("---")
            
            if st.button("🔧 Compress PDF", use_container_width=True):
                with st.spinner("Compressing PDF..."):
                    compressed_pdf = compress_pdf_file(uploaded_pdf, compression_level)
                    
                    if compressed_pdf:
                        compressed_size = get_file_size(compressed_pdf)
                        reduction = (original_size - compressed_size) / original_size * 100
                        
                        st.success("✅ Compression successful!")
                        
                        col_orig, col_comp = st.columns(2)
                        with col_orig:
                            st.metric("Original Size", format_file_size(original_size))
                        with col_comp:
                            st.metric("Compressed Size", format_file_size(compressed_size))
                            st.metric("Reduction", f"{reduction:.1f}%")
                        
                        # Download link
                        filename = f"compressed_{uploaded_pdf.name}"
                        st.markdown(get_download_link(compressed_pdf, filename, "pdf"), unsafe_allow_html=True)
                        
                        # Preview first page
                        try:
                            st.subheader("Preview (First Page)")
                            pdf_document = fitz.open(stream=compressed_pdf.getvalue(), filetype="pdf")
                            if len(pdf_document) > 0:
                                page = pdf_document.load_page(0)
                                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                                img_data = pix.tobytes("png")
                                st.image(img_data, caption="First Page Preview", use_column_width=True)
                            pdf_document.close()
                        except Exception as e:
                            st.warning("Could not generate preview")

elif option == "PDF to Images":
    st.header("🖼️ Convert PDF to Images")
    
    uploaded_pdf = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_pdf:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("PDF Info")
            st.write(f"File: {uploaded_pdf.name}")
            st.write(f"Size: {format_file_size(len(uploaded_pdf.getvalue()))}")
            
            # Get page count
            try:
                pdf_document = fitz.open(stream=uploaded_pdf.getvalue(), filetype="pdf")
                page_count = len(pdf_document)
                st.write(f"Pages: {page_count}")
                pdf_document.close()
            except:
                st.write("Pages: Unable to read")
            
            dpi = st.slider("Image Quality (DPI)", 72, 300, 150)
            output_format = st.selectbox("Output Format", ["JPEG", "PNG"])
        
        with col2:
            if st.button("Convert PDF to Images"):
                with st.spinner(f"Converting {page_count} pages..."):
                    images = pdf_to_images(uploaded_pdf, dpi, output_format)
                    if images:
                        st.success(f"✅ Converted {len(images)} pages successfully!")
                        
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
            output_format = st.selectbox("Output Format", ["JPEG", "PNG"])
            
            # Target size selection
            target_size = st.selectbox(
                "Target Size",
                ["No specific target", "Under 100KB", "Under 500KB", "Under 1MB", "Under 5MB"]
            )
            
            size_map = {
                "Under 100KB": (800, 600),
                "Under 500KB": (1200, 900),
                "Under 1MB": (1600, 1200),
                "Under 5MB": (2000, 1500)
            }
            
            max_size = size_map.get(target_size, None)
            
            if st.button("Compress Image"):
                with st.spinner("Compressing image..."):
                    compressed_buffer = compress_image(original_image, quality, max_size, output_format)
                    
                    if compressed_buffer:
                        compressed_size = get_file_size(compressed_buffer)
                        compression_ratio = (original_size - compressed_size) / original_size * 100
                        
                        st.subheader("Compressed Image")
                        compressed_image = Image.open(compressed_buffer)
                        st.image(compressed_image, caption="Compressed", use_column_width=True)
                        
                        col_orig, col_comp = st.columns(2)
                        with col_orig:
                            st.metric("Original Size", format_file_size(original_size))
                        with col_comp:
                            st.metric("Compressed Size", format_file_size(compressed_size))
                            st.metric("Reduction", f"{compression_ratio:.1f}%")
                        
                        filename = f"compressed_image.{'jpg' if output_format == 'JPEG' else 'png'}"
                        st.markdown(get_download_link(compressed_buffer, filename, output_format.lower()), unsafe_allow_html=True)

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
            output_format = st.selectbox("Output Format", ["JPEG", "PNG"])
            
            if st.button("Resize Image"):
                with st.spinner("Resizing image..."):
                    resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    resized_buffer = BytesIO()
                    if resized_image.mode in ('RGBA', 'LA') and output_format == "JPEG":
                        background = Image.new('RGB', resized_image.size, (255, 255, 255))
                        background.paste(resized_image, mask=resized_image.split()[-1])
                        resized_image = background
                    
                    if output_format == "JPEG":
                        resized_image.save(resized_buffer, format='JPEG', quality=quality, optimize=True)
                    else:
                        resized_image.save(resized_buffer, format='PNG', optimize=True)
                    
                    resized_buffer.seek(0)
                    resized_size = get_file_size(resized_buffer)
                    
                    st.subheader("Resized Image")
                    st.image(resized_image, caption=f"Resized to {new_width} x {new_height}", use_column_width=True)
                    
                    col_orig, col_resized = st.columns(2)
                    with col_orig:
                        st.metric("Original Size", format_file_size(original_size))
                        st.metric("Original Dimensions", f"{original_width} x {original_height}")
                    with col_resized:
                        st.metric("Resized Size", format_file_size(resized_size))
                        st.metric("New Dimensions", f"{new_width} x {new_height}")
                    
                    filename = f"resized_image.{'jpg' if output_format == 'JPEG' else 'png'}"
                    st.markdown(get_download_link(resized_buffer, filename, output_format.lower()), unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("### 💡 Tips:")
st.markdown("""
- **Image to PDF**: Use A4/Letter sizes for standard document formats
- **PDF Compression**: Medium compression usually gives the best balance of size and quality
- **PDF to Images**: Higher DPI = better quality but larger file sizes
- **Image Compression**: Start with 85% quality and adjust as needed
- **Resize**: Maintain aspect ratio to avoid image distortion
""")

if __name__ == "__main__":
    pass