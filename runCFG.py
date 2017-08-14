#!/usr/bin/python

from Classes import *
from Rules import rules
import sys,getopt

#def values
prints = False
width = 5
reset = 5    

try:                                
    opts, args = getopt.getopt(sys.argv[1:], "n:l:w:p:")
except getopt.GetoptError:          
    print('Not valid options. Please specify at least -n.')    
    sys.exit(2) 
for opt, arg in opts:
    if opt == '-n':      
            name = arg
    try:
        if opt == '-l' and isinstance(arg, int):      
            reset = arg
    except:
        print('Not valid reset number integer given.')  
        sys.exit(2) 
    try:
        if opt == '-w' and isinstance(arg, int):      
            width = arg
    except:
        print('Not valid width limit integer given.')   
        sys.exit(2) 
    try:
        if opt == '-p' and isinstance(arg, bool):      
            prints = arg
    except:
        print('Not valid print command. Please specify True or False.') 
        sys.exit(2) 
            
if prints:
    print('Creating fingerings tree for file {0} with width limit {1}, resetting every {2} notes and printing the output'.format(name, width, reset))
else:
    print('Creating fingerings tree for file {0} with width limit {1}, resetting every {2} notes without printing the output'.format(name, width, reset))
tree = NoteTree(name, rules, width, reset, prints)