! Still known issues with writing tabs. Working on it.

To compute the fingerings for a music file in MusicXML the user can either run the runGUI.py or the runCGF.py script. 
The GUI class needs to be updated to the latest rules in order to work properly.

#### Important Note: The code is compatible with python 3.5

### How to use the run scripts:

Running the CFG script will open a window requesting an input filename by the user, which will then run the program using the default configuration. The output will be created as "New_[filename].xml".

Alternatively, the CFG shell script can be run on a console with the following options:

-n: input filename

-w: width limit parameter

-l: layer reset parameter

-p: print on the console the computed results

If the w, l, p options are omitted the program will use the default configuration (5, 5, False). In the name is omitted or the file is incorrect, the program will request a valid input file.

### How to use the graphic interface:

Running the GUI script will open the default window where the user has the following options:

- Type in the textbox the MusicXML file to be parsed. 
If the file does not exist or is invalid, a message will notify the user.

- Use the button SHOW RULES to view the rule set used in the framework. 
This open a new window that shows only the human description of the rules, not the condition to which they translate.

- Use the CUSTOMIZE RULES button to set the rule weights. 
This opens a new window where the user can type next to the shown rules the desired weight.
Once finished the user can click SET and CLOSE.

- Use the button CHANGE CONFIGURATION to set the pruning and system parameters.
This opens a new window where the user can type the width limit, notes per layer reset or choose the print option in the corresponding textbox.
Once finished the user can click SET and CLOSE.

- Use the button COMPUTE FINGERINGS to compute the fingerings for the selected file with the set parameters. If successful, there will be an output message with the new file that was created.

- Use QUIT to exit.
