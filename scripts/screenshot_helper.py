import os
import re
from PIL import Image, ImageDraw, ImageFont

def render_terminal(
    command_str: str,
    output_lines: list[str],
    output_png_path: str,
    title: str = "MINGW64:/c/Users/PC/Downloads/serverless-rota-vital/serverless-rota-vital",
    exit_code: int = 0
):
    font_path = "C:/Windows/Fonts/consola.ttf"
    font_bold_path = "C:/Windows/Fonts/consolab.ttf"
    
    font_size = 14
    line_height = 20
    font = ImageFont.truetype(font_path, font_size)
    font_bold = ImageFont.truetype(font_bold_path, font_size)
    font_title = ImageFont.truetype(font_path, 12)
    
    # Process text lines
    all_lines = []
    # Prompt line
    all_lines.append(("prompt", f"$ {command_str}"))
    
    # Output lines
    for line in output_lines:
        line_clean = line.rstrip("\r\n")
        all_lines.append(("normal", line_clean))
        
    # Calculate dimensions
    max_line_len = max(len(l[1]) for l in all_lines)
    max_line_len = max(max_line_len, 70)
    width = int(max(850, min(1400, max_line_len * 8.6 + 60)))
    header_height = 36
    padding_y = 15
    height = header_height + padding_y * 2 + len(all_lines) * line_height + 15
    
    # Colors
    bg_color = (24, 24, 24)
    header_bg = (34, 34, 34)
    border_color = (60, 60, 60)
    text_color = (220, 220, 220)
    prompt_color = (80, 250, 123)  # Bright green
    cyan_color = (139, 233, 253)
    yellow_color = (241, 250, 140)
    red_color = (255, 85, 85)
    gray_color = (120, 120, 120)
    
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Header bar
    draw.rectangle([(0, 0), (width, header_height)], fill=header_bg)
    draw.line([(0, header_height), (width, header_height)], fill=border_color, width=1)
    
    # Window buttons
    draw.ellipse([(14, 12), (26, 24)], fill=(255, 95, 86))
    draw.ellipse([(34, 12), (46, 24)], fill=(255, 189, 46))
    draw.ellipse([(54, 12), (66, 24)], fill=(39, 201, 63))
    
    # Window title
    draw.text((80, 10), title, font=font_title, fill=(160, 160, 160))
    
    # Draw lines
    y = header_height + padding_y
    for kind, text in all_lines:
        if kind == "prompt":
            draw.text((25, y), "$ ", font=font_bold, fill=prompt_color)
            draw.text((45, y), text[2:], font=font_bold, fill=(255, 255, 255))
        else:
            # Simple syntax highlighting based on content
            color = text_color
            cur_font = font
            if "Build Succeeded" in text or "StatusCode: 201" in text or "201" in text and "POST" in text:
                color = prompt_color
                cur_font = font_bold
            elif "Error" in text or "Exception" in text or "502" in text or "Timed out" in text or "Task timed out" in text:
                color = red_color
                cur_font = font_bold
            elif "Building codeuri" in text or "Commands you can use next" in text or "Mounting" in text:
                color = cyan_color
            elif "START" in text or "END" in text or "REPORT" in text or "Duration:" in text:
                color = yellow_color
            elif text.startswith("[*]") or text.startswith("=="):
                color = cyan_color
                cur_font = font_bold
            elif text.startswith("{\"") or text.startswith("{"):
                color = (248, 248, 242)
                
            draw.text((25, y), text, font=cur_font, fill=color)
        y += line_height
        
    # Draw border around window
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=border_color, width=1)
    
    os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
    img.save(output_png_path, "PNG")
    print(f"Salvo: {output_png_path} ({width}x{height})")

if __name__ == "__main__":
    test_out = [
        "Building codeuri: C:\\Users\\PC\\Downloads\\serverless-rota-vital\\hello_world runtime: python3.12 architecture: x86_64 functions: GuiaFunction",
        " Running PythonPipBuilder:ResolveDependencies",
        " Running PythonPipBuilder:CopySource",
        "",
        "Build Succeeded",
        "",
        "Built Artifacts  : .aws-sam\\build",
        "Built Template   : .aws-sam\\build\\template.yaml",
        "",
        "Commands you can use next",
        "=========================",
        "[*] Validate SAM template: sam validate",
        "[*] Invoke Function: sam local invoke",
        "[*] Test Function in the Cloud: sam sync --stack-name {{stack-name}} --watch",
        "[*] Deploy: sam deploy --guided"
    ]
    render_terminal(
        "sam build",
        test_out,
        "c:/Users/PC/Downloads/serverless-rota-vital/serverless-rota-vital/evidencias/01-sam-build.png"
    )
