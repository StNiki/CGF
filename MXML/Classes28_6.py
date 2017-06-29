import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString
from Options import *
from array import array
from collections import deque
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
    def __init__(self, notes = None):
        self.notes = list() # list of notenodes 
        
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
            # initialise
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
            self.vector = [0,0,0,0,0,0,0,0,0,0]
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
        total = 0
        if self.position != self.parent.position: # penalize position change
            if self.position != 0:
                total += 10
                self.vector[0] = 1
        if self.position == self.finger: # prioritize finger-position
            total += -10
            self.vector[1] = 1
        if self.fret == 0: # prioritize 0
            total += -20
            self.vector[2] = 1
        if self.finger == int(str(self.parent.finger).split(',')[-1]): # fingers should be different
            if self.finger != 0:
                total += 10
                self.vector[3] = 1
        if self.finger < int(str(self.parent.finger).split(',')[-1]): # higher fingers first
            if self.parent.finger != 0:
                total += -5
                self.vector[4] = 1
        if self.fret < 5: # prioritize smaller positions
            total += -5
            self.vector[5] = 1
        self.vector[6] = abs(self.position - self.parent.position)
        self.vector[7] = abs(self.fret - self.parent.fret)
        self.vector[8] = abs(self.string - self.parent.string)
        self.vector[9] = abs(self.finger - int(str(self.parent.finger).split(',')[-1]))    
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
    # check if two nodes contain the same pitch info == are the same
    def equals(self, note):
        return note.pitch == self.pitch
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
            self.note_list = self.fillNotes() # got note list
            self.chord_list = self.getChords() # replace chords in note list
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
        chords = []
        new_chord = Chord()
        for note in self.note_list:
            currx = note.x
            if currx != prevx:
                if new_chord.notes:
                    chords.append(new_chord)
                new_chord = Chord() # refresh chord
                new_chord.addNote(note)
                prevx = note.x
            else:
                new_chord.addNote(note)
        chords.append(new_chord) # last note
        return chords
                 
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
        lim = 1 # set limit
        c = 0
        for chord in self.chord_list: # start for all notes
            while stack:
                sc = [] # scores
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
                stack_dummy = []
                break
        self.leafs = list(stack)
        print('Created tree with {0} leafs'.format(len(self.leafs)))
    
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
        print('There were {0} possible paths'.format(len(self._fingering_paths)))
        self.prints = self.prints + '\nThere were {0} possible paths'.format(len(self._fingering_paths))
        
    # ============================= ============================= #
    def score(self):
        # creates the scores dictionary
        for node in self._fingering_paths:
            self.scores[node] = node[-1].score
    
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
        print('Chosen path: {0} with score: {1}'.format(s[:-1], self.scores[best]))
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