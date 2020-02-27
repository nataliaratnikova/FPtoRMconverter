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

###  Functions to get HTML document contents:

def soup_from_file(fname):
    fin = open(fname, mode='r')
    return BeautifulSoup(fin, 'html.parser')

def soup_from_text(txt):
    return BeautifulSoup(txt, 'html.parser')

### Document manipulation functions

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
            print "Warning: document has no title\n Using first line of page text."
            for s in doc.body.contents:
                if s.string.strip():
                    return s.string.strip()
            return None

### Tag parsing functions adopted from Adam Lyon

def parseTag(tagElement, o, offset):
  tag = tagElement.name
  print "NR in parseTag:", offset*"-" + tag

  ## Handle the tag!
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
  elif tag in ["p"]:
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
  for anAttr in tagElement.attrs:
    if anAttr[0] == 'name':
      ## Don't do anything with names yet!
      print offset*"-" + "ATTR:name"
      removeA = True
    elif anAttr[0] == "href":
      target = anAttr[1]
      if target.find("sortcol") >= 0:
        removeA = True
        continue
      ## Is it an attachment?
      if target.find("/cgi-bin/twiki/bin/viewfile") >= 0:
        ## Get the part after "filename="
        fname = target.split("filename=")[1]
        o.addText(" attachment:%s " % fname)
        return
      ## Is it a pub attachment
      if target.find("/pub/"+o.area+"/"+o.page) >= 0:
        ## Get the last part
        fname = target.split("/")[-1]
        o.addText(" attachment:%s " % fname)
        return
      if target.find("/cgi-bin/twiki/bin/view/") >= 0:
        ## It's a Wiki target
        isWikiTarget = True
        targetParts = target.split("/")
        wikiTarget = targetParts[-1]
        o.addText(" [[%s|" % wikiTarget)
        o.addWikiLink(targetParts[-2],targetParts[-1])
      else:
        o.addText(' "')
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
        default = '/users/natasha/DOCUMENTATION/contents/Operations/d/dba-team/internal/freeware/index.html')
    ap.add_argument('-o', '--outdir', 
        help='Where the results should go',
        default = '/tmp/fp2rm')
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
        # We normally want to parse document body:
        t = document.find('body')
        parseTag(t, o, 0)
        o.writeOutRedmine()
        
if __name__ == '__main__':
    # python conversion.py -f index.html 
    main(sys.argv[1:])
else:
    print("this is a library")
