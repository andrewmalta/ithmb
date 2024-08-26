import numpy as np
from PIL import Image
import os
import sys

def normalize_value(val):
    return val - 128
    
def get_rgb(chunk_data, offset, even):
    four_bytes = int.from_bytes(chunk_data[offset:offset+4], byteorder='big')
    y2 = four_bytes & 0xFF
    v =  (four_bytes >> 8) & 0xFF
    y1 = (four_bytes >> 16) & 0xFF
    u = (four_bytes >> 24) & 0xFF

    if (even):
        return yuv_to_rgb(normalize_value(y1) , normalize_value(u), normalize_value(v))
    else:
        return yuv_to_rgb(normalize_value(y2) , normalize_value(u), normalize_value(v))

def yuv_to_rgb(y, u, v):
    r = y + 1.3983 * v
    g = y - 0.39465 * u - 0.5806 * v
    b = y + 2.03211 * u
    
    # Clamp values to the range [0, 255]
    r = int(min(max(0, r + 128), 255))
    g = int(min(max(0, g + 128), 255))
    b = int(min(max(0, b + 128), 255))
    
    return r, g, b

def process_chunk_yuv_interlaced_shared_chromiance(chunk_data, width, height):
    rgb_data = rgb_data = np.zeros((height, width, 3), dtype=np.uint8)

    # Number of pixels
    num_pixels = width * height

    for y in range(height):
        y_over_2 = y // 2
        y_minus_1_over_2 = (y - 1) // 2
        for x in range(width):
            x_times_2 = x * 2
            x_minus_1_times_2 = (x - 1) * 2

            r = 0
            g = 0
            b = 0
            if y % 2 == 0:
                if x % 2 == 0:
                    offset = int(y_over_2 * width * 2 + x_times_2)
                    r, g, b = get_rgb(chunk_data, offset, True)
                else:
                    offset =  int(y_over_2 * width * 2 + x_minus_1_times_2)
                    r, g, b = get_rgb(chunk_data, offset, False)
            else:
                if x % 2 == 0:
                    offset = int(num_pixels + y_minus_1_over_2 * 2 * width + x_times_2)
                    r, g, b = get_rgb(chunk_data, offset, True)
                else:
                    offset = int(num_pixels + y_minus_1_over_2 * 2 * width + x_minus_1_times_2)
                    r, g, b = get_rgb(chunk_data, offset, False)            

            rgb_data[y, x] = r, g, b

    return rgb_data


def convertCLToRGBColor(chromiance, luminance):
    y = luminance
    u = (chromiance >> 4 & 0xF) * 16
    v = (chromiance & 0xF) * 16

    return yuv_to_rgb(normalize_value(y), normalize_value(u), normalize_value(v))


def process_chunk_yuv_plain(chunk_data, width, height):
    rgb_data = rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            offset = int(y * width * 2 + 2 * x)
            low_byte = int.from_bytes(chunk_data[offset:offset+1], byteorder='big')
            high_byte = int.from_bytes(chunk_data[offset+1:offset+2], byteorder='big')
            r, g, b = convertCLToRGBColor(low_byte, high_byte)
            rgb_data[y, x] = r, g, b

    return rgb_data

'''RGBColor rgb;
    unsigned char red, green, blue;
    
    red =   (highByte >> 3) & 31/*0b00011111*/;
    green = ((highByte << 3) & 56/*0b00111000*/) | ((lowByte >> 5) & 7/*0b00000111*/);
    blue =  lowByte & 31/*0b00011111*/;
    
    rgb.red = red * 2048;
    rgb.green = green * 1024;
    rgb.blue = blue * 2048;
    
    return rgb;'''

def convert_two_byte_rgb_to_rgb_color(high_byte, low_byte):
    r = (high_byte >> 3) & 0x1F
    g = ((high_byte >> 3) & 0x38) | ((low_byte >> 5) & 0x7)
    b = low_byte & 0x1F

    return (r * 8, g * 8, b * 8)


def process_file_16_bit_rgb(chunk_data, width, height):
    rgb_data = rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            offset = y * width * 2 + 2 * x
            low_byte = int.from_bytes(chunk_data[offset:offset+1], byteorder='big')
            high_byte = int.from_bytes(chunk_data[offset+1:offset+2], byteorder='big')
            r,g,b = convert_two_byte_rgb_to_rgb_color(high_byte, low_byte)
            rgb_data[y, x] = r, g, b

    return rgb_data


def process_file(input_file, output_dir):
    input_file_prefix =  os.path.basename(input_file).split(".")[0].split("_")[0][1:]

    dimension_mapping = {
        "1015": (130, 88, process_file_16_bit_rgb),
        "1019": (720, 480, process_chunk_yuv_interlaced_shared_chromiance),
        "1024": (320, 240, process_file_16_bit_rgb),
        "1036": (50, 41, process_chunk_yuv_plain)
    }

    if not input_file_prefix in dimension_mapping:
        print("Invalid file input format")
        return

    width, height, processing_function = dimension_mapping[input_file_prefix]

    os.makedirs(output_dir, exist_ok=True)
    with open(input_file, 'rb') as f:
        total_bytes = width * height * 2 # two bytes per pixel

        chunk_number = 1
        while True:
            chunk_data = f.read(total_bytes)
            if not chunk_data:
                break  # End of file
            
            # Process the image data
            rgb = processing_function(chunk_data, width, height)
            
            # Save the image as PNG
            output_file = os.path.join(output_dir, f"output_image_{chunk_number}.png")
            img = Image.fromarray(rgb)
            img.save(output_file)
            
            print(f"Saved {output_file}")
            chunk_number += 1


if __name__ == "__main__":
    output_dir = 'output_images'

    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print(len(sys.argv))
        print("./ithmb.py [input file path] [output directory name]")
        sys.exit(1)
    else:
        input_file = sys.argv[1]
        if len(sys.argv) == 3:
            output_dir = sys.argv[2]

    process_file(input_file, output_dir)
