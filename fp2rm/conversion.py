# conversion.py
'''
This is doc string for fp2rm conversion module
'''

from bs4 import BeautifulSoup, element
import sys
import argparse
import os.path
import os
import string

class BadHTML(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class WikiFromSoup:
    def __init__(self, soup, title, outfile):
        self.soup = clear_blank_lines(soup)
        self.title = title
        self.textile = []
        self.outfile = outfile
        self.isUlStack = []
        self.liOffset = -2
    def addText(self, text):
        # encode as utf8 to avoid UnicodeEncodeError like this:
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\xa0' in position 27: ordinal not in range(128) 
        res = text.encode('utf-8')
        print "NR in addText adding: \""+res+"\""
        self.textile.append(res)
    def writeOutRedmine(self):
        ## Write this out 
        text = string.join(self.textile, "")
        open("%s" % self.outfile, 'w').write(text+"\n")
    def set_docpath(self, path):
        self.docpath = path

###  Functions to get HTML document contents:

def soup_from_file(fname):
    fin = open(fname, mode='r')
    return BeautifulSoup(fin, 'html.parser')

def soup_from_text(txt):
    return BeautifulSoup(txt, 'html.parser')

### Document manipulation functions

def clean_new_lines_from_text(txt):
    '''removes all new lines and single quotes from a text, 
can be easily extended to remove more special characters'''
    txt=txt.strip()
    return string.join([ c for c in txt if c not in ( u'\n', '\'')],'')

def replace_by_hr(txt):
    # Use markup horizontal rule for lines consisting of 3 or more equal signs
    if len (txt.strip()) >= 3:
        check = [ c for c in txt.strip() if c != '=' ]
        if not check:
            return '\n\n---\n\n'
    return txt

def plain_text(txt):
    '''removes repeated whitespaces, new lines from text'''
    # Remove also MS windows left-overs (carriage return)
    txt   = txt.replace('\r', ' ').replace('\n', ' ').strip()
    clist = [c for c in txt if c != "\'"]
    result=[]
    previous=''
    for c in clist:
        if c == ' ' and previous == ' ':
            continue
        result.append(c)
        previous = c 
    return string.join(result, '')

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
    '''Takes beautiful soup document as an argument. If found, returns title tag specified 
in the head section; otherwise takes first nonempty text from the closest document tag. 
Converts text to a plain string using underscores as word breaks'''
    if isinstance(doc, BeautifulSoup):
        try:
            return clean_new_lines_from_text(doc.html.head.title.string.strip())
        except:
            print "Warning: document has no title\n Using first line of page text."
            for tag in doc.html.body.find_all():
                #res = clean_new_lines_from_text(tag.get_text()).strip()
                res = plain_text(tag.get_text())
                if res:
                    return res.replace(' ','_')
    else:
        print "ERROR: document must be a BeautifulSoup object! type: ", type(doc)
### Tag parsing functions adopted from Adam Lyon

def parseTag(tagElement, o, offset):
  tag = tagElement.name
  print "NR in parseTag:", offset*"-" + tag

  ## Handle the tag!
  if tag == "hr":
    o.addText('\n\n---\n')
  if tag == "a":
    parseA(tagElement, o, offset)
  elif tag in ["h1", "h2", "h3", "h4", "h5"]:
    parseTextOut(tagElement, o, offset, "%s. " % tag, "\n\n")
  elif tag in ["b", "strong"]:
    o.addText('*%s*' % tagElement.get_text().strip())
    #parseTextOut(tagElement, o, offset, "*", "*")
  elif tag in ["code", "tt"]:
    parseTextOut(tagElement, o, offset, " @", "@ ")
  elif tag == "pre":
    parseTextOut(tagElement, o, offset, "\n\n"+o.liOffset*" "+"<pre>\n", "\n"+" "*o.liOffset+"</pre>\n\n")
  elif tag in ["p", "dl"]:
    # Since definition list has  no text, treat it as a new paragraph
    parseTextOut(tagElement, o, offset, "\n\n", "")
  elif tag in ["br"]:
    parseTextOut(tagElement, o, offset, "\n", "")
  elif tag == "li":
    parseListElement(tagElement, o, offset)
  elif tag in ["ul", "ol"]:
    parseList(tagElement, o, offset)
  elif tag == 'table':
    parseTable(tagElement, o, offset)
  elif tag in ['tr']:
    parseTableRow(tagElement, o, offset)
  elif tag in ['td', 'th']:
    parseTableCell(tagElement, o, offset)
  else:
    parseOther(tagElement, o, offset)

def parseOther(tagElement, o, offset):
  ## Don't actually do anything to the output here
  print offset*"-" + "OTHER:"+tagElement.name+":open"
  for anAttr in tagElement.attrs:
    print offset*"-" + "OTHER:" + str(anAttr)

  o.addText("")

  ## Do we have any contents?
  if tagElement.contents:
    parseContents(tagElement.contents, o, offset+2)

  # We're back from contents!
  print offset*"-" + "OTHER:"+tagElement.name+":close"

  o.addText("")

def parseContents(contents, o, offset):
  #print "NR in parseContents"
  for c in contents:
    ## Is this a comment?
    if isinstance(c, element.Comment):
      ## Don't do comments
      print "Skipping a comment: ", c.string
      continue
    ## If it's a string, let's see what we do
    if isinstance(c, element.NavigableString):
      s = c.strip()
      print offset*"-" + 'text: %s' % s
      s = replace_by_hr(s)
      o.addText(s)
    if isinstance(c, element.Tag):
      ## It's a tag! Parse it
      parseTag(c, o, offset)

def parseTextOut(tagElement, o, offset, begin, end):

  print offset*" " + tagElement.name + ":open"

  o.addText(begin)

  if tagElement.contents:
    parseContents(tagElement.contents, o, offset+2)

  o.addText(end)

  print offset*" " + tagElement.name + ":close"

def parseList(tagElement, o, offset):
  print offset*" " + tagElement.name + ":open"
  o.addText("\n\n")
  if tagElement.name == "ul":
    o.isUlStack.append(True)
  else:
    o.isUlStack.append(False)
  o.liOffset += 2
  if tagElement.contents:
    parseContents(tagElement.contents, o, offset+2)
  o.liOffset -= 2
  o.isUlStack.pop()
  print offset*" " + tagElement.name + ":close"

def parseListElement(tagElement, o, offset):
  print offset*" " + tagElement.name + ":open"
  h = "#"
  if o.isUlStack[ -1 ]:
    h = "*"
  o.addText(" "*o.liOffset + "* ")
  if tagElement.contents:
    parseContents(tagElement.contents, o, offset+2)
  o.addText("\n\n")
  print offset*" " + tagElement.name + ":close"

def parseA(tagElement, o, offset):
  print offset*"-" + 'A:open'
  removeA = False
  isWikiTarget = False
  ## NR: in bs4 attrs is a dict
  for anAttr in tagElement.attrs.keys():
    if anAttr == 'name':
      ## Don't do anything with names yet!
      print offset*"-" + "ATTR:name"
      removeA = True
    elif anAttr == "href":
      target = tagElement.attrs[anAttr]
      print "NR in parseA, target: \'%s\'" % target
      # if it is an internal document, prepend with a path to a local file
      # and let the browser serve it accordingly
      if target[:4] == 'http':
        print "NR: link to external document, as target starts with http."
        #o.addText(' "%s":%s ' % (clean_new_lines_from_text(tagElement.get_text().strip()),target))
        o.addText(' "%s":%s ' % (plain_text(tagElement.get_text()),target))
        return
      else:
        print "NR: this is a link to internal document, using local file path"
        o.addText(' "%s":%s ' % (plain_text(tagElement.get_text()),os.path.join(o.docpath,target)))
        return
    else:
      print "NR in parseA: FIXME "
      sys.exit(1)
  ## Do we have any contents?
  if tagElement.contents:
    parseContents(tagElement.contents, o, offset+2)
  ## Add the end part
  if not removeA:
    if isWikiTarget:
      o.addText("]] ")
    else:
      target = "NR target test"
      o.addText('":%s ' % target)
  ## We're back from contents!
  print offset*"-" + "A:close"

### Main

def main(args):
    ap = argparse.ArgumentParser()
    ap.add_argument('-f', '--file', 
        help='File to load',
        default = './index.html')
    ap.add_argument('-o', '--outdir', 
        help='Where the results should go',
        default = '/tmp/fp2rm')
    ap.add_argument('-d', '--docpath', 
        help='Path do local documents to substitute in reference links',
        default = '/tmp/fp2rm/Documents')
    opts = ap.parse_args(args)
    if opts.outdir:
        try:
            os.mkdir(opts.outdir)
        except OSError:
            print ("Creation of the directory %s failed" % opts.outdir)
        else:
            print ("Successfully created the directory %s " % opts.outdir)
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
        o.set_docpath('file://' + opts.docpath)
        # We normally want to parse document body:
        t = document.find('body')
        parseTag(t, o, 0)
        o.writeOutRedmine()
        
if __name__ == '__main__':
    # python conversion.py -f index.html 
    main(sys.argv[1:])
else:
    print("this is a library")
