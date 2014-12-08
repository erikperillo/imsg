#!/usr/bin/env python

#imsg - read/write messages to/from images
#by Erik Perillo

VERSION = "1.5.1"

import cv2
import sys
import numpy as np
from random import sample

CHRLEN       = 8
MAXVAL       = 255
EOT          = unichr(4)

#command line args parser - DEAL WITH IT
class Clarg:
     
     def __init__(self,name,defval,description,nargs=1):
          self.name        = name
          self.defval      = defval
          self.description = description
          self.nargs       = nargs

     def describe(self,showdefval=False):
          string = "\t%s \t \t %s" % (self.name,self.description)
          
          if showdefval:
               string += " (default value: " + str(self.defval) + ")"

          print string
               
class Container:
     
     def __init__(self):
          self.argv     = sys.argv
          self.clargs   = []
          self.readargs = 0

     def parse(self,clarg):
          self.clargs.append(clarg)
          res = []          

          for i in range(len(self.argv)):
               if self.argv[i] == clarg.name:
                    self.readargs += 1
                    if len(self.argv)-i <= clarg.nargs:
                         break
                    if clarg.nargs == 0:
                         return True
                    if clarg.nargs > 1:
                         for i in range(i+1,i+1+clarg.nargs):
                              res.append(self.argv[i]) 
                         return tuple(res)
                    return self.argv[i+1]
          return clarg.defval

     def describe(self,showdefval=False):
          for clarg in self.clargs:
               clarg.describe(showdefval)

     def help(self,showdefval=False):
          for arg in self.argv:
               if arg == "--help" or arg == "-help" or arg == "-h":
                    print "Avaliable options are:"
                    self.describe(showdefval)
                    exit() 

#displays error and exits
def error(msg="error"):
     print "imsg: error:",msg
     exit()

#gets positions for chars to be written
def Position(array):
     shift = 0
     maxx  = max(array) + 1

     while True:
          for elem in array:
               yield elem + shift
          shift += maxx

#opens and reads key from filename
def getKey(filename):
     try:
          flie = open(filename,"r")
     except IOError:
          return None

     key  = tuple(int(word) for line in flie for word in line.lower().split())
     if len(key) == 0:
          return None

     flie.close()
     return key

#saves key to filename
def saveKey(filename,key):
     flie = open(filename,"w")

     for k in key:
          flie.write(str(k)+" ")

     flie.close()

#returns random key 
def getRandKey(string,src):
     return tuple(sample(range(len(src)/CHRLEN),len(string)+1))

#gets extension of filename
def getExt(string):
     for i in range(len(string)):
          if string[i] == ".":
               return string[i:]
     return ""

#changes extension of filename
def setExt(string,ext):
     ret = string
     for i in range(len(string)):
          if(string[i] == "."):
               ret = string[:i]
     return ret + "." + ext

#splits file into its path and filename
def fileSplit(string):
     directory = ""
     flie = string
     for i in range(len(string)):
          if string[i] == "/":
               directory = string[:i]
               flie = string[(i+1):]
     return directory,flie

#checks if message fits into source array
def pairCheck(src,string,key):
     flag   = "OK" 
     ret    = string

     rest   = (len(string)+1) % len(key) 
     if rest != 0:
          rest = max(key[:(len(string)+1)%len(key)])

     if len(src)/CHRLEN < ((len(string)+1)/len(key))*max(key) + rest:
          return "ERR_LEN", None

     for i in range(len(ret)):
          if ord(ret[i]) >= 2**CHRLEN or ord(ret[i]) < 0:
               flag = "ERR_CHAR"
               ret = ret.replace(ret[i],u"?")

     return flag, ret

#writes a char to array
def writeChar(src,char):
     binchr = bin(char)[2:(CHRLEN+2)].zfill(CHRLEN)

     for i in range(CHRLEN):
          if (binchr[i] == "1" and src[i]%2 == 0) or (binchr[i] == "0" and src[i]%2 == 1):
               if src[i] >= MAXVAL:
                    src[i] -= 1
               else:
                    src[i] += 1

#writes a string to array
def writeString(src,string,key=(0,)):
     posit   = Position(key)
     string += EOT

     for char in string:
          pos = posit.next()
          writeChar(src[pos*CHRLEN:(pos+1)*CHRLEN],ord(char))

#reads a char from array
def readChar(src):
     binstr = ""

     for elem in src:
          binstr += str(elem%2)
     return unichr(int(binstr,2))

