from pdf2image import convert_from_path
from pathlib import Path

#convert pdf to images page by page
def pdf_to_images(pdf_path:Path, output_folder:Path): 
    output_folder.mkdir(parents=True, exist_ok=True) # Create output folder if it doesn't exist
    
    # Convert PDF to images, each page as a separate image
    images = convert_from_path(pdf_path,dpi=300)
   
    # Save each image to the output folder
    image_paths = []
    
    for index, image in enumerate(images,start=1):  #enumerate to get page number, starting from 1
        image_path = output_folder / f"page_{index}.png" #compose image path
        image.save(image_path, 'PNG')                     #save image as PNG
        image_paths.append(image_path)                    #store image path
    
    #return list of image paths
    return image_paths