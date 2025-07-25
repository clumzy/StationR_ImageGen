import os
import base64
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List
from typing import Tuple

def generate_freq_image(frequency: str, scene_genre: str, scene_name: str, 
                       radio_station_name: str, verbatims: List[str], tags: List[str], artists: List[str],
                       output_path: str = None, assets_dir: str = "assets") -> str:
    """
    Génère une image, avec informations de fréquence, genre, nom de scène, radio et différents types de pills.

    Arguments :
        frequency : (str) Fréquence à afficher (ex: "97.3")
        scene_genre : (str) Genre musical de la scène (ex: "House solaire")
        scene_name : (str) Nom de la scène ("Le Refuge" ou "L'Atrium")
        radio_station_name : (str) Nom de la radio ou de la programmation
        verbatims : (List[str]) Liste de verbatims (fond gris)
        tags : (List[str]) Liste de tags (fond blanc)
        artists : (List[str]) Liste d'artistes (fond coloré selon la scène)
        output_path : (str, optionnel) Chemin de sauvegarde de l'image générée. Si None, un nom par défaut est utilisé.
        assets_dir : (str, optionnel) Dossier contenant les assets (images et polices). Par défaut "assets".

    Returns :
        str : Image encodée en base64
    """
    # Helper functions 
    def draw_text_with_tracking(draw, position, text, font, fill, tracking):
        """Draw text with custom letter spacing."""
        x, y = position
        for char in text:
            draw.text((x, y), char, fill=fill, font=font)
            x += font.getlength(char) + tracking

    def draw_wrapped_text(draw, text, font, fill, pos, max_width, line_spacing=8, tracking=None, max_lines=None):
        """Draw text with word wrapping."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Truncate to max_lines if specified
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            # Add ellipsis to the last line if truncated
            last_line = lines[-1]
            while True:
                test_line = last_line + '...'
                test_width = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
                if test_width <= max_width or len(last_line) <= 3:
                    lines[-1] = (last_line, '...')  # Store as tuple to indicate ellipsis
                    break
                last_line = last_line[:-1]
        
        for i, line in enumerate(lines):
            line_pos = (pos[0], pos[1] + i * (font.size + line_spacing))
            if isinstance(line, tuple):
                # Handle line with ellipsis (no tracking for ellipsis)
                text_part, ellipsis = line
                if tracking is not None:
                    draw_text_with_tracking(draw, line_pos, text_part, font, fill, tracking)
                    # Calculate position for ellipsis after the tracked text
                    text_width = sum(font.getlength(char) + tracking for char in text_part[:-1]) + font.getlength(text_part[-1]) if text_part else 0
                    ellipsis_pos = (line_pos[0] + text_width, line_pos[1])
                    draw.text(ellipsis_pos, ellipsis, fill=fill, font=font)
                else:
                    draw.text(line_pos, text_part + ellipsis, fill=fill, font=font)
            elif tracking is not None:
                draw_text_with_tracking(draw, line_pos, line, font, fill, tracking)
            else:
                draw.text(line_pos, line, fill=fill, font=font)
    
    def draw_pill(draw, text, font, text_fill, pill_fill, pos=None, 
                  relative_to=None, relative_to_text=None, relative_to_font=None,
                  gap=0, offset=(0, 0), padding_x=40, pill_height=72):
        """Draw a pill (rounded rectangle) with perfectly centered text."""
        # Calculate pill dimensions
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        pill_width = text_width + 2 * padding_x
        
        # Calculate pill position
        if pos is not None:
            pill_x, pill_y = pos
        elif relative_to and relative_to_text and relative_to_font:
            ref_bbox = relative_to_font.getbbox(relative_to_text)
            ref_width = ref_bbox[2] - ref_bbox[0]
            ref_height = ref_bbox[3] - ref_bbox[1]
            pill_x = relative_to[0] + ref_width + gap
            pill_y = relative_to[1] + (ref_height - pill_height) // 2
        elif relative_to:
            pill_x, pill_y = relative_to
        else:
            pill_x, pill_y = (0, 0)
        
        pill_x += offset[0]
        pill_y += offset[1]
        
        # Draw the pill shape
        draw.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_width, pill_y + pill_height],
            radius=pill_height // 2,
            fill=pill_fill
        )
        
        # Center text in pill
        text_x = pill_x + (pill_width - text_width) // 2 - text_bbox[0]
        
        # Use font metrics for consistent vertical centering
        ascent, descent = font.getmetrics()
        baseline_y = pill_y + pill_height // 2 + descent // 2 + 7
        text_y = baseline_y - ascent
        
        draw.text((text_x, text_y), text, fill=text_fill, font=font)
        return (pill_x, pill_y, pill_x + pill_width, pill_y + pill_height)

    # Determine which background image to use
    if scene_name.lower() == "l'atrium":
        bg_image_path = os.path.join(assets_dir, "orange.png")
    elif scene_name.lower() == "le refuge":
        bg_image_path = os.path.join(assets_dir, "purple.png")
    else:
        raise ValueError(f"Unknown scene_name: {scene_name}. Must be 'Le Refuge' or 'L'Atrium'")
    
    # Check if background image exists
    if not os.path.exists(bg_image_path):
        raise FileNotFoundError(f"Background image not found: {bg_image_path}")
    
    # Open the background image
    image = Image.open(bg_image_path)
    draw = ImageDraw.Draw(image)
    
    # Load fonts
    def load_font(font_path, size):
        """Load a font with fallback to default if not found."""
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            return ImageFont.load_default()
    
    frequency_font = load_font(os.path.join(assets_dir, "Obviously-MediumItalic.otf"), 174)
    scene_genre_font = load_font(os.path.join(assets_dir, "DarkerGrotesque-SemiBold.ttf"), 60)
    scene_name_font = load_font(os.path.join(assets_dir, "DarkerGrotesque-ExtraBold.ttf"), 54)
    date_font = load_font(os.path.join(assets_dir, "DarkerGrotesque-ExtraBold.ttf"), 69)
    radio_station_font = load_font(os.path.join(assets_dir, "Obviously-MediumItalic.otf"), 127)
    tags_font = load_font(os.path.join(assets_dir, "DarkerGrotesque-ExtraBold.ttf"), 42)
    
    # Get image dimensions
    width, height = image.size
    # Colors
    WHITE = (255, 255, 255, 255)
    BLACK = (0, 0, 0, 255)
    GREY = (113, 102, 102, 255)
    
    # Scene-specific colors
    if scene_name.lower() == "l'atrium":
        pill_bg_color = (255, 134, 53, 255)
    elif scene_name.lower() == "le refuge":
        pill_bg_color = (182, 140, 254, 255)
    
    # Draw all elements
    # 1. Frequency
    draw_text_with_tracking(draw, (66, 311), f"{frequency} FM", 
                           frequency_font, WHITE, tracking=-8)
    
    # 2. Scene genre text
    scene_genre_text = f"{scene_genre} dans"
    scene_genre_pos = (66, 460)
    draw.text(scene_genre_pos, scene_genre_text, fill=BLACK, font=scene_genre_font)
    
    # 3. Scene name pill (next to genre text)
    draw_pill(draw, scene_name, scene_name_font, BLACK, pill_bg_color,
              relative_to=scene_genre_pos, relative_to_text=scene_genre_text, 
              relative_to_font=scene_genre_font, gap=24, offset=(0, 32),
              padding_x=25, pill_height=72)
    
    # 4. Date
    draw.text((66, 520), "le 31 juillet à La Rotonde", fill=BLACK, font=date_font)
    
    # 5. Radio station name (with wrapping, max 3 lines)
    draw_wrapped_text(draw, radio_station_name, radio_station_font, WHITE,
                     (66, 800), max_width=width-200, line_spacing=8, tracking=-7, max_lines=3)
    # 6. Mixed pills (verbatims, tags, artists) across max 4 lines
    all_pills = []
    
    # Add verbatims (grey background)
    for verbatim in verbatims:
        all_pills.append(('verbatim', verbatim, GREY))
    
    # Add tags (white background)
    for tag in tags:
        all_pills.append(('tag', tag, WHITE))
    
    # Add artists (colored background)
    for artist in artists:
        all_pills.append(('artist', artist, pill_bg_color))
    
    # Mix the pills randomly with a fixed seed for reproducibility
    random.seed(420)
    random.shuffle(all_pills)
    
    if all_pills:
        pill_start_x = 66
        pill_start_y = 1300
        pill_gap_y = 24
        pill_gap_x = 24
        max_pill_right = width - 66
        pill_height = 78
        max_lines = 4
        
        # Distribute pills across lines trying to fit as many as possible per line
        lines = []
        current_line = []
        current_line_width = 0
        
        for pill_type, pill_text, pill_bg in all_pills:
            # Calculate pill width
            text_width = tags_font.getbbox(pill_text)[2] - tags_font.getbbox(pill_text)[0]
            pill_width = text_width + 50  # 25px padding on each side
            
            # Check if this pill fits on current line
            needed_width = pill_width
            if current_line:
                needed_width += pill_gap_x
            
            if current_line_width + needed_width <= (max_pill_right - pill_start_x) and len(lines) < max_lines:
                # Fits on current line
                current_line.append((pill_type, pill_text, pill_bg))
                current_line_width += needed_width
            else:
                # Start new line if we haven't reached max lines
                if current_line:
                    lines.append(current_line)
                    current_line = []
                    current_line_width = 0
                
                if len(lines) < max_lines:
                    current_line.append((pill_type, pill_text, pill_bg))
                    current_line_width = pill_width
                else:
                    # We've reached max lines, stop adding pills
                    break
        
        # Add the last line if it has pills
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        
        # Draw the pills
        for line_num, line_pills in enumerate(lines):
            y = pill_start_y + line_num * (pill_height + pill_gap_y)
            x = pill_start_x
            
            for pill_type, pill_text, pill_bg in line_pills:
                # Truncate text if needed to fit
                display_text = pill_text
                max_text_width = max_pill_right - x - 50  # Account for padding
                
                while (tags_font.getbbox(display_text)[2] - tags_font.getbbox(display_text)[0] > max_text_width 
                       and len(display_text) > 6):
                    display_text = display_text[:-4] + '...'
                
                # Draw the pill
                bbox = draw_pill(draw, display_text, tags_font, BLACK, pill_bg,
                               pos=(x, y), padding_x=25, pill_height=pill_height)
                
                # Move x position for next pill
                x = bbox[2] + pill_gap_x
    
    # Convert image to base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Optionally save to file if output_path is provided
    if output_path is not None:
        image.save(output_path)
    
    return image_base64


# Example usage
if __name__ == "__main__":
    # Example for L'Atrium (orange background)
    output1 = generate_freq_image(
        frequency="97.3",
        scene_genre="House solaire",
        scene_name="L'Atrium",
        radio_station_name="House solaire et organique",
        verbatims=["Open-air au coucher du soleil", "Flottant et groovy"],
        tags=["Défensif", "Paisible", "Révélateur", "Percutant", "Hypnotique"],
        artists=["Dom Dolla", "The Blessed Madonna", "X-coast", "Ollie Lishman"],
        output_path="output_latrium.png"  # Will save to file AND return base64
    )
    print(f"Generated base64 (length: {len(output1)} chars)")
    
    # Example for Le Refuge (purple background) - no file output
    output2 = generate_freq_image(
        frequency="108.9",
        scene_genre="Techno sombre",
        scene_name="Le Refuge",
        radio_station_name="Techno hypnotique et mentale",
        verbatims=["Un club sombre", "Il faut que je me dépense"],
        tags=["Industriel", "Énergique", "Nocturne", "Intense", "Transcendant"],
        artists=["I Hate Models", "Clara Cuvé", "Reiner Zonneveld", "Rebekah"],
        output_path="output_le_refuge.png"
    )
    print(f"Generated base64 (length: {len(output2)} chars)")
    # Create HTML file to display the image
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Generated Radio Station Image</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 8px;
        }}
        .info {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Generated Radio Station Image - L'Atrium</h1>
        <img src="data:image/png;base64,{output2}" alt="Generated radio station image">
        <div class="info">
            <h3>Image Details:</h3>
            <p><strong>Frequency:</strong> 97.3 FM</p>
            <p><strong>Scene:</strong> House solaire dans L'Atrium</p>
            <p><strong>Radio:</strong> House solaire et organique</p>
            <p><strong>Base64 length:</strong> {len(output2)} characters</p>
        </div>
    </div>
</body>
</html>
"""
        
    html_file = "test_image_display.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML file created: {html_file}")
    print("Open this file in your web browser to view the generated image.")
    
    # Try to open in default browser (Windows)
    try:
        import webbrowser
        webbrowser.open(html_file)
        print("Attempting to open in default browser...")
    except Exception as e:
        print(f"Could not auto-open browser: {e}")
    

