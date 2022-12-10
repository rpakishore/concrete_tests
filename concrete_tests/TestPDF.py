import os

class TestPdf:
    def __init__(self, folderpath: str):
        self.folderpath = folderpath
    
    def __str__(self):
        return f"TestPdf module running on folder: {self.folderpath}"
    
    def __repr__(self):
        return f"TestPdf(folderpath=\"{self.folderpath}\")"

def get_pdf_from_folder(folderpath: str):
    """Returns a list of filepaths for all `.pdf` files found in the folder

    Args:
        folderpath (str): Folder path to look at

    Returns:
        list[str]: list of PDF files found
    """
    return [os.path.join(folderpath, file) for file in os.listdir(folderpath) if file.lower().endswith('.pdf')]