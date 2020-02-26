# conversion.py
'''
This is doc string for fp2rm conversion module
'''

from bs4 import BeautifulSoup, element
import sys
import argparse
import os.path
class BadHTML(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class WikiFromSoup:
    def __init__(self, soup, title, outfile):
        self.soup = clear_blank_lines(soup)
        self.title = title
        self.textile = ''
        self.outfile = outfile
    def addText(self, text):
        # encode as utf8 to avoid UnicodeEncodeError like this:
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\xa0' in position 27: ordinal not in range(128) 
        res = text.encode('utf-8')
        print "NR in addText adding:", res
        self.outText.append(res)
    def writeOutRedmine(self):
        ## Write this out 
        open("%s" % self.outfile, 'w').write(self.textile+"\n")

def soup_from_file(fname):
    fin = open(fname, mode='r')
    return BeautifulSoup(fin, 'html.parser')

def soup_from_text(txt):
    return BeautifulSoup(txt, 'html.parser')

def clear_blank_lines(doc):
    ''' Removes useless contents containing just blank lines 
from a BeautifulSoup top object (document)
If the argument passed to this function contains BeautifulSoup object,
clear contents are substituted in place; otherwise, unchanged document
is returned.'''
    if isinstance(doc, (BeautifulSoup, element.Tag)):
        clearsoup = [c for c in doc if c != u'\n']
        doc.contents = clearsoup
    return doc
    
def get_first_html_tag (doc):
    for c in doc.contents:
        if c.name:
            return c.name
    raise BadHTML(doc);

def get_document_title (doc):
    if isinstance(doc, BeautifulSoup):
        try:
            return doc.html.head.title
        except:
            print "could not find title tag"
            return None

def main(args):
    ap = argparse.ArgumentParser()
    ap.add_argument('-f', '--file', 
        help='File to load',
        default = '/users/natasha/DOCUMENTATION/contents/Operations/d/dba-team/internal/freeware/index.html')
    ap.add_argument('-o', '--outdir', 
        help='Where the results should go',
        default = '/tmp/fp2rm')
    opts = ap.parse_args(args)
    if opts.file:
        print "Converting file:  ", opts.file
        document = soup_from_file(opts.file)
        print "Document type:    ", get_first_html_tag (document)
        title = get_document_title(document)
        if not title:
            print "WARNING: Document has no title, using input file name"
            title = os.path.basename (opts.file)
        print "Document title:   ", title
        print "Output directory: ",  opts.outdir
        outfile = opts.outdir+'/' + title + '.redmine'
        print "Output file: ", outfile
        o = WikiFromSoup(document, title, outfile)
        o.writeOutRedmine()
        
if __name__ == '__main__':
    # python conversion.py -f index.html 
    main(sys.argv[1:])

else:
    print("this is a library")
    
