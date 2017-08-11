import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString
from Options import *
from time import sleep
import gc
import os.path
import sys

# ============================= ============================= ============================= #
# ============================= ============================= ============================= #  
class Note(object):
    # ============================= ============================= #
    def __init__(self, pitch, octave, duration=None, x=None):
        self.pitch = pitch
        self.octave = octave
        self.me = str('{0}-{1}'.format(self.pitch,self.octave))
        self.fingers = None
        self.duration = duration
        self.x = x
    
    def setFingers(self, fingers):
        self.fingers = fingers
        
    def addFinger(self, finger):
        self.fingers.add(finger)
    
    def getPitch(self):
        return self.pitch
    
    def getOctave(self):
        return self.octave
    
    def getFingers(self):
        return self.fingers
    
    # show pitch, octave, possible fingerings
    def getNoteInfo(self):
        return ('Note {0} of octave {1} playable at fret-string-finger combination(s): {2}'.format(self.pitch,self.octave,self.fingers))

# ============================= ============================= ============================= # 
# ============================= ============================= ============================= #  
class Chord(object):
    # ============================= ============================= #
    def __init__(self, notes):
        self.notes = notes # list of notenodes 
        self.me = ','.join(str(note.me) for note in self.notes)
        
    def addNote(self, note):
        self.notes.append(note)
                 
    def getNotes(self):
        return self.notes
    
