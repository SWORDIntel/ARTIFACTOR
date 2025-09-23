#!/usr/bin/env python3
"""
ARTIFACTOR Chrome Extension Icon Generator
Creates professional extension icons matching ARTIFACTOR branding
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename, state='normal'):
    """Create an ARTIFACTOR extension icon"""

    # ARTIFACTOR brand colors (dark theme)
    if state == 'normal':
        bg_color = '#0078D4'  # Microsoft Blue
        accent_color = '#FFFFFF'
        text_color = '#FFFFFF'
    elif state == 'disabled':
        bg_color = '#404040'  # Gray
        accent_color = '#808080'
        text_color = '#808080'
    elif state == 'error':
        bg_color = '#D13438'  # Red
        accent_color = '#FFFFFF'
        text_color = '#FFFFFF'
    elif state == 'warning':
        bg_color = '#FF8C00'  # Orange
        accent_color = '#FFFFFF'
        text_color = '#FFFFFF'
    else:
        bg_color = '#0078D4'
        accent_color = '#FFFFFF'
        text_color = '#FFFFFF'

    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    margin = max(2, size // 16)
    radius = max(4, size // 8)

    # Background shape
    draw.rounded_rectangle([margin, margin, size-margin, size-margin],
                          radius=radius, fill=bg_color)

    # Draw stylized "A" for ARTIFACTOR
    if size >= 32:
        # For larger icons, draw detailed "A"
        font_size = max(10, size // 2)
        center_x = size // 2
        center_y = size // 2

        # Draw "A" shape
        letter_width = size // 3
        letter_height = size // 2

        # Left line of "A"
        draw.line([(center_x - letter_width//2, center_y + letter_height//2),
                  (center_x, center_y - letter_height//2)],
                 fill=accent_color, width=max(2, size//16))

        # Right line of "A"
        draw.line([(center_x + letter_width//2, center_y + letter_height//2),
                  (center_x, center_y - letter_height//2)],
                 fill=accent_color, width=max(2, size//16))

        # Crossbar of "A"
        crossbar_y = center_y + letter_height//6
        draw.line([(center_x - letter_width//4, crossbar_y),
                  (center_x + letter_width//4, crossbar_y)],
                 fill=accent_color, width=max(2, size//16))

    else:
        # For smaller icons, draw simple shape
        center = size // 2
        inner_size = size // 3
        draw.ellipse([center - inner_size//2, center - inner_size//2,
                     center + inner_size//2, center + inner_size//2],
                    fill=accent_color)

    # Add subtle border
    border_width = max(1, size // 32)
    draw.rounded_rectangle([border_width, border_width,
                          size-border_width, size-border_width],
                          radius=radius, outline=accent_color, width=border_width)

    # Save the icon
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

def main():
    """Generate all required extension icons"""

    # Standard extension icon sizes
    sizes = [16, 32, 48, 128]

    # Create normal icons
    for size in sizes:
        create_icon(size, f'icon-{size}.png', 'normal')

    # Create disabled state icons
    for size in sizes:
        create_icon(size, f'icon-{size}-disabled.png', 'disabled')

    # Create error state icons for notifications
    create_icon(48, 'icon-48-error.png', 'error')
    create_icon(48, 'icon-48-warning.png', 'warning')

    print("\nAll ARTIFACTOR extension icons created successfully!")
    print("Icons follow ARTIFACTOR brand guidelines with:")
    print("- Primary color: #0078D4 (Microsoft Blue)")
    print("- Professional rounded design")
    print("- Clear state differentiation")
    print("- Optimized for all Chrome extension contexts")

if __name__ == '__main__':
    main()