#reads a string to array
def readString(src,key=(0,)):
     posit   = Position(key)
     message = u""

     for i in range(len(src)):
          pos  = posit.next()
          char = readChar(src[pos*CHRLEN:(pos+1)*CHRLEN])
          if char == EOT:
               return message
          message += char
           
#descriptors for command line args
input_fn_desc  = Clarg("-i","","Path to input image",1)
msg_desc       = Clarg("-m","","Message (in latin-1 chars) to be hidden",1)
msg_file_desc  = Clarg("-mf","","Path to message file to be hidden",1)
output_fn_desc = Clarg("-o","","Path to output image",1)
decrypt_desc   = Clarg("-d",False,"Decrypt a message in input image",0)
keypath_desc   = Clarg("-k","","Path to key",1)
randkey_desc   = Clarg("-rk",False,"Generate random key",0)
warnoff_desc   = Clarg("-wo",False,"Turn warnings off",0)
verbose_desc   = Clarg("-v",False,"Verbose level 1, show messages",0)
verbose2_desc  = Clarg("-v2",False,"Verbose level 2, show messages and display input image",0)
helpmsg_desc   = Clarg("-h",False,"This help message",0)

#container for commando line args
container = Container()

#reading args
input_fn   = str(container.parse(input_fn_desc))
msg        = unicode(str(container.parse(msg_desc)),"utf-8")
msg_file   = str(container.parse(msg_file_desc))
output_fn  = str(container.parse(output_fn_desc))
decrypt    = bool(container.parse(decrypt_desc))
keypath    = str(container.parse(keypath_desc))
randkey    = bool(container.parse(randkey_desc))
verbose    = bool(container.parse(verbose_desc))
verbose2   = bool(container.parse(verbose2_desc))
warnoff    = bool(container.parse(warnoff_desc))
helpmsg    = bool(container.parse(helpmsg_desc))

#help message
if helpmsg or container.readargs == 0:
     print "imsg: read/write messages to/from images - version",VERSION
     print "by Erik Perillo"
     print "Usage:"
     container.describe()
     exit()

#checking args:

#checking input filename
if input_fn == "":
     error("no input image filename specified")
#reading image
img = cv2.imread(input_fn)
if img is None:
     error("file could not be loaded")
#converting first plane of image to an array
src = np.array(img[:,:,0]).reshape(-1,)

#checking decrypt
if msg_file == "":
     if msg == "":
          decrypt = True
else:
     try:
          flie = open(msg_file,"r")
     except IOError:
          error("message file not found/could not be opened")
     msg = unicode(flie.read(),"utf-8")
     flie.close()

#checking output filename
if output_fn == "":
     output_fn = setExt(input_fn,"png")
else:
     if decrypt:
          error("invalid operation")
     if getExt(output_fn) != ".png":
          if not decrypt and not warnoff:
               print "imsg: warning: output image extension has been changed. it must be in .png"
          output_fn = setExt(output_fn,"png")

#checking key things
if randkey:
     key = getRandKey(msg,src)
     if verbose or verbose2:
          print "imsg: generated random key: ",key
else:
     if keypath == "":
          dri,flie = fileSplit(output_fn)
          key = getKey(dri + "." + setExt(flie,"key"))
          if key is None:
               key = (0,)
     else:
          key = getKey(keypath)
          if key is None:
               error("key file not found")

#checking validity of image/message
check,msg = pairCheck(src,msg,key)
if check == "ERR_LEN":
     if decrypt:
          error("imcompatible key")
     else:
          error("size of image not enough for writing whole message")
elif check == "ERR_CHAR" and not warnoff:
     print "imsg: warning: some characters where not in latin-1 and where replaced"

#displaying image
if verbose2:
     cv2.imshow("image",img)
     cv2.waitKey(0)

#doing required work 
if decrypt:
     print readString(src,key)
else:
     writeString(src,msg,key)
     img[:,:,0] = np.matrix(src).reshape(img.shape[0],img.shape[1])
     cv2.imwrite(output_fn,img,[cv2.IMWRITE_JPEG_QUALITY,100])
     if randkey:
          if keypath == "":
               dri,flie = fileSplit(output_fn)
               keypath = setExt(dri + "." + flie,"key")
          saveKey(keypath,key)
     if verbose or verbose2:
          print "imsg: written message: '",readString(src,key),"'"
          print "imsg: result saved as '",output_fn,"'"
          if keypath != "":
               print "imsg: key saved as '",keypath,"'" 
