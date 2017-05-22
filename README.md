# KiCad-Lib
Schematic and footprint component library for KiCad EDA tool.
Use this library for all satellite KiCad schematic and layouts by adding this repository as a git submodule.

# Normal Usage
Go to the KiCad-Lib folder in your KiCad project folder. Create a branch on your local repositry:
```
git branch [your name]
git checkout [your name]
```
and edit the libray. Once done commit and push to the remote repository:
```
git add .
git commit -m "[enter commit message]" -m "[this is optional; allows for extra notes]"
git push
```
and send a pull request through the github web interface.

# Setting up a new KiCad Project
Create a new KiCad project and git repository to house it.
In the project directory add this repository as a git submodule:

`git submodule add https://github.com/SFUSatClub/KiCad-Lib.git`

In KiCad main window go to Eeschema > Preferences > Component Libraies:
1. "Add" user defined search path, select the KiCad-Lib folder in your project folder
2. "Add" component library files and select the SFUSat.lib file in the KiCad-Lib folder
3. Press ok.

Exit back to the KiCad home window and go to Pcbnew > Preferences > Footprint Libraries Manager > "Project Specific Libraies" tab:
1. "Add Library"
2. Nickname: SFUSat
3. Library Path: ${KIPRJMOD}/KiCad-Lib/SFUSat.pretty
