# conversion.py
'''
This is doc string for fp2rm conversion module
'''

from bs4 import BeautifulSoup

class BadHTML(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def soup_from_file(fname):
    fin = open(fname, mode='r', encoding='utf8')
    return BeautifulSoup(fin, 'html.parser')

def soup_from_text(txt):
    return BeautifulSoup(txt, 'html.parser')

def clear_blank_lines(doc):
    ''' Removes useless contents containing just blank lines 
from a BeautifulSoup top object (document)
If the argument passed to this function contains BeautifulSoup object,
clear contents are substituted in place; otherwise, unchanged document
is returned.'''
    if isinstance(doc, BeautifulSoup):
        clearsoup = [c for c in doc if c != u'\n']
        doc.contents = clearsoup
    return doc
    
def get_first_html_tag (doc):
    for c in doc.contents:
        if c.name:
            return c.name
    raise BadHTML(doc);

def main(args):
    ap = argparse.ArgumentParser()
    ap.add_argument('-f', '--file', help='File to load')
    ap.add_argument('-f', '--file', help='File to load')
    opts = ap.parse_args(args)
    if opts.file:
        document = from_file(opts.file)
        get_first_html_tag (document)

if __name__ == '__main__':
    # you are executing this file
    # m = from_file('pp.txt', size=4)
    # repl(m)
    # python markov.py -f pp.txt -s 4
    main(sys.argv[1:])

else:
    print("this is a library")
    
