import re as re
def soundex( name ):
   name_length = len(name)
   if name_length < 3 :
       return '0'*4
   name_in = name
   # truncate name to exclude any text in parenthesis
   if name[0] == '(' :
      name = name.split(')')[1]
   else:
      name = name.split('(')[0]
   # strip all punctuation characters
   name = re.sub('[^a-zA-Z]','',name)
   try:
      assert len(name) > 1
   except:
      print("'{}':'{}'".format(name_in, name))
   # now soundex
   letter1 = name[0]
   name = re.sub('[aeiouyhwAEIOUYHW]','0',name)
   name = re.sub('[bfpvBFPV]','1',name)
   name = re.sub('[cgjkqsxzCGJKQSXZ]','2',name)
   name = re.sub('[dtDT]','3',name)
   name = re.sub('[lL]','4',name)
   name = re.sub('[mnMN]','5',name)
   name = re.sub('[rR]','6',name)
   number1 = name[0]

   paired_numbers = ['11','22','33','44','55','66','77','88','99']
   for pn in paired_numbers:
      while pn in name :
         name = re.sub(pn, pn[0], name)
   name = re.sub( '0', '', name )
   name_length = len(name)
   if name_length < 4 :
       name = name + '0' * (4 - name_length)

   name_length = len(name)

   if number1 == name[0] :
      name = letter1 + name[1:name_length]
   else :
      name = letter1 + name
   return name

