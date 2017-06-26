import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString
from Options import *
from array import array
from collections import deque

# ============================= ============================= ============================= #

class Note(object):
    # ============================= ============================= #
    def __init__(self, pitch, octave, duration = None, x = None):
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

class Chord(Note):
    # ============================= ============================= #
    def __init__(self, notes = None):
        self.notes = list()
        
    def addNote(self, note):
        self.notes.append(note)
                 
    def getNotes(self):
        return self.notes
    
# ============================= ============================= ============================= #
                 
class NoteNode(object):
    # ============================= ============================= #
    def __init__(self, note, finger, parent = None):
        self.pitch, self.fret, self.string, self.finger = self.analyze(note, finger)
        self.score = 0
        self.octave = note.getOctave()
        self.children = list()
        self.position = self.fret - self.finger +1
        if parent:
            self.parent = parent
            self.parent.addChild(self)
        else:
            self.parent = self
        self.me = str('{0}-{1}: ({2}/{3}): {4}'.format(self.pitch, self.octave, self.fret, self.string, self.finger))
        self.score = self._score()
            
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
    
    def _score(self):
        # calculate score
        # the bigger the score the worse the fingering
        total = 0
        total += abs(self.position-self.parent.position)
        total += abs(self.fret-self.parent.fret)
        total += abs(self.string-self.parent.string)
        #if self.finger==self.parent.finger:
        #    total += 10
        return total
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
    
    def replaceNodeData(self, note, children):
        self.note = note
        self.children = children
        if self.hasChildren():
            for child in self.children:
                child.parent = self
                
    # ============================= ============================= #
    # check if two nodes contain the same pitch info == are the same
    def equals(self, note):
        return note.me == self.me
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
    
class NoteTree(object):
    # ============================= ============================= #
    def __init__(self, file):
        self.file = file
        self.options = options # imported
        self.rules = rules # imported
        self.root = None # init
        self.best_path = list() # init
        self.fingering_paths = set() # init
        self._fingering_paths = set() # init
        self.leafs = list() # init
        self.scores = {} # init
        
        self.fingering_options = self.fillOptions() # created all possible fingering placement combs
        self.note_list = self.fillNotes() # got note list
        self.chord_list = self.getChords() # replace chords in note list
        self.expand() # expand tree with all combs
        self.fillPaths() # get all paths
        self.best() # compute best path
        self.writeFingers() # write new file
     
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
        note_list = list()
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
            if alter:
                pitch = pitch + 's'
            new_note = Note(pitch, octave, duration, x)
            new_note.setFingers(self.fingering_options[new_note.me])
            note_list.append(new_note)
        print('Creating tree for {0} notes'.format(len(note_list)))
        return note_list
    
    # replace chords in note list
    def getChords(self):
        prevx = 0
        currx = 0
        chords = list()
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
        self.root = NoteNode(n, n.fingers)
        # continue for the rest notes
        stack = list()
        stack.append(self.root)
        c = 0
        i = 0
        for note in self.note_list:
            c = 0 
            for child in stack[-i:]:
                curr_min = self.scorepath(child)
                if len(note.fingers.split(','))>1:
                    for finger in note.fingers.split(','):
                        node = NoteNode(note, finger, child)
                        #print('child {0} on parent {1}'.format(node.me, child.me))
                        #score = node.score
                        #if score <= curr_min:
                        #    curr_min = self.scorepath(node)
                        stack.append(node)
                        c += 1
                else:
                    node = NoteNode(note, note.fingers, child)
                    #print('child {0} on parent {1}'.format(node.me, child.me))
                    #score = node.score
                    #if score <= curr_min:
                    #    curr_min = self.scorepath(node)
                    stack.append(node)
                    c += 1
            i = c
        print('Created tree with {0} leafs'.format(c))
        self.leafs = stack[-i:]
    
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
            
        print('Computing paths')
        for node in self.leafs:
            path = list()
            curr = node
            while not curr.equals(self.root):
                path.insert(0, curr)
                curr = curr.parent
            self._fingering_paths.add(tuple(path)) 
                
        print('There are {0} possible paths'.format(len(self._fingering_paths)))
        
    # ============================= ============================= #
    def score(self):
        # evaluate Nodes
        for path in self._fingering_paths:
            sc = self._score(path)
            self.scores[path] = sc
    
    def _score(self, path):
        # format: pitch-octave: (string/note):finger > ...
        total = 0
        pos_changes = 0
        curr_pos = 0
        tot_finger_dist = 0
        for node in path:
            if curr_pos != node.position:
                pos_changes += 1
                curr_pos = node.position
            tot_finger_dist += node.score
        total = tot_finger_dist + pos_changes # total finger distances, position changes
        return total
    
    def scorepath(self, node):
        curr = node
        path = list()
        while not curr.equals(self.root):
            path.insert(0, curr)
            curr = curr.parent
        return self._score(path)
    
    def best(self):
        self.score()
        best = min(self.scores, key=self.scores.get)
        s = ''
        for node in best:
            s += node.me
            s += ' '
            self.best_path.append(node.finger)
        print('Chosen path: {0} with score: {1}'.format(s[:-1], self.scores[best]))
        
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
            print(path + '\n')
    
    # print all scored paths
    def printScores(self):
        for path in self._fingering_paths:
            print(self.scores[path])
    
    # print all notes in the tree
    def printNoteList(self):
        for note in self.note_list:
            print(note.getNoteInfo())
        
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
        new_file = str('New_{0}'.format(self.file))
        tree.write(new_file)
            
    # ============================= ============================= #
    # XML parsing helping functions            
    def get_step(self, note):
        stepNode = note.getElementsByTagName("step")[0]
        octave = note.getElementsByTagName("octave")[0]
        duration = note.getElementsByTagName("duration")[0]
        x = note.getAttribute("default-x")
        return str(stepNode.childNodes[0].nodeValue), str(octave.childNodes[0].nodeValue), str(duration.childNodes[0].nodeValue), x
        
    def get_alter(self, note):
        alters = note.getElementsByTagName("alter")
        if len(alters) == 0:
            return None
        return alters[0]

    def is_rest(self, note):
        return len(note.getElementsByTagName("rest")) > 0

    def is_accidental(self, note):
        return self.get_alter(note) != None

# ============================= ============================= ============================= #