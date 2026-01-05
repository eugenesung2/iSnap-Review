# Dataset

This data contains detailed log data of students' use of the [iSnap](http://go.ncsu.edu/isnap) programming environment for an introductory undergraduate computing course for non-majors. The course content focused on computer applications, but also included a once-per-week lab section where students learned to program, using a curriculum loosely based on the [Beauty and Joy of Computing](http://bjc.berkeley.edu/). The data includes data from both in-lab assignments, where students worked in the lab sections with a TA available for help, and independent homework assignments.

The assignments for the course, their descriptions, and solutions, can be found in the [Assignments.md](Resources/Assignments.md) file.

TODO: Need to add both versions of Guessing Game 2 .

TODO: May also want to include the .xml files, instead of just markdown

## Semesters and Inteventions

There were a number of interventions in the course, which are described in some detail, along with relevant papers:


| Semester | # Students | Intervention(s) | Papers | Notes |
| - | - | - | - | - |
| Fall 2015 | 82 | None |   |   |
| Spring 2016 |   |   |   |   |


TODO: Fill this in this table based on [this GDoc](https://docs.google.com/document/d/19Jc01-pvOf8CijGpluZZZkxDSmVzrTx_DP5_7f4eX6M/edit) and update it for the past few semesters. Also figure out which semesters had hints and indicate that (it's missing for some semesters in the doc)

### Hint Types: CTD and SourceCheck

TODO: Explain the difference between CTD and SourceCheck hints with screenshots


# ProgSnap2 Format

The data is stored in the ProgSnap2 format, a standard format for programming process data. You can read more about ProgSnap2 at [bit.ly/ProgSnap2](). The full specification has more details, but the most importnt files are:

* MainTable.csv: A log of every event that students experienced while using iSnap.
* CodeStates/CodeStates.csv: A table of each code state recorded from students (each event links to the student's current CodeState in the `CodeStateID` column).

This dataset also contains a number of special event types, columns, and values, usually denoted with the `X-` prefix. They are explained in detail below.

## Custom Event Types

The following events, prefixed with `X-` are not defined in ProgSnap2 and are instead defined here:

TODO: Add events and indicate additional columns that belong to these events

* `X-Run.StopProgram`:
* `X-Run.Pause`:
* `X-Run.Unpause`:
* `X-ChangeBlockCategory`:
* `X-Block.HidePrimitiveInPalette`
* `X-Block.ShowPrimitiveInPalette`
* `X-Block.scriptPic`
* `X-HighlightDisplay.startHighlight`
* `X-HighlightDisplay.stopHighlight`
* `X-HighlightDialogBoxMorph.cancelShowOnRun`
* `X-HighlightDialogBoxMorph.destroy`
* `X-HighlightDialogBoxMorph.promptShowOnRun`
* `X-HighlightDialogBoxMorph.showOnRun`:
* `X-HighlightDialogBoxMorph.toggleAutoClear`:
* `X-HighlightDialogBoxMorph.toggleInsert`:
* `X-HighlightDialogBoxMorph.toggleShowOnRun`:
* `X-HighlightDisplay.checkMyWork`:
* `X-HighlightDisplay.showHighlightDialog`:
* `X-HighlightDisplay.showHintWarning`:
* `X-HintDialogBox.done`:
* `X-HintDialogBox.destroy`:
* `X-IDE.toggleAppMode`:
* `X-IDE.toggleStageSize`:
* `X-IDE.rotationStyleChanged`:
* `X-IDE.paintNewSprite`:
* `X-IDE.exportGlobalBlocks`:
* `X-IDE.setSpriteTab`:
* `X-IDE.setSpriteDraggable`:
* `X-ProjectDialog.setSource`:
* `X-ProjectDialog.shown`:
* AttemptAction.BLOCK_TYPE_DIALOG_CANCEL:
* AttemptAction.BLOCK_TYPE_DIALOG_OK:
* AttemptAction.BLOCK_TYPE_DIALOG_NEW_BLOCK:
* AttemptAction.BLOCK_TYPE_DIALOG_CHANGE_BLOCK_TYPE:
* `X-HighlightDisplay.autoClear`:
* `X-HighlightDisplay.informNoHints`:
* `X-HighlightDisplay.promptShowBlockHints`:
* `X-HighlightDisplay.promptShowInserts`:
* `X-HighlightDisplay.showInsertsFromPrompt`:
* `X-IDE.opened`:
* `X-Assignment.setID`:
* `X-Assignment.setIDFrom`:

## Custom Columns

* X-EditSubtype
* X-BlockID
* X-BlockSelector
* X-BlockCategorySelected
* X-EventData
* X-HintData

### X-HintData Detailed Specification
TODO: Update this with more recent info

All hints instruct the student to change the children under one node of the AST. When present, the Feedback Text column will contain a JSON object with the following fields:

* parentID: the ID of the parent AST node, the children of which the hint directs the user to change. If the parent is a `script` node, it will not have an ID, in which case this refers to the script's parent node. If this value is null, that means that we cannot determine which node the hint referred to, usually due to a logging error.
* parentType: the type of the parent node in the AST (e.g. snapshot, callBlock, etc.).
* scriptIndex: if the parent is a script, this gives the child index of that script under it's parent, so that the script can be exactly identified using this value and the parentID.
* from: the current list of children of the parent node in the AST.
* to: the recommended list of children of the parent node in the AST, as suggested by the hint.
* message: the actual text shown to the user, in the case of a "structure hint," which gives text rather than showing what blocks to change.

## Custom CodeState format

### Snap Project structure

This data is from [Snap](http://snap.berkeley.edu/), which features drag-and-drop block-based programming and visual output. Snap projects have the following hierarchical elements:

* **Snapshot**: The high-level structure for an entire Snap project.
  * **Stage**: The background Sprite for a project. While the stage is itself a sprite, it also is that parent of all other Sprites.
    * *Sprite Members*: Stages contains all members of a Sprite, defined below:
    * **Sprites**: Scriptable actors on the Snap stage.
      * *Variables*: Local variables for this sprite.
      * **Scripts**: Executable code fragments.
        * **Blocks**: Code blocks (vertically alligned) in this Script
          * *Blocks and Scripts*: Depending on the type of block, it may contained additional Blocks and Scripts nested inside.
      * **Block Definitions**: Custom blocks just for this Sprite
        * *Inputs*: Parameters for the custom block.
        * **Script**: The primary script the executes when this block is run.
        * **Scripts**: Additional scripts that are held in the custom block (they won't run).
  * *Variables*: Global variables for the project.
  * **Block Definitions**: Global custom blocks

### ASTs

The AST representation used is fairly straightforward. It uses JSON to represent the tree structure. The most up-to-date documentation can be found at [this gist](https://gist.github.com/thomaswp/8c8ef19bd5203ce8b6cd4d6df5e3db44).

All code in these datasets are represented as abstract syntax trees (ASTs), stored in a JSON format. Each JSON object represents a node in the AST, and has the following properties:

* `type` [required]: The type of the node (e.g. "if-statement", "expression", "variable-declaration", etc.). In Snap, this could be the name of a built-in block (e.g. "forward", "turn"). The set of possible types is pre-defined by a given programming language, as they generally correspond to keywords. The possible types for a given language are defined in the grammar file for the dataset, discussed later.
* `value` [optional]: This contains any user-defined value for the node, such as the identifier for a variable or function, the value of a literal, or the name of an imported module These are things the student names, and they could take any value. **Note**: In the Snap datasets, string literal values have been removed to anonymize the dataset; however, these values are generally not relevant for hint generation.
* `children` [optional]: A map of this node's children, if any. In Python, the keys of the map indicate the relationship of the parent/child (e.g. a while loop might have a "condition" child). In the Snap dataset, they are simply numbers indicating the ordering of the children (e.g. arguments "0", "1" and "2"). The values are objects representing the children.
* `children-order` [optional]: The order of this node's children, represented as an array of keys from the `children` map. This is necessary because JSON maps have no ordering, though the order of the children in the map should correspond to the correct order.
* `id` [optional]: A trace-unqiue ID for the node that will be kept constant across ASTs in this trace. This is useful in block-based languages, for example, to identify a given block, even if it moves within the AST.

# Version History

This is version 1.0 of this README, last updated 2021/01/07.
