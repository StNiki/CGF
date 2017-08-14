from Classes import *
from Rules import rules

root = Tk()
root.resizable(width=False, height=False)
gui = GUI(root)
root.mainloop() #runs until quit or closed
root.destroy() #cannot invoke, application is destroyed