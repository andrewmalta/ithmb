# iPod Classic .ithmb File Reader

## Description

This script is for reading the `.ithmb` files that existed on my Grandpa's iPod classic into images. Huge thanks to Keith W. for doing the first reverse engineering of the file format. This Python file aims to make it easier for people to use Keith's work for decoding their own `.ithmb` files.

## Usage
./ithmb.py <input_ithmb_file_path> <output_directory_path>
Copy
The script will use the name of the input file to select the right way to decode the images, so don't modify the `.ithmb` file name before passing it to the script.

## Current State

- The ported algorithm for reading the highest resolution (720x480) from the `F1019_x.ithmb` files seems to be correct. I was able to salvage nearly 2000 lost family pictures, and they look good!

- I started down the road of figuring out how the `F1015_x.ithmb`, `F1024_x.ithmb`, `F1036_x.ithmb` can be decoded, and I think it's pretty close. I'm pretty sure I found the sizes of the images at least for 5th generation iPod Classic, and that they are likely stored as 2-Byte RGB images, but the colors still feel a bit wrong.

## Contribution

Would love a PR if you figure out the decoding for the other file types!

Hopefully, you find this helpful!