from pdf2image import convert_from_path
from pathlib import Path
import pdfplumber

#read text directly from digital pdfs
def extract_text_from_pdf(pdf_path:Path)->list:
    words_list=[]
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
             # tables with bbox + cell text
            for t in page.find_tables():
                all_tables.append({
                    "page": page_no,
                    "bbox": t.bbox,
                    "table": t.extract()   # ✅ list of rows, each row list of cells
                })
            words=page.extract_words() #returns list of dictionaries representing words and their positions
            if words:
                for w in words:
                    w["page"]=page_no
                words_list.extend(words)
    return words_list,all_tables 

def word_inside_any_table(word, tables_from_pdf, pad=2):
    wx0, wx1 = word["x0"], word["x1"]
    wtop, wbottom = word["top"], word["bottom"]
    wpage = word["page"]

    for tinfo in tables_from_pdf:
        if tinfo["page"] != wpage:
            continue  # ✅ only same page

        tx0, ttop, tx1, tbottom = tinfo["bbox"]
        # overlap check (not full inside)
        if not (
            wx1 < tx0 - pad or
            wx0 > tx1 + pad or
            wbottom < ttop - pad or
            wtop > tbottom + pad
        ):
            return True
    return False


#convert pdf to images page by page
def pdf_to_images(pdf_path:Path, output_folder:Path): 
    output_folder.mkdir(parents=True, exist_ok=True) # Create output folder if it doesn't exist
    
    # Convert PDF to images, each page as a separate image
    images = convert_from_path(str(pdf_path),dpi=300)
   
    # Save each image to the output folder
    image_paths = []
    
    for index, image in enumerate(images,start=1):  #enumerate to get page number, starting from 1
        image_path = output_folder / f"page_{index}.png" #compose image path
        image.save(image_path, 'PNG')                     #save image as PNG
        image_paths.append(image_path)                    #store image path
    
    #return list of image paths
    return image_paths