# ============================= ============================= ============================= #
# ============================= ============================= ============================= #           
class NoteNode(object):
    # ============================= ============================= #
    def __init__(self, notes, rules, isChord=False, finger=None, parent=None):
        self.rules = rules
        if isChord:
            # create nodes for each note in chord, get score and best fignering and keep it as a whole
            # find optimal path first and keep it
            chords = list()
            i = 0
            # initialise with first note
            if len(notes[0].fingers.split(','))>1:
                for finger in notes[0].fingers.split(','):
                    node = NoteNode(notes[0], rules, False, finger, parent)
                    node.resetScore()
                    chords.append(node)
            else:
                node = NoteNode(notes[0], rules, False, notes[0].fingers, parent)
                node.resetScore()
                chords.append(node)    
            for note in notes[1:]:
                c = 0
                for child in chords[-i:]:
                    ch_finger = int(str(child.finger).split(',')[-1])
                    if len(note.fingers.split(','))>1:
                        for finger in note.fingers.split(','):
                            if ((finger != ch_finger) or (ch_finger==0)):
                                node = NoteNode(note, rules, False, finger, child)
                                chords.append(node)
                                c += 1
                    else:
                        if ((note.fingers != ch_finger) or (ch_finger==0)):
                            node = NoteNode(note, rules, False, note.fingers, child)
                            chords.append(node)
                            c += 1
                i = c
            chords_leafs = chords[-i:]
            scores = {}
            for leaf in chords_leafs: #get the best possible path for the chord
                scores[leaf] = leaf.score
            best_path = list()
            start = min(scores, key=scores.get)
            best_pitch = ''
            best_fingers = ''
            for note in notes:
                while not start.equals(notes[0]): 
                    best_path.insert(0, start)
                    best_pitch = start.pitch + ',' + best_pitch
                    best_fingers = str(start.finger) + ',' + best_fingers
                    start = start.parent
            # last note 
            best_path.insert(0, start)
            best_pitch = start.pitch + ',' + best_pitch
            best_fingers = str(start.finger) + ',' + best_fingers
            
            # got best chord fingerings, now fill the rest 
            self.pitch = best_pitch[:-1]
            self.fret = chords_leafs[-1].fret
            self.string = chords_leafs[-1].string
            self.finger = best_fingers[:-1]
            self.children = list()
            self.octave = chords_leafs[-1].octave
            self.position = chords_leafs[-1].position
            if parent:
                self.parent = parent
                self.parent.addChild(self)
            else:
                self.parent = self
            self.score = chords_leafs[-1].score + self.parent.score
            self.me = str('{0}: (chord): {1}'.format(self.pitch, self.finger))

        else:
            self.vector = [0,0,0,0,0,0,0,0,0,0,0] # num of rules
            # normal node with 1 note
            self.pitch, self.fret, self.string, self.finger = self.analyze(notes, finger)
            self.score = 0
            self.octave = notes.getOctave()
            self.children = list()
            self.position = self.findPos()
            if parent:
                self.parent = parent
                self.parent.addChild(self)
            else:
                self.parent = self
            self.me = str('{0}-{1}: ({2}/{3}): {4}'.format(self.pitch, self.octave, self.fret, self.string, self.finger))
            self.score = self._score() + self.parent.score
            
    # ============================= ============================= #
    # Note format: (fret/string):finger
    def analyze(self,note,f):
        pitch = note.getPitch()
        if len(f)==7:
            fret = f[1]
            string = f[3]
            finger = f[6]
        else:
            fret = f[1:3]
            string = f[4]
            finger = f[7]
        return pitch, int(fret), int(string), int(finger)
    
    def findPos(self):
        if self.fret == 0:
            return 0
        if self.finger <= self.fret:
            return self.fret - self.finger +1
        else:
            return 1
    
    # ============================= ============================= #
    def _score(self):
        # calculate score
        # the bigger the score the worse the fingering
        #total = 0
        if self.position != self.parent.position: # penalize position change
            if self.position != 0:
                #total += 10
                self.vector[0] = 1
        if self.position == self.finger: # prioritize finger-position
            #total += -10
            self.vector[1] = 1
        if self.fret == 0: # prioritize 0
            #total += -20
            self.vector[2] = 1
        if self.finger == int(str(self.parent.finger).split(',')[-1]): # fingers should be different
            if self.finger != 0:
                #total += 10
                self.vector[3] = 1
        if self.finger < int(str(self.parent.finger).split(',')[-1]): # higher fingers first
            if self.parent.finger != 0:
                #total += -5
                self.vector[4] = 1
        if self.fret < 5: # prioritize smaller positions
            #total += -5
            self.vector[5] = 1
        if self.finger == 4: # penalize 4
            self.vector[6] = 1
        self.vector[7] = abs(self.position - self.parent.position)
        self.vector[8] = abs(self.fret - self.parent.fret)
        self.vector[9] = abs(self.string - self.parent.string)
        self.vector[10] = abs(self.finger - int(str(self.parent.finger).split(',')[-1]))    
        
        return sum(int(a)*int(b) for a,b in zip(self.rules,self.vector))    
            
        #total += abs(self.position - self.parent.position)
        #total += abs(self.fret - self.parent.fret)
        #total += abs(self.string - self.parent.string)
        #total += abs(self.finger - int(str(self.parent.finger).split(',')[-1]))
        #return total
    # ============================= ============================= #
    # Node stuff
    def hasChildren(self):
        return self.children
    
    def isChild(self):
        return self.parent and (self in self.parent.children)
    
    def isRoot(self):
        return (self is self.parent)

    def isLeaf(self):
        return not self.children

    def addChild(self, child):
        if not (child in self.children):
            self.children.append(child)
    
    def resetScore(self):
        self.score = 0
        
    def replaceNodeData(self, notenode):
        self.vector = notenode.vector
        self.pitch = notenode.pitch
        self.fret = notenode.fret
        self.string = notenode.string
        self.finger = notenode.finger
        self.score = notenode.score
        self.octave = notenode.octave
        self.position = notenode.position
        self.me = notenode.me
        
        notenode.parent.addChild(self)
        self.delete()
        self.parent = notenode.parent
        
    def delete(self):
        if self in self.parent.hasChildren():
            self.parent.children.remove(self)
    # ============================= ============================= #
    # check if two nodes contain the same pitch/octave info == are the same
    def equals(self, note):
        return ((note.pitch == self.pitch) and (note.octave == self.octave))
    # ============================= ============================= #
    # prints
    def getChildren(self):
        child = ''
        for ch in self.children:
            child += ch.me
            child += ' , '
        return child[:-2]
    
    def getNodeInfo(self):
        return ('Pitch {0} on fret {1} of string {2} with finger {3}'.format(self.pitch, self.fret, self.string, self.finger))

