import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString
from array import array
from Options import *

class Note(object):
    # ============================= ============================= #
    def __init__(self, pitch, octave):
        self.pitch = pitch
        self.octave = octave
        self.me = str('{0}-{1}'.format(self.pitch,self.octave))
        self.fingers = None
    
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

    
class NoteNode(object):
    # ============================= ============================= #
    def __init__(self, note, finger, parent = None):
        self.pitch, self.fret, self.string, self.finger = self.analyze(note,finger)
        self.score = 0
        self.octave = note.getOctave()
        self.children = set()
        self.position = self.fret - self.finger
        if parent:
            self.parent = parent
            self.parent.addChild(self)
        else:
            self.parent = self
        self.me = str('{0}-{1}: ({2}/{3}): {4}'.format(self.pitch, self.octave, self.fret, self.string, self.finger))
        self.score = self._score()
            
    # ============================= ============================= #
    # Note format: (fret-string):finger
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
        total = 0
        total += abs(self.position-self.parent.position)
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
        self.children.add(child)
    
    def replaceNodeData(self, note, children):
        self.note = note
        self.children = children
        if self.hasChildren():
            for child in self.children:
                child.parent = self
                
    # ============================= ============================= #
    # check if two nodes contain the same info == are the same
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
    
    
import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString
from Options import *
from array import array

class NoteTree(object):
    # ============================= ============================= #
    def __init__(self, file):
        self.file = file
        self.options = options
        self.rules = rules
        self.root = None
        self.fingering_options = self.fillOptions()
        self.note_list = self.fillNotes()
        self.best_path = list()
        self.fingering_paths = set()
        self._fingering_paths = set()
        self.scores = {}
        self.expand()
        self.fillPaths(self.root)
        self._fillPaths(self.root)
        self.best()
        self.writeFingers()
     
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
        notes = filter(lambda note: not self.is_accidental(note), notes)
        # fill list with all notes
        for note in notes:
            pitch, octave = self.get_step(note)
            new_note = Note(pitch, octave)
            new_note.setFingers(self.fingering_options[new_note.me])
            note_list.append(new_note)
        print('Starting tree of {0} notes'.format(len(note_list)))
        return note_list
    
    # ============================= ============================= #
    # creates all possible fingering combinations
    def expand(self, note_pos = 0, parent = None):
        pos = note_pos
        last = parent
        # check for root, if None, create it
        if not self.root:
            note = self.note_list[pos]
            if len(note.fingers.split(','))>1:
                for finger in note.fingers.split(','):
                    self.root = NoteNode(note, finger)
                    print('Added root {0}'.format(self.root.getNodeInfo()))
                    self.expand(1, self.root)
            else:
                self.root = NoteNode(note, note.fingers)
                print('Added root {0}'.format(self.root.getNodeInfo()))
                self.expand(1, self.root)
        else:
        # add children recursively
            print('Expanding note...{0}'.format(pos))
            note = self.note_list[pos]
            if len(note.fingers.split(','))>1:
                for finger in note.fingers.split(','):
                        nodeTest = NoteNode(note, finger, last)
                        #print('Added {0}'.format(nodeTest.getNodeInfo()))
                        # check if there are more notes, add them
                        if pos+1<len(self.note_list) :
                            self.expand(pos+1, nodeTest)
            else:
                nodeTest = NoteNode(note, note.fingers, last)
                #print('Added {0}'.format(nodeTest.getNodeInfo()))
                # check if there are more notes, add them
                if pos+1<len(self.note_list) :
                    self.expand(pos+1, nodeTest)
    
    # ============================= ============================= #
    # fill fingering_paths set with all possible fingering paths
    def fillPaths(self, node, path = ''):
        print('Getting paths')
        path += node.me
        path += ' > '
        if node.children:
            for ch in node.children:
                self.fillPaths(ch, path)
        else: # reached leaf
        #if len(path.split(' > ')) == len(self.note_list):
            self.fingering_paths.add(path[:-3])
                  
    def _fillPaths(self, node, path = list()):
        print('Getting paths')
        path.append(node)
        if node.children:
            for ch in node.children:
                self._fillPaths(ch, path)
            path.remove(node)
        else:
            self._fingering_paths.add(tuple(path))
            path.remove(node)
                
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
        total = tot_finger_dist + pos_changes
        return total
    
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
            print(path)

    def print_Paths(self):
        for path in self._fingering_paths:
            s = ''
            for node in path:
                s += node.me
                s += ' , '
            print(s[:-2])
    
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
                if child.find('accidental')==None:
                    fingering.text = str(self.best_path[p])
                    child.append(notations)
                    p+=1
        new_file = str('New_{0}'.format(self.file))
        tree.write(new_file)
            
    # ============================= ============================= #
    # XML parsing helping functions            
    def get_step(self, note):
        stepNode = note.getElementsByTagName("step")[0]
        octave = note.getElementsByTagName("octave")[0]
        return str(stepNode.childNodes[0].nodeValue), str(octave.childNodes[0].nodeValue)
        
    def get_alter(self, note):
        alters = note.getElementsByTagName("alter")
        if len(alters) == 0:
            return None
        return alters[0]

    def is_rest(self, note):
        return len(note.getElementsByTagName("rest")) > 0

    def is_accidental(self, note):
        return self.get_alter(note) != None
    