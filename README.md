# C4D Bend Chain
Link two or more Cinema 4D Bend Deformers in a chain that will automatically follow each other when their 'Strength' settings are animated.
Updated to Python 3 for C4D R23.

## Installation
Copy the Python file to your Cinema 4D library/scripts folder, restart or open Cinema 4D.

## Use
Select two or more Bend Deformers, run the script! (In C4D R23 you can run scripts from the 'Extensions' > 'User Scripts' menu)

The script will apply the rig and link the bends in the order they were selected.

The added Python script tag has further settings to control the rig:
1) Previous Bend - linked to the bend this deformer will follow
2) Offset - moves this bend forwards/backwards in the space of the previous bend
3) Rotation - rotate this bend around the axis of the previous bend

### Notes: 
* the Bend Deformer 'Angle' setting doesn't work with this rig, so the applied Python code sets it to 0.
* because Bend Deformers bend everything forwards of the bend there's a limit to how flexible you can make your bend chain - eg if the first bend is at 180 degrees, subsequent bends are likely to unintentionally bend geometry that was behind the first bend. For these cases you'll need to use Fields to limit the effect.

## Licence
Modified BSD - available in the .py file
