import unittest

import conversion

document='''
<html>
 <head>
  <title>
   The Dormouse's story
  </title>
 </head>
 <body>
  <p class="title">
   <b>
    The Dormouse's story
   </b>
  </p>
  <p class="story">
   Once upon a time there were three little sisters; and their names were
   <a class="sister" href="http://example.com/elsie" id="link1">
    Elsie
   </a>
   ,
   <a class="sister" href="http://example.com/lacie" id="link2">
    Lacie
   </a>
   and
   <a class="sister" href="http://example.com/tillie" id="link3">
    Tillie
   </a>
   ;
and they lived at the bottom of a well.
  </p>
  <p class="story">
   ...
  </p>
 </body>
</html>
'''

class TestConversion(unittest.TestCase):
    def test_get_first_html_tag1(self):
        soup = conversion.soup_from_text(document)
        res = conversion.get_first_html_tag(soup)
        self.assertEqual(res,'html')

    def test_get_first_html_tag2(self):
        example = 'Some tagless non-html text ...'
        try:
            soup = conversion.soup_from_text(example)
            conversion.get_first_html_tag(soup)
        except conversion.BadHTML:
            res = True # caught an exception 
        self.assertEqual(res,True)

    def test_clear_blank_lines(self):
        soup = conversion.soup_from_text(document)
        print "orig:", len(soup)
        soup = conversion.clear_blank_lines(soup)
        print "cleared:", len(soup)
        self.assertEqual(len(soup), 1)
    def test_document_title_from_title(self):
        soup = conversion.soup_from_text(document)
        res = conversion.get_document_title(soup)
        self.assertEqual(res,'The Dormouses story')
    def test_document_title_from_text(self):
        soup = conversion.soup_from_text('''
      <html> <head> </head> <body>  <p>  <b>
    The 
    Dormouse's 
    story   </b>  </p> </body></html>
        ''')
        res = conversion.get_document_title(soup)
        self.assertEqual(res,'The_Dormouses_story')

if __name__ == '__main__':
    # I`m executing this file
    unittest.main()