# ============================= ============================= ============================= #  
# ============================= ============================= ============================= #  
class NoteTree(object):
    # ============================= ============================= #
    def __init__(self, file, rules):
        self.options = options # imported
        self.rules = rules # imported in gui
        self.root = None # init
        self.best_path = [] # init
        self.fingering_paths = set() # init
        self._fingering_paths = set() # init
        self.leafs = [] # init
        self.scores = {} # init
        self.new_file = ''
        self.prints = ''
        self.file = ''

        if self.validate(file):
            self.file = file
            self.fingering_options = self.fillOptions() # created all possible fingering placement combs
            self.note_list = list(self.fillNotes()) # got note list
            self.chord_list = list(self.getChords()) # replace chords in note list
            self.expand() # expand tree with all combs
            self.fillPaths() # get all paths
            self.best() # compute best path
            self.writeFingers() # write new file
        #print(self.prints)
     
    # ============================= ============================= #
    # fills the options dict with all possible fingering combinations
    # NEEDS: option dictionary from Options.py 
    def fillOptions(self):
        fingerings = dict()
        fingers = [0,1,2,3,4]
        for option in options:
            pos_comb = options[option]
            add_comb = ''
            # for every fre-string combination add a finger
            for comb in pos_comb.split(','):
                add_finger = ''
                for finger in fingers:
                    # CHECKING: open chord only when fret==0
                    if comb[0]!='0':
                        if finger!=0:
                            add_finger = '({0}):{1},{2}'.format(comb,finger,add_finger)
                    else:
                        if finger==0:
                            add_finger = '({0}):{1},{2}'.format(comb,finger,add_finger)
                add_finger = add_finger[:-1]
                add_comb = '{0},{1}'.format(add_finger,add_comb)
            add_comb = add_comb[:-1]
            fingerings[option]=add_comb
        return fingerings
        
    # ============================= ============================= #
    # fills note_list with the XML notes
    def fillNotes(self):
        # gather notes
        note_list = []
        dom = parse(self.file)
        notes = dom.getElementsByTagName("note")
        # rests don't have steps or alters, filter them out.
        notes = filter(lambda note: not self.is_rest(note), notes)
        # for easiness filter out accidentals
        #notes = filter(lambda note: not self.is_accidental(note), notes)
        # fill list with all notes
        for note in notes:
            # alter '1' means sharp
            # alter '-1' means flat
            alter = self.get_alter(note)
            pitch, octave, duration, x = self.get_step(note)
            if alter == '1':
                pitch = pitch + 's'
            if alter == '-1':
                pitch = pitch + 'f'
            new_note = Note(pitch, octave, duration, x)
            new_note.setFingers(self.fingering_options[new_note.me])
            note_list.append(new_note)
        print('Creating tree for {0} notes'.format(len(note_list)))
        self.prints = self.prints + 'Creating tree for {0} notes'.format(len(note_list))
        return note_list
    
    # replace chords in note list
    def getChords(self):
        prevx = 0
        currx = 0
        chords = [] # the list of chords to return 
        #new_chord = Chord()
        chord_notes = [] # the notes
        for note in self.note_list:
            currx = note.x
            if currx != prevx:
                chords.append(Chord(chord_notes))
                chord_notes = [] # refresh chord
                chord_notes.append(note) # add new note
                prevx = note.x
            else:
                chord_notes.append(note)
        chords.append(Chord(chord_notes)) # last note
        return chords[1:]
                 
    # ============================= ============================= #
    # creates all possible fingering combinations
    def expand(self):
        pos = 0
        # create root
        n = Note('ROOT','0')
        n.setFingers('(0/0):0')
        self.root = NoteNode(n, self.rules, False, n.fingers)
        #self.root.score = -1000
        # continue for the rest notes
        stack = []
        stack.append(self.root)
        stack_dummy = [] # dummy stack
        lim = 3 # set limit
        print('Child number limit set to: {0}'.format(lim))
        c = 0 # for limit
        msg = 0 # for printing
        i = 0 # for status bar
        for chord in self.chord_list: # start for all notes
            while stack:
                sc = [] # scores
                stack_dummy = []
                for child in stack: # start for all new added nodes
                    c =0 
                    #ch_finger = int(str(child.finger).split(',')[-1])
                    if len(chord.notes) == 1: # chord containing one note
                        note = chord.notes[0]
                        if len(note.fingers.split(','))>1:
                            for finger in note.fingers.split(','):
                                node = NoteNode(note, self.rules, False, finger, child)
                                if (c<=lim): # check the scores are -10
                                    stack_dummy.append(node)
                                    sc.append(node.score)
                                    c += 1
                                elif max(sc)>node.score: # replace max score
                                    stack_dummy[sc.index(max(sc))].replaceNodeData(node)
                                    sc[sc.index(max(sc))] = node.score
                                else: 
                                    node.delete()
                        else:
                            node = NoteNode(note, self.rules, False, note.fingers, child)
                            if (c<=lim):
                                stack_dummy.append(node)
                                sc.append(node.score)
                                c += 1
                            elif max(sc)>node.score: # replace max score
                                stack_dummy[sc.index(max(sc))].replaceNodeData(node)
                                sc[sc.index(max(sc))] = node.score
                            else: 
                                node.delete()
                    else: # actual chord with multiple notes
                        node = NoteNode(chord.notes, self.rules, True, parent = child)
                        stack_dummy.append(node)
                        c += 1
                stack = list(stack_dummy)
                gc.collect()
                break # out of while with stack containing the leafs to be expanded
            msg += 1
            i += 1 # printing bars and stuff
            sys.stdout.write('\r')
            sys.stdout.write("[{: <50}] {}%".format(u'\u2713'*int((50/len(self.chord_list))*i), int((100/len(self.chord_list))*i)))
            sys.stdout.flush()
            #sleep(0.25)
            if msg%5==0: # status updates and limiting
                #print('Expanded {0} notes... paths: {1}'.format(msg, len(stack)))
                self.prints = self.prints + 'Expanded {0} notes... paths: {1}'.format(msg, len(stack))
                best = self.limit(stack)
                stack = list(best)
                #print('Cutting down to... {0}'.format(len(stack)))
                self.prints = self.prints + 'Cutting down to... {0}'.format(len(stack))
        self.leafs = list(stack)
        print('\nCreated tree with {0} leafs'.format(len(self.leafs)))
        self.prints = self.prints + 'Created tree with {0} leafs'.format(len(self.leafs))
    
    # ============================= ============================= #
    # fill fingering_paths set with all possible fingering paths
    # start from leafs
    def fillPaths(self):
        print('Computing paths')
        for node in self.leafs:
            path = ''
            curr = node
            while curr != self.root:
                path = curr.me + path
                path = ' > ' + path
                curr = curr.parent
            self.fingering_paths.add(path[3:])
            
        #print('Computing paths')
        for node in self.leafs:
            path = list()
            curr = node
            while not curr.equals(self.root):
                path.insert(0, curr)
                curr = curr.parent
            self._fingering_paths.add(tuple(path)) 
        #print('There were {0} possible paths'.format(len(self._fingering_paths)))
        #self.prints = self.prints + '\nThere were {0} possible paths'.format(len(self._fingering_paths))
        
    # ============================= ============================= #
    def score(self):
        # creates the scores dictionary
        for node in self._fingering_paths:
            self.scores[node] = node[-1].score
    
    def limit(self, stack):
        # downsize stack list of nodes
        minv = stack[0].score
        i = 0
        while i<len(stack):
            if len(stack)==1:
                break
            if stack[i].score>minv:
                stack.pop(i)
                i = 1
                continue
            else: # stack[i].score<minv:
                minv = stack[i].score
                #for j in range(i-1):
                #    stack.pop(j)
                stack.pop(i-1)
                i = 1
                continue
        return stack
        
    def best(self):
        self.score()
        best = min(self.scores, key=self.scores.get)
        s = ''
        for node in best:
            s += node.me
            s += ' '
            if len(str(node.finger).split(','))>1: # split chords fingers
                #print(node.finger)
                for finger in str(node.finger).split(','):
                    self.best_path.append(int(finger))
            else:
                self.best_path.append(node.finger)
        #print('Chosen path: {0} with score: {1}'.format(s[:-1], self.scores[best]))
        self.prints = self.prints + '\nChosen path: {0} \nwith score: {1}'.format(s[:-1], self.scores[best])
        
    # ============================= ============================= #
    # print calls
    # print all the nodes in the tree DEPTH first
    def printTree(self, start = None):
        start = start or self.root
        if (start.equals(self.root)):
            print('Starting from root: \n{0}'.format(start.getNodeInfo()))
        if start.children:
            for ch in start.children:
                print(ch.getNodeInfo())
                self.printTree(ch)
    
    # print all fingering paths
    def printPaths(self):
        for path in self.fingering_paths:
            yield(path + '\n')
    
    # print all scored paths
    def printScores(self):
        for path in self._fingering_paths:
            yield(self.scores[path])
    
    # print all notes in the tree
    def printNoteList(self):
        for note in self.note_list:
            print(note.getNoteInfo())
        
    # ============================= ============================= #
    def validate(self, file):
        if os.path.isfile(file):
            return True
        else:
            self.prints = 'File does not exist. Exited.'
    
    # ============================= ============================= #
    # write computed fingerings to new XML file
    def writeFingers(self):
        tree = ET.parse(self.file)
        root = tree.getroot()
        p = 0
        for child in root.iter('note'):
            notations = ET.Element('notations')
            technical = ET.SubElement(notations, 'technical') 
            fingering = ET.SubElement(technical, 'fingering')
            if child.find('rest')==None:
                fingering.text = str(self.best_path[p])
                child.append(notations)
                p += 1
        self.new_file = str('New_{0}'.format(self.file))
        tree.write(self.new_file)
        print('New file writing complete')
            
    # ============================= ============================= #
    # XML parsing helping functions            
    def get_step(self, note):
        stepNode = note.getElementsByTagName("step")[0]
        octave = note.getElementsByTagName("octave")[0]
        duration = note.getElementsByTagName("duration")
        x = note.getAttribute("default-x")
        if note.getElementsByTagName("duration"):
            duration = note.getElementsByTagName("duration")[0]
            return str(stepNode.childNodes[0].nodeValue), str(octave.childNodes[0].nodeValue), str(duration.childNodes[0].nodeValue), x
        else:
            return str(stepNode.childNodes[0].nodeValue), str(octave.childNodes[0].nodeValue), '0', x

    def get_alter(self, note):
        alters = note.getElementsByTagName("alter")
        if len(alters) == 0:
            return None
        return alters[0].childNodes[0].nodeValue

    def is_rest(self, note):
        return len(note.getElementsByTagName("rest")) > 0

    def is_accidental(self, note):
        return self.get_alter(note) != None

