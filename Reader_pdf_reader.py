# importing required modules 
from PyPDF2 import PdfReader 


def pdfReadModullar( filename,x=50):
    
# creating a pdf reader object 
    reader = PdfReader(filename) 

# printing number of pages in pdf file 
    print(len(reader.pages)) 
  
# getting a specific page from the pdf file
# never ask for more pages than the document has
    text = ""
    for i in range(min(x, len(reader.pages))): # x is number of PDF pages
        page = reader.pages[i]
        # extracting text from page 
        text = text + page.extract_text() 
    
    return text 

    