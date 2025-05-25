import qrcode
import os
from io import BytesIO
import base64

def generate_qr_code(url, output_path=None, size=10):
    """
    Generate a QR code for the given URL.
    
    Args:
        url: The URL to encode in the QR code
        output_path: Optional path to save the QR code image
        size: Size of the QR code (default: 10)
        
    Returns:
        If output_path is provided, saves the QR code to that path and returns the path.
        Otherwise, returns the QR code as a base64 encoded string.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    if output_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Save the image
        img.save(output_path)
        return output_path
    else:
        # Return as base64 encoded string
        buffered = BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

if __name__ == "__main__":
    # Example usage
    telegram_url = "https://t.me/CurrentAdda"
    
    # Generate and save QR code
    output_path = os.path.join("templates", "telegram_qr.png")
    generate_qr_code(telegram_url, output_path)
    print(f"QR code saved to {output_path}")
    
    # Generate QR code as base64 string
    qr_base64 = generate_qr_code(telegram_url)
    print("Base64 QR code generated successfully") 