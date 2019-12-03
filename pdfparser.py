
#!/usr/bin/env python
import sys
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter


def parse_pdf(fname, outfile):
    # input option
    password = b''
    pagenos = set()
    maxpages = 0
    # output option
    #outfile = fname + '.txt'
    outtype = 'text'
    imagewriter = None
    rotation = 0
    stripcontrol = False
    layoutmode = 'normal'
    encoding = 'utf-8'
    pageno = 0
    scale = 1
    caching = True
    showpageno = False
    laparams = LAParams()
    #
    rsrcmgr = PDFResourceManager(caching=caching)
    outfp = open(outfile, 'w', encoding=encoding)
    device = TextConverter(rsrcmgr, outfp, laparams=laparams,
                           imagewriter=imagewriter)

    with open(fname, 'rb') as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp, pagenos,
                                      maxpages=maxpages, password=password,
                                      caching=caching, check_extractable=True):
            page.rotate = (page.rotate+rotation) % 360
            interpreter.process_page(page)
    device.close()
    outfp.close()
    return
