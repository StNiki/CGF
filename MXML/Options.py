# E,A,D,G,B,E
# set default note combinations
# CREATES: options dictionary
# 'note-octave' playabe at 'fret:string'
# s: sharp
# TODO f: flat
options = {
    'E-2':('0/6'),
    'F-2':('1/6'),
    'Fs-2':('2/6'),
    'G-2':('3/6'),
    'Gs-2':('4/6'),
    'A-2':('5/6,0/5'),
    'As-2':('6/6,1/5'),
    'B-2':('7/6,2/5'),
    'C-3':('8/6,3/5'),
    'Cs-3':('9/6,4/5'),
    'D-3':('10/6,5/5,0/4'),
    'Ds-3':('11/6,6/5,1/4'),
    'E-3':('12/6,7/5,2/4'),
    'F-3':('8/5,3/4'),
    'Fs-3':('9/5,4/4'),
    'G-3':('10/5,5/4,0/3'),
    'Gs-3':('11/5,6/4,1/3'),
    'A-3':('12/5,7/4,2/3'),
    'As-3':('8/4,3/3'),
    'B-3':('9/4,4/3,0/2'),
    'C-4':('10/4,5/3,1/2'),
    'Cs-4':('11/4,6/3,2/2'),
    'D-4':('12/4,7/3,3/2'),
    'Ds-4':('8/3,4/2'),
    'E-4':('9/3,5/2,0/1'),
    'F-4':('10/3,6/2,1/1'),
    'Fs-4':('11/3,7/2,2/1'),
    'G-4':('12/3,8/2,3/1'),
    'Gs-4':('9/2,4/1'),
    'A-4':('10/2,5/1'),
    'As-4':('11/2,6/1'),
    'B-4':('12/2,7/1'),
    'C-5':('8/1'),
    'Cs-5':('9/1'),
    'D-5':('10/1'),
    'Ds-5':('11/1'),
    'E-5':('12/1')
}

#rules = {}
'''
rules = [10,-10,-20,10 ,-5,-5]
('Penalize position change weight')
('Prioritize same finger-position weight')
('Prioritize open position weight')
('Penalize consecutive same finger weight')
('Favor bigger finger numbers weight')
('Favor smaller position numbers weight')
'''