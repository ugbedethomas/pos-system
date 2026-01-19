"""
Barcode Utilities for POS System
Handles barcode generation, storage, and management
"""

import os
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import sys


class BarcodeGenerator:
    def __init__(self, barcodes_dir='static/barcodes'):
        """
        Initialize barcode generator

        Args:
            barcodes_dir: Directory to store barcode images (relative to app folder)
        """
        # Get the absolute path to the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        self.barcodes_dir = os.path.join(app_dir, barcodes_dir)
        self.ensure_directory()

    def ensure_directory(self):
        """Create barcodes directory if it doesn't exist"""
        if not os.path.exists(self.barcodes_dir):
            os.makedirs(self.barcodes_dir)
            print(f"Created barcode directory: {self.barcodes_dir}")

    def generate_barcode_image(self, barcode_data, barcode_type='code128',
                               add_checksum=True, options=None):
        """
        Generate a barcode image

        Args:
            barcode_data (str): The data to encode
            barcode_type (str): Type of barcode (code128, ean13, upc, etc.)
            add_checksum (bool): Whether to add checksum
            options (dict): Additional options for barcode writer

        Returns:
            str: Path to the generated barcode image
        """
        try:
            # Validate barcode data
            if not barcode_data or not isinstance(barcode_data, str):
                raise ValueError("Invalid barcode data")

            # Default options for barcode generation
            if options is None:
                options = {
                    'module_width': 0.2,
                    'module_height': 15.0,
                    'quiet_zone': 6.5,
                    'font_size': 10,
                    'text_distance': 5.0,
                    'background': 'white',
                    'foreground': 'black',
                    'write_text': True,
                    'text': barcode_data
                }

            # Get barcode class
            try:
                barcode_class = barcode.get_barcode_class(barcode_type)
            except barcode.errors.BarcodeNotFoundError:
                print(f"Barcode type '{barcode_type}' not found, defaulting to 'code128'")
                barcode_class = barcode.get_barcode_class('code128')

            # Create barcode instance
            barcode_instance = barcode_class(barcode_data, writer=ImageWriter())

            # Clean barcode data for filename
            clean_barcode = ''.join(c for c in barcode_data if c.isalnum())
            if not clean_barcode:
                clean_barcode = 'barcode'

            # Generate filename
            filename = f"{clean_barcode}_{barcode_type}"
            filepath = os.path.join(self.barcodes_dir, filename)

            # Generate and save barcode
            print(f"Generating barcode: {barcode_data} ({barcode_type})")
            full_path = barcode_instance.save(filepath, options)

            print(f"Barcode saved to: {full_path}")
            return full_path

        except Exception as e:
            print(f"Error generating barcode: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return None

    def generate_ean13(self, barcode_data, add_checksum=True):
        """Generate EAN-13 barcode"""
        try:
            # Ensure barcode is 12 digits for EAN-13 (without checksum)
            if len(barcode_data) > 12:
                barcode_data = barcode_data[:12]
            elif len(barcode_data) < 12:
                barcode_data = barcode_data.ljust(12, '0')

            # Validate numeric barcode for EAN-13
            if not barcode_data.isdigit():
                print(f"EAN-13 requires numeric data, got: {barcode_data}")
                return self.generate_code128(barcode_data)

            options = {
                'module_width': 0.2,
                'module_height': 15.0,
                'quiet_zone': 6.5,
                'font_size': 10,
                'text_distance': 5.0,
                'background': 'white',
                'foreground': 'black',
                'write_text': True,
                'text': barcode_data
            }

            return self.generate_barcode_image(barcode_data, 'ean13', add_checksum, options)
        except Exception as e:
            print(f"Error generating EAN-13: {e}")
            return None

    def generate_code128(self, barcode_data):
        """Generate Code 128 barcode (supports alphanumeric)"""
        try:
            options = {
                'module_width': 0.2,
                'module_height': 15.0,
                'quiet_zone': 6.5,
                'font_size': 10,
                'text_distance': 5.0,
                'background': 'white',
                'foreground': 'black',
                'write_text': True,
                'text': barcode_data
            }

            return self.generate_barcode_image(barcode_data, 'code128', True, options)
        except Exception as e:
            print(f"Error generating Code128: {e}")
            return None

    def generate_barcode_for_product(self, product):
        """
        Generate barcode for a product

        Args:
            product: Product object from database

        Returns:
            str: Path to barcode image or None
        """
        try:
            # Use existing barcode if available
            if product.barcode:
                barcode_data = str(product.barcode)
                print(f"Using existing barcode: {barcode_data}")
            else:
                # Generate from SKU or product ID
                if product.sku:
                    barcode_data = product.sku.replace('-', '').replace('_', '')
                else:
                    barcode_data = str(product.id).zfill(8)

                print(f"Generated barcode from product: {barcode_data}")

            # Ensure barcode is valid
            if not barcode_data or len(barcode_data) < 1:
                print("Invalid barcode data")
                return None

            # Choose barcode type based on content
            if barcode_data.isdigit() and len(barcode_data) >= 12:
                # Use EAN-13 for long numeric barcodes
                return self.generate_ean13(barcode_data)
            elif barcode_data.isdigit() and 8 <= len(barcode_data) < 12:
                # Use EAN-8 for shorter numeric barcodes
                return self.generate_barcode_image(barcode_data, 'ean8')
            else:
                # Use Code128 for alphanumeric or shorter codes
                return self.generate_code128(barcode_data)

        except Exception as e:
            print(f"Error generating barcode for product: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_barcode_url(self, product):
        """
        Get barcode image URL for a product

        Args:
            product: Product object

        Returns:
            str: URL to barcode image or None
        """
        if not product or not product.barcode:
            return None

        try:
            # Check if barcode image exists
            barcode_data = str(product.barcode)
            clean_barcode = ''.join(c for c in barcode_data if c.isalnum())

            # Check for existing barcode files
            barcode_types = ['code128', 'ean13', 'ean8', 'upc']
            for barcode_type in barcode_types:
                filename = f"{clean_barcode}_{barcode_type}.png"
                filepath = os.path.join(self.barcodes_dir, filename)

                if os.path.exists(filepath):
                    # Convert to URL path (relative to static)
                    relative_path = os.path.relpath(filepath, os.path.dirname(self.barcodes_dir))
                    return f"/{relative_path.replace(os.sep, '/')}"

            # Generate barcode if it doesn't exist
            barcode_path = self.generate_barcode_for_product(product)
            if barcode_path:
                # Convert to URL path
                relative_path = os.path.relpath(barcode_path, os.path.dirname(self.barcodes_dir))
                return f"/{relative_path.replace(os.sep, '/')}"

            return None

        except Exception as e:
            print(f"Error getting barcode URL: {e}")
            return None

    def delete_barcode_image(self, barcode_data):
        """
        Delete barcode image file

        Args:
            barcode_data (str): Barcode data
        """
        try:
            if not barcode_data:
                return

            # Clean barcode for filename
            clean_barcode = ''.join(c for c in str(barcode_data) if c.isalnum())
            if not clean_barcode:
                return

            # Delete all barcode types for this data
            barcode_types = ['code128', 'ean13', 'ean8', 'upc']
            deleted_count = 0

            for barcode_type in barcode_types:
                filename = f"{clean_barcode}_{barcode_type}.png"
                filepath = os.path.join(self.barcodes_dir, filename)

                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"Deleted barcode: {filepath}")

            if deleted_count > 0:
                print(f"Deleted {deleted_count} barcode files for: {barcode_data}")

        except Exception as e:
            print(f"Error deleting barcode: {e}")

    def list_barcode_files(self):
        """List all barcode files in the directory"""
        try:
            files = []
            for filename in os.listdir(self.barcodes_dir):
                if filename.endswith('.png'):
                    filepath = os.path.join(self.barcodes_dir, filename)
                    size = os.path.getsize(filepath)
                    files.append({
                        'filename': filename,
                        'path': filepath,
                        'size': size
                    })
            return files
        except Exception as e:
            print(f"Error listing barcode files: {e}")
            return []

    def cleanup_orphaned_barcodes(self, valid_barcodes):
        """
        Delete barcode images that don't correspond to existing products

        Args:
            valid_barcodes (list): List of valid barcode strings
        """
        try:
            valid_barcodes = set(str(b) for b in valid_barcodes)
            barcode_files = self.list_barcode_files()
            deleted_count = 0

            for barcode_file in barcode_files:
                filename = barcode_file['filename']
                # Extract barcode from filename (format: barcode_type.png)
                barcode_from_file = filename.split('_')[0]

                if barcode_from_file not in valid_barcodes:
                    try:
                        os.remove(barcode_file['path'])
                        deleted_count += 1
                        print(f"Deleted orphaned barcode: {filename}")
                    except Exception as e:
                        print(f"Error deleting orphaned barcode {filename}: {e}")

            print(f"Cleanup complete: Deleted {deleted_count} orphaned barcode files")
            return deleted_count

        except Exception as e:
            print(f"Error in barcode cleanup: {e}")
            return 0


# Global instance for easy import
barcode_generator = BarcodeGenerator()


# Test function
def test_barcode_generation():
    """Test barcode generation"""
    print("Testing barcode generation...")

    # Create test directory
    test_dir = 'test_barcodes'
    test_generator = BarcodeGenerator(test_dir)

    # Test barcodes
    test_cases = [
        ('123456789012', 'ean13'),
        ('12345678', 'ean8'),
        ('TEST-001', 'code128'),
        ('PRODUCT-123', 'code128'),
    ]

    for barcode_data, barcode_type in test_cases:
        print(f"\nGenerating {barcode_type} barcode: {barcode_data}")
        result = test_generator.generate_barcode_image(barcode_data, barcode_type)
        if result:
            print(f"✓ Success: {result}")
        else:
            print(f"✗ Failed: {barcode_data}")

    # List generated files
    print(f"\nGenerated files in {test_dir}:")
    for file_info in test_generator.list_barcode_files():
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")

    print("\nTest complete!")


if __name__ == "__main__":
    # Run test if file is executed directly
    test_barcode_generation()