import os
from PIL import Image, ImageDraw, ImageFont
from typing import List
from typing import Tuple

def generate_freq_image(frequency: str, scene_genre: str, scene_name: str, 
                       radio_station_name: str, tags: List[str], 
                       output_path: str = None) -> str:
    """
    Génère une image, avec informations de fréquence, genre, nom de scène, radio et tags, sur un fond spécifique à la scène.

    Arguments :
        frequency : (str) Fréquence à afficher (ex: "97.3")
        scene_genre : (str) Genre musical de la scène (ex: "House solaire")
        scene_name : (str) Nom de la scène ("Le Refuge" ou "L'Atrium")
        radio_station_name : (str) Nom de la radio ou de la programmation
        tags : (List[str]) Liste de 5 tags descriptifs affichés sous forme de "pills"
        output_path : (str, optionnel) Chemin de sauvegarde de l'image générée. Si None, un nom par défaut est utilisé.

    Retourne :
        str : Chemin du fichier image généré

    Notes :
        - Le fond est orange pour "L'Atrium" et violet pour "Le Refuge".
        - Les polices et couleurs sont adaptées à chaque élément.
        - Les tags sont affichés en 3 lignes de pills, avec gestion automatique du texte et de la couleur selon la scène.
        - Nécessite les fichiers d'assets (images et polices) dans le dossier "assets".
    """
    # Helper functions 
    def draw_text_with_tracking(
        draw: ImageDraw.ImageDraw,
        position: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: Tuple[int, int, int, int],
        tracking: int
    ) -> None:
        """
        Draw text with custom letter spacing (tracking).
        Args:
            draw: ImageDraw.Draw object
            position: (x, y) tuple
            text: string to draw
            font: ImageFont instance
            fill: color tuple
            tracking: int, additional space (can be negative) between characters
        """
        x, y = position
        for char in text:
            draw.text((x, y), char, fill=fill, font=font)
            # Use advance width for accurate horizontal positioning
            try:
                # Pillow >= 8.0.0
                char_width = font.getlength(char)
            except AttributeError:
                # Fallback for older Pillow
                char_width = font.getmask(char).size[0]
            x += char_width + tracking
        return

    def draw_wrapped_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: tuple,
        pos: tuple,
        max_width: int,
        line_spacing: int = 8,
        tracking: int = None
    ) -> None:
        """
        Draws text with word wrapping at the given position, using the provided font and color.
        Each line will not exceed max_width in pixels.
        """
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            try:
                test_line_width = font.getbbox(test_line)[2] - font.getbbox(test_line)[0]
            except AttributeError:
                test_line_width = font.getsize(test_line)[0]
            if test_line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(' '.join(current_line))
        for i, line in enumerate(lines):
            line_pos = (pos[0], pos[1] + i * (font.size + line_spacing))
            if tracking is not None:
                draw_text_with_tracking(draw, line_pos, line, font, fill, tracking)
            else:
                draw.text(line_pos, line, fill=fill, font=font)
        return
    
    def draw_pill(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        text_fill: tuple,
        pill_fill: tuple,
        pos: tuple = None,
        relative_to: tuple = None,
        relative_to_text: str = None,
        relative_to_font: ImageFont.FreeTypeFont = None,
        gap: int = 0,
        offset: tuple = (0, 0),
        padding_x: int = 40,
        padding_y: int = 18
    ) -> tuple:
        """
        Draws a pill (rounded rectangle) with centered text.
        - If pos is given, places pill absolutely at pos (top-left of pill).
        - If relative_to and relative_to_text and relative_to_font are given, places pill to the right of the text, with gap and vertical centering.
        - If only relative_to is given, places pill to the right of the given (x, y) position.
        - offset is always added to the final (x, y).
        Returns the bounding box (x0, y0, x1, y1) of the pill.
        """
        # Measure text size
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        pill_width = text_width + 2 * padding_x
        pill_height = text_height + 2 * padding_y
        if pos is not None:
            pill_x, pill_y = pos
        elif relative_to is not None and relative_to_text is not None and relative_to_font is not None:
            # Place to the right of the text, with gap and vertical centering
            ref_bbox = relative_to_font.getbbox(relative_to_text)
            ref_width = ref_bbox[2] - ref_bbox[0]
            ref_height = ref_bbox[3] - ref_bbox[1]
            pill_x = relative_to[0] + ref_width + gap
            pill_y = relative_to[1] + (ref_height - pill_height) // 2
        elif relative_to is not None:
            pill_x = relative_to[0]
            pill_y = relative_to[1]
        else:
            pill_x, pill_y = (0, 0)
        pill_x += offset[0]
        pill_y += offset[1]
        # Draw rounded rectangle (Pillow >= 8.2.0)
        try:
            draw.rounded_rectangle(
                [pill_x, pill_y, pill_x + pill_width, pill_y + pill_height],
                radius=pill_height // 2,
                fill=pill_fill
            )
        except AttributeError:
            draw.rectangle([pill_x + pill_height//2, pill_y, pill_x + pill_width - pill_height//2, pill_y + pill_height], fill=pill_fill)
            draw.ellipse([pill_x, pill_y, pill_x + pill_height, pill_y + pill_height], fill=pill_fill)
            draw.ellipse([pill_x + pill_width - pill_height, pill_y, pill_x + pill_width, pill_y + pill_height], fill=pill_fill)
        # Draw text centered in pill
        text_x = pill_x + (pill_width - text_width) // 2 - text_bbox[0]
        text_y = pill_y + (pill_height - text_height) // 2 - text_bbox[1]
        draw.text((text_x, text_y), text, fill=text_fill, font=font)
        return (pill_x, pill_y, pill_x + pill_width, pill_y + pill_height)

    # Determine which background image to use
    if scene_name.lower() == "l'atrium":
        bg_image_path = os.path.join("assets", "orange.png")
    elif scene_name.lower() == "le refuge":
        bg_image_path = os.path.join("assets", "purple.png")
    else:
        raise ValueError(f"Unknown scene_name: {scene_name}. Must be 'Le Refuge' or 'L'Atrium'")
    
    # Check if background image exists
    if not os.path.exists(bg_image_path):
        raise FileNotFoundError(f"Background image not found: {bg_image_path}")
    
    # Open the background image
    image = Image.open(bg_image_path)
    draw = ImageDraw.Draw(image)
    
    # Load individual fonts for each element
    try:
        frequency_font = ImageFont.truetype(os.path.join("assets","Obviously-MediumItalic.otf"), 174)
    except (OSError, IOError):
            frequency_font = ImageFont.load_default()
    
    try:
        scene_genre_font = ImageFont.truetype(os.path.join("assets","DarkerGrotesque-SemiBold.ttf"), 60)
    except (OSError, IOError):
        scene_genre_font = ImageFont.load_default()
    
    try:
        scene_name_font = ImageFont.truetype(os.path.join("assets","DarkerGrotesque-ExtraBold.ttf"), 54)
    except (OSError, IOError):
        scene_name_font = ImageFont.load_default()
    
    try:
        date_font = ImageFont.truetype(os.path.join("assets","DarkerGrotesque-ExtraBold.ttf"), 80)
    except (OSError, IOError):
        date_font = ImageFont.load_default()

    try:
        # Radio station font - medium sans-serif
        radio_station_font = ImageFont.truetype(os.path.join("assets","Obviously-MediumItalic.otf"), 127)
    except (OSError, IOError):
        radio_station_font = ImageFont.load_default()
    
    try:
        # Tags font - small monospace style
        tags_font = ImageFont.truetype(os.path.join("assets","DarkerGrotesque-ExtraBold.ttf"), 42)
    except (OSError, IOError):
        tags_font = ImageFont.load_default()
    
    # Get image dimensions
    width, height = image.size
    
    # Draw frequency at top-left with reduced letter spacing
    frequency_text = f"{frequency} FM"
    frequency_pos = (66, 311)
    frequency_color = (255, 255, 255, 255)
    #do it with a function
    draw_text_with_tracking(draw, frequency_pos, frequency_text, frequency_font, frequency_color, tracking=-8)

    # Draw scene genre and pill next to each other
    scene_genre_text = f"{scene_genre} dans"
    scene_genre_pos = (66, 460)
    scene_genre_color = (0, 0, 0, 255)
    # Draw scene genre text
    draw.text(scene_genre_pos, scene_genre_text, fill=scene_genre_color, font=scene_genre_font)

    # Draw scene name in a pill to the right of the genre using helper (all logic encapsulated)
    scene_name_color = (31, 41, 55, 255)
    if scene_name.lower() == "l'atrium":
        pill_bg_color = (255, 134, 53, 255)
    elif scene_name.lower() == "le refuge":
        pill_bg_color = (182, 140, 254, 220)
    else:
        pill_bg_color = (255, 255, 255, 220)
    # You can adjust offset here, e.g. (0, -10) to move pill up by 10px
    pill_offset = (0, 30)  # (x, y)
    draw_pill(
        draw=draw,
        text=scene_name,
        font=scene_name_font,
        text_fill=scene_name_color,
        pill_fill=pill_bg_color,
        relative_to=scene_genre_pos,
        relative_to_text=scene_genre_text,
        relative_to_font=scene_genre_font,
        gap=24,
        offset=pill_offset,
        padding_x=30,
        padding_y=15
    )

    date_pos = (66, 520)
    date_color = (0, 0, 0, 255)
    date_text = "le 31 juillet à La Rotonde"
    draw.text(date_pos, date_text, fill=date_color, font=date_font)

    # Draw radio station name at bottom-left with wrapping using helper
    radio_station_pos = (66, 800)
    radio_station_color = (255, 255, 255, 255)
    max_radio_width = width -200
    draw_wrapped_text(
        draw=draw,
        text=radio_station_name,
        font=radio_station_font,
        fill=radio_station_color,
        pos=radio_station_pos,
        max_width=max_radio_width,
        line_spacing=8,
        tracking=-8
    )
    
    # Draw tags in 3 lines of pills: (1&2), (3&4), (5). Pills 2 and 3 are colored, others are white.
    if tags and len(tags) == 5:
        pill_start_x = 66
        pill_start_y = 1300
        pill_gap_y = 24  # vertical gap between lines
        pill_gap_x = 24  # horizontal gap between pills in a line
        pill_text_fill = (31, 41, 55, 255)
        # Color for colored pills (2 and 3)
        if scene_name.lower() == "l'atrium":
            colored_pill_bg = (255, 134, 53, 255)
        elif scene_name.lower() == "le refuge":
            colored_pill_bg = (182, 140, 254, 220)
        else:
            colored_pill_bg = (255, 255, 255, 220)
        white_pill_bg = (255, 255, 255, 220)
        max_pill_right = width-66  # don't overflow right margin

        # Define lines: [(tag indices)]
        lines = [ [0,1], [2,3], [4] ]
        pill_idx = 0
        for line_num, tag_indices in enumerate(lines):
            x = pill_start_x
            y = pill_start_y + line_num * (tags_font.size + 2 * 15 + pill_gap_y)
            if len(tag_indices) == 2:
                # Two pills: try to fit both at full length, only truncate if needed, allow short pill to use less space
                available_width = max_pill_right - pill_start_x
                tag0 = tags[tag_indices[0]]
                tag1 = tags[tag_indices[1]]
                pill_bg0 = colored_pill_bg if pill_idx == 1 or pill_idx == 2 else white_pill_bg
                pill_bg1 = colored_pill_bg if pill_idx+1 == 1 or pill_idx+1 == 2 else white_pill_bg
                display_tag0 = tag0
                display_tag1 = tag1
                def pill_w(text):
                    bbox = tags_font.getbbox(text)
                    return (bbox[2] - bbox[0]) + 2*30
                # Try to fit both at full length
                while True:
                    w0 = pill_w(display_tag0)
                    w1 = pill_w(display_tag1)
                    total = w0 + pill_gap_x + w1
                    if total <= available_width:
                        break
                    # If both are too long, truncate the longer one
                    if w0 >= w1 and len(display_tag0) > 3:
                        display_tag0 = display_tag0[:-1]
                        if len(display_tag0) > 3:
                            display_tag0 = display_tag0[:-3] + '...'
                    elif len(display_tag1) > 3:
                        display_tag1 = display_tag1[:-1]
                        if len(display_tag1) > 3:
                            display_tag1 = display_tag1[:-3] + '...'
                    else:
                        break
                # Draw both pills side by side
                pill_x = x
                pill_bbox0 = draw_pill(
                    draw=draw,
                    text=display_tag0,
                    font=tags_font,
                    text_fill=pill_text_fill,
                    pill_fill=pill_bg0,
                    pos=(pill_x, y),
                    padding_x=30,
                    padding_y=15
                )
                pill_x = pill_bbox0[2] + pill_gap_x
                pill_bbox1 = draw_pill(
                    draw=draw,
                    text=display_tag1,
                    font=tags_font,
                    text_fill=pill_text_fill,
                    pill_fill=pill_bg1,
                    pos=(pill_x, y),
                    padding_x=30,
                    padding_y=15
                )
                pill_idx += 2
            else:
                # Single pill (last line)
                tag_i = tag_indices[0]
                tag = tags[tag_i]
                pill_bg = colored_pill_bg if pill_idx == 1 or pill_idx == 2 else white_pill_bg
                max_pill_width = max_pill_right - x
                display_tag = tag
                while True:
                    text_bbox = tags_font.getbbox(display_tag)
                    text_width = text_bbox[2] - text_bbox[0]
                    pill_width = text_width + 2 * 30
                    if pill_width <= max_pill_width or len(display_tag) <= 3:
                        break
                    display_tag = display_tag[:-1]
                    if len(display_tag) > 3:
                        display_tag = display_tag[:-3] + '...'
                pill_bbox = draw_pill(
                    draw=draw,
                    text=display_tag,
                    font=tags_font,
                    text_fill=pill_text_fill,
                    pill_fill=pill_bg,
                    pos=(x, y),
                    padding_x=30,
                    padding_y=15
                )
                pill_idx += 1
    
    # Determine output path
    if output_path is None:
        scene_safe_name = scene_name.lower().replace("'", "").replace(" ", "_")
        output_path = f"output_{scene_safe_name}.png"
    
    # Save the image
    image.save(output_path)
    
    return output_path


# Example usage
if __name__ == "__main__":
    # Example for L'Atrium (orange background)
    output1 = generate_freq_image(
        frequency="97.3",
        scene_genre="House solaire",
        scene_name="L'Atrium",
        radio_station_name="House solaire et organique",
        tags=[
            "Open-air au coucher du soleil", 
            "Flottant et groovy", 
            "Danser ensemble", 
            "Une basse funky",
            "Dom Dolla, The Blessed Madonna, X-coast, Ollie Lishman"]
    )
    print(f"Generated: {output1}")
    
    # Example for Le Refuge (purple background)
    output2 = generate_freq_image(
        frequency="108.9",
        scene_genre="Techno sombre",
        scene_name="Le Refuge",
        radio_station_name="Techno hypnotique et mentale",
        tags=[
            "Un club sombre", 
            "Il faut que je me dépense", 
            "Me perdre dans la masse",
            "Un kick sec et rapide",
            "I Hate Models, Clara Cuvé, Reiner Zonneveld, Rebekah, Un artiste en overflow"]
    )
    print(f"Generated: {output2}")