# ============================= ============================= ============================= #
# ============================= ============================= ============================= #

from tkinter import *
from tkinter import messagebox
from tkinter.tix import *
from Classes import *
from Options import *
from Rules import *
import os.path

class GUI():

    def __init__(self, master):        
        # init frame
        self.rules = rules
        self.master = master
        self.master.geometry('600x300')
        self.master.title('Computing Fingerings')
        swin = ScrolledWindow(self.master, scrollbar=Y, width=600 , height=300)
        swin.pack()
        self.win = swin.window
        
        
        self.frame = Frame(self.win, cursor='cross', relief=SUNKEN, bg="light blue")
        self.frame.pack(side = LEFT, fill = BOTH, expand = True, padx = 10, pady = 10)
        
        # string variables
        self.file = StringVar()
        self.file.set("sTest.xml")
        self.choice = StringVar()
        self.created = StringVar()
        self.prints = StringVar()
        
        # file entry
        self.entry = Entry(self.frame, textvariable=self.file, font='Helvetica 10 italic', justify='center', width=40)
        self.entry.pack(ipady=3)
        self.entry.bind('<Leave>' ,self.setfile)
        
        # validate message
        self.val_msg = Message(self.frame, textvariable=self.choice, font='Helvetica 10', justify='center', width=400)
        self.val_msg.pack(ipady=3)
        
        # button frame
        #self.but_frame = Frame(self.frame, pady=10, padx=10, cursor='cross', relief=SUNKEN, bg="light blue")
        #self.but_frame.place(in_=self.frame, anchor="c", relx=.5, rely=.5)
        
        # show rules button
        self.create = Button(self.frame, text="SHOW RULES", fg="brown", font='Helvetica 10 bold', command=self.showrules)
        self.create.pack(ipady=3) 
        
        self.ruleset = Button(self.frame, text="CUSTOMIZE RULES", fg="brown", font='Helvetica 10 bold', command=self.setrules)
        self.ruleset.pack(ipady=3)
        
        # create Tree button
        self.create = Button(self.frame, text="COMPUTE FINGERINGS", fg="brown", font='Helvetica 10 bold', command=self.createTree)
        self.create.pack(ipady=3)           
        
        # prints display message
        self.res_msg = Message(self.frame, textvariable=self.prints, font='Helvetica 10', justify='center', width=560)
        self.res_msg.pack(ipady=3) 
        
        # created message entry
        self.val = Entry(self.frame, textvariable=self.created, font='Helvetica 10', justify='center', width=40)
        self.val.pack(ipady=3)     
        
        # quit button
        self.quit = Button(self.frame, text="QUIT", font='Helvetica 10 bold', fg="brown", command=self.frame.quit)
        self.quit.pack(ipady=3)     
        
    def getR(self, rules):
        r = ''
        r = r.join(i+'\n' for i in str(rules).split())
        r = r.replace(']','')
        r = r.replace('[','')
        r = r.replace(',','')
        return r
        
    def setfile(self, event):
        self.choice.set("Compute fingerings for: {0} ?".format(self.file.get()))
    
    def showrules(self):
        #messagebox.showinfo("Rules", self.rules)
        t = Toplevel(self.master)
        t.wm_title('Scoring Rules')
        t.geometry('250x230')
        t.resizable(width=False, height=False)
        swin = ScrolledWindow(t, scrollbar=Y, width=250 , height=230)
        swin.pack()
        win = swin.window
        f = Frame(win, bg='light blue', relief=SUNKEN)
        f.pack(fill = BOTH, expand = True, padx = 5, pady = 5)
        
        msg = Message(f, text=self.getR(self.rules), font='Helvetica 10', justify='center', width=30)
        msg.pack(ipady=3)
        
        q = Button(f, text="CLOSE", fg="brown", font='Helvetica 10 bold', command=t.destroy)
        q.pack(ipady=3)        
        
    def setrules(self):
        t = Toplevel(self.master)
        t.wm_title('Customize Rules Weights')
        t.geometry('350x400')
        t.resizable(width=False, height=False)
        swin = ScrolledWindow(t, scrollbar=Y, width=350 , height=400)
        swin.pack()
        win = swin.window
        f = Frame(win, bg='light blue', relief=SUNKEN)
        f.pack(fill = BOTH, expand = True, padx = 5, pady = 5)
        
        # add message
        m1 = StringVar()
        m2 = StringVar()
        m3 = StringVar()
        m4 = StringVar()
        m5 = StringVar()
        m6 = StringVar()
        m7 = StringVar()
        m8 = StringVar()
        m9 = StringVar()
        m10 = StringVar()
        m11 = StringVar()
        m12 = StringVar()
        m1.set('Penalize position change weight')
        m2.set('Prioritize same finger-position weight')
        m3.set('Prioritize open position weight')
        m4.set('Penalize consecutive same finger weight')
        m5.set('Favor consecutive same note-finger usage')
        m6.set('Favor bigger finger numbers weight')
        m7.set('Favor smaller position numbers weight')
        m8.set('Penalize 4th finger')
        m9.set('Position difference')
        m10.set('Fret distance')
        m11.set('String difference')
        m12.set('Finger distance')
        
        #add frame
        f1 = Frame(f, bg='light blue', relief=SUNKEN)
        f1.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f2 = Frame(f, bg='light blue', relief=SUNKEN)
        f2.pack(fill = BOTH, expand = True, padx = 3, pady = 3)        
        f3 = Frame(f, bg='light blue', relief=SUNKEN)
        f3.pack(fill = BOTH, expand = True, padx = 3, pady = 3)        
        f4 = Frame(f, bg='light blue', relief=SUNKEN)
        f4.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f5 = Frame(f, bg='light blue', relief=SUNKEN)
        f5.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f6 = Frame(f, bg='light blue', relief=SUNKEN)
        f6.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f7 = Frame(f, bg='light blue', relief=SUNKEN)
        f7.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f8 = Frame(f, bg='light blue', relief=SUNKEN)
        f8.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f9 = Frame(f, bg='light blue', relief=SUNKEN)
        f9.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f10 = Frame(f, bg='light blue', relief=SUNKEN)
        f10.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f11 = Frame(f, bg='light blue', relief=SUNKEN)
        f11.pack(fill = BOTH, expand = True, padx = 3, pady = 3)
        f12 = Frame(f, bg='light blue', relief=SUNKEN)
        f12.pack(fill = BOTH, expand = True, padx = 3, pady = 3)        
        
        # show message
        msg1 = Message(f1, textvariable=m1, font='Helvetica 10', justify='center', width=500)
        msg1.pack(side=LEFT, ipady=3)
        msg2 = Message(f2, textvariable=m2, font='Helvetica 10', justify='center', width=500)
        msg2.pack(side=LEFT, ipady=3)
        msg3 = Message(f3, textvariable=m3, font='Helvetica 10', justify='center', width=500)
        msg3.pack(side=LEFT, ipady=3)
        msg4 = Message(f4, textvariable=m4, font='Helvetica 10', justify='center', width=500)
        msg4.pack(side=LEFT, ipady=3)
        msg5 = Message(f5, textvariable=m5, font='Helvetica 10', justify='center', width=500)
        msg5.pack(side=LEFT, ipady=3)
        msg6 = Message(f6, textvariable=m6, font='Helvetica 10', justify='center', width=500)
        msg6.pack(side=LEFT, ipady=3)
        msg7 = Message(f7, textvariable=m7, font='Helvetica 10', justify='center', width=500)   
        msg7.pack(side=LEFT, ipady=3)
        msg8 = Message(f8, textvariable=m8, font='Helvetica 10', justify='center', width=500)   
        msg8.pack(side=LEFT, ipady=3)
        msg9 = Message(f9, textvariable=m9, font='Helvetica 10', justify='center', width=500)  
        msg9.pack(side=LEFT, ipady=3)
        msg10 = Message(f10, textvariable=m10, font='Helvetica 10', justify='center', width=500)  
        msg10.pack(side=LEFT, ipady=3)
        msg11 = Message(f11, textvariable=m10, font='Helvetica 10', justify='center', width=500)  
        msg11.pack(side=LEFT, ipady=3)
        msg12 = Message(f11, textvariable=m10, font='Helvetica 10', justify='center', width=500)
        msg12.pack(side=LEFT, ipady=3)
        
        # add entry
        self.e1 = Entry(f1, font='Helvetica 10 italic', justify='center', width=10)
        self.e1.pack(side=RIGHT, ipady=3)
        self.e2 = Entry(f2, font='Helvetica 10 italic', justify='center', width=10)
        self.e2.pack(side=RIGHT, ipady=3)
        self.e3 = Entry(f3, font='Helvetica 10 italic', justify='center', width=10)
        self.e3.pack(side=RIGHT, ipady=3)
        self.e4 = Entry(f4, font='Helvetica 10 italic', justify='center', width=10)
        self.e4.pack(side=RIGHT, ipady=3)
        self.e5 = Entry(f5, font='Helvetica 10 italic', justify='center', width=10)
        self.e5.pack(side=RIGHT, ipady=3)
        self.e6 = Entry(f6, font='Helvetica 10 italic', justify='center', width=10)
        self.e6.pack(side=RIGHT, ipady=3)
        self.e7 = Entry(f7, font='Helvetica 10 italic', justify='center', width=10)
        self.e7.pack(side=RIGHT, ipady=3)
        self.e8 = Entry(f8, font='Helvetica 10 italic', justify='center', width=10)
        self.e8.pack(side=RIGHT, ipady=3)
        self.e9 = Entry(f9, font='Helvetica 10 italic', justify='center', width=10)
        self.e9.pack(side=RIGHT, ipady=3)
        self.e10 = Entry(f10, font='Helvetica 10 italic', justify='center', width=10)
        self.e10.pack(side=RIGHT, ipady=3)
        self.e11 = Entry(f11, font='Helvetica 10 italic', justify='center', width=10)
        self.e11.pack(side=RIGHT, ipady=3)
        self.e12 = Entry(f12, font='Helvetica 10 italic', justify='center', width=10)
        self.e12.pack(side=RIGHT, ipady=3)

        s = Button(f, text="SET WEIGHTS", fg="brown", font='Helvetica 10 bold', command=self.setR)
        s.pack(ipady=3)
        
        r = Button(f, text="RESTORE DEFAULT", fg="brown", font='Helvetica 10 bold', command=self.setD)
        r.pack(ipady=3)
        
        q = Button(f, text="CLOSE", fg="brown", font='Helvetica 10 bold', command=t.destroy)
        q.pack(ipady=3)
    
    def setR(self):
        new_rules = 'rules = [{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}]'.format(self.e1.get() or 0,self.e2.get() or 0,self.e3.get() or 0,
                                                               self.e4.get() or 0,self.e5.get() or 0,self.e6.get() or 0, 
                                                        self.e7.get() or 0, self.e8.get() or 0, self.e9.get() or 0,self.e10.get() or 0,
                                                                    self.e11.get() or 0, self.e12.get() or 0)
        file = open('Rules.py','w')
        file.write(new_rules)
        new_rules = new_rules.replace("rules = ",'')
        new_rules = new_rules.replace("]",'')
        new_rules = new_rules.replace(",",'')
        new_rules = new_rules.replace("[",'')
        self.rules = list(new_rules.split())
        #print(self.rules)
      
    def setD(self):
        # INITIAL: rules = [10, -10, -20, 10, -5, -5, 0, 0, 0, 0]
        new_rules = 'rules = [10, -10, -20, 10, -10, -5, -5, 5, 0, 0, 0, 0]'
        file = open('Rules.py','w')
        file.write(new_rules)
        new_rules = new_rules.replace("rules = ",'')
        new_rules = new_rules.replace("]",'')
        new_rules = new_rules.replace(",",'')
        new_rules = new_rules.replace("[",'')
        self.rules = list(new_rules.split())
        messagebox.showinfo("Rules", 'Weight restored')
    
    def createTree(self):
        if os.path.isfile(self.file.get()):
            tree = NoteTree(self.file.get(), list(self.rules))
            self.prints.set(tree.prints)
            self.created.set('Created {0}'.format(tree.new_file))
        else:
            self.created.set('Please enter a valid MusicXML file.')

root = Tk()
root.resizable(width=False, height=False)
gui = GUI(root)
root.mainloop() #runs until quit or closed
root.destroy() #cannot invoke, application is destroyed