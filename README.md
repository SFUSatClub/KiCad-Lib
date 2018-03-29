# KiCad-Lib
Schematic and footprint component library for KiCad EDA tool.
Use this library for all satellite KiCad schematic and layouts by adding this repository as a git submodule. Component datasheets should be present in the "Doc" file with the same name as the footprint or symbol that it is associated with.

The stencil aperture (.Paste layer) should be defined by this library. Strencil aperture should be baset off of manufacturer recomemndation or the IPC-7525 Stencil Design Guide.

IPC-SM-782 Surface Mount Design and Land Pattern Standard should be used for SMD footprint design unless component datasheet lists a footprint.

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

Disable global aperture settings by going to PCBNew > Dimentions > Pad Mask Clearence and set:
Solder mask clearence 0.075mm
Solder paste clearence 0mm
Make sure to set the Solder mask min width in accordance with your PCB manufacturer.


#3D Models
Both STEP and WRL files are stored in SFUSat.pretty

The procedure for generating 3D models of boards is complicated due to KiCad not natively supporting export of 3D models. We will use KiCad-Stepup (https://sourceforge.net/p/kicadstepup/wiki/Home/) to perform the following operations: component STEP file -> WRL file -> PCBNew settings -> board STEP file. KiCad-Stepup is a macro written for FreeCad (https://www.freecadweb.org/).

0. change ksu-config.ini: prefix3D_1 = /home/tobi/Cubesat/CubeSat-Radio-v0.1/KiCad-Lib/SFUSat.pretty
1. Load the macro in FreeCAD: Macro > Macros .. > Set Macro Destination > Create > Execute
2. Create new document in freecad
3. Load kicad footprint using the macro
4. Load step file using macro
5. Union the varius compoentns of the 3d model in the model tab of freecad
6. Move the 3D model such that it aligns with the footprint using the kicad-stepup macro interface. Note the orientation of the footprint indicated by the unit vectors in the bottom right of the 3D window.
7. Export to kicad using the macro, use all default values, change the file names to something appropriate, file names for .step and .wrl should be the same, move both files to SFUSat.pretty
8. in PCBnew > footprint properties > 3D settings > Add 3D shape to select the wrl file
9. Confirm the model positioning and file selection usign the PCBnew 3D view
10. Create a new document in freecad, Load Kicad_pcb using kicad-stepup macro
11. Select all geometries you want to export using the model tab.
12. Export to STEP using Export in Freecad