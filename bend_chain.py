cr = """

#Copyright (c) 2014-2021, Noad Animation Limited
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of Curious Animal Limited nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL CURIOUS ANIMAL LIMITED BE LIABLE FOR ANY
#DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import c4d
import c4d.utils
from c4d import gui
import math

#These multi-line strings are going to be put into our rig's Python tag later
pythontagcode = """#bendchain tagcode""" + cr + """
import c4d
import math

def main():
    bend = op.GetObject()
    if bend.GetType() != c4d.Obend:
        return None
    prevbend = op[c4d.ID_USERDATA,1]
    if prevbend==None:
        return None
    if prevbend.GetType() != c4d.Obend:
        return None
    prevbend[c4d.DEFORMOBJECT_ANGLE] = 0.0
    offset = op[c4d.ID_USERDATA,2]
    rotation = op[c4d.ID_USERDATA,3]

    prevlength = prevbend[c4d.DEFORMOBJECT_SIZE].y
    prevstrength = prevbend[c4d.DEFORMOBJECT_STRENGTH]
    mtx = c4d.Matrix()
    if(prevstrength != 0.0):
        #calculate circle properties
        prevcircleportion = prevstrength / (2.0 * math.pi)
        prevcircumference = prevlength / prevcircleportion
        prevradius = prevcircumference / (2.0 * math.pi)
        #origin
        prevorigin = c4d.Vector()
        prevorigin.x = prevradius
        prevorigin.y = -prevlength / 2
        #bend end point
        prevendpoint = c4d.Vector()
        prevendpoint.x = prevorigin.x - (prevradius * math.cos(prevstrength))
        prevendpoint.y = prevorigin.y + (prevradius * math.sin(prevstrength))

        #rotation matrix based on previous bend strength
        mtx = c4d.utils.MatrixRotZ(prevstrength)
        #rotation matrix from tag's 'Rotation' user data setting
        mtx2 = c4d.utils.MatrixRotY(rotation)
        #new position - move along in 'rotation' direction from end point
        newpos = prevendpoint + (c4d.Vector(0.0, (bend[c4d.DEFORMOBJECT_SIZE].y * 0.5) + offset, 0.0) * mtx)
        mtx = prevbend.GetMg() * mtx * mtx2
    else:
        #if strength is 0 the calculations are much simpler
        mtx = c4d.utils.HPBToMatrix(c4d.utils.MatrixToHPB(prevbend.GetMg())) * c4d.utils.MatrixRotY(rotation)
        newpos = c4d.Vector()
        newpos.y = (prevlength / 2) + (bend[c4d.DEFORMOBJECT_SIZE].y / 2) + offset
    mtx.off = newpos * prevbend.GetMg()
    bend.SetMg(mtx)
    bend.Message(c4d.MSG_UPDATE)"""

#Create a new rig from scratch
def new_rig(object):
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, object)

    #create a Python tag and attach it to the first joint
    pythontag = c4d.BaseTag(c4d.Tpython)
    object.InsertTag(pythontag)
    doc.AddUndo(c4d.UNDOTYPE_NEW, pythontag)
    #set the Python code inside the tag
    pythontag[c4d.TPYTHON_CODE] = pythontagcode

    #add a 'link' field to the python tag's user data -
    #this link will determine which previous bend to attach to
    userdata_link = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BASELISTLINK)
    userdata_link[c4d.DESC_NAME] = "Previous Bend"
    pythontag.AddUserData(userdata_link)

    #add an offset field to the user data
    userdata_offset = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    userdata_offset[c4d.DESC_NAME] = "Offset"
    pythontag.AddUserData(userdata_offset)

    #add an offset field to the user data
    userdata_rotation = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
    userdata_rotation[c4d.DESC_NAME] = "Rotation"
    userdata_rotation[c4d.DESC_UNIT] = c4d.DESC_UNIT_DEGREE
    userdata_rotation[c4d.DESC_STEP] = math.pi / 180.0
    pythontag.AddUserData(userdata_rotation)

    return pythontag

def getTagsByType(tags, tagtype):
    newtags = []
    for tag in tags:
        if tag.GetType() == tagtype:
            newtags.append(tag)
    return newtags

#returns a list with objects of only the selected type
def filterlist(originallist, objecttype):
    newlist = []
    for op in originallist:
        if op.GetType() == objecttype:
            newlist.append(op)
    return newlist

def main():
    oplist = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)

    #Quit early if nothing is selected
    if len(oplist)==0:
        print('Please apply the "bend chain" script to a Bend object.')
        gui.MessageDialog('Please apply the "bend chain" script to a Bend object.')
        return None

    oplist = filterlist(oplist, c4d.Obend)

    #apply the rig to selected bend objects
    rigcount = 0
    existingcount = 0
    doc.StartUndo()
    for index, op in enumerate(oplist):
        applytag = True

        #Test for existing rig - if there is one, don't add the tag again
        #The test looks for any Python tag starting with the teststring ("#bendchain tagcode")
        pythontags = getTagsByType(op.GetTags(), c4d.Tpython)
        teststring = "#bendchain tagcode"

        rigtag = None

        for tag in pythontags:
            if tag[c4d.TPYTHON_CODE][:len(teststring)]==teststring:
                applytag = False
                existingcount += 1
                rigtag = tag
                break

        #If there isn't already a rig, create one
        if applytag:
            rigtag = new_rig(op)
            rigcount += 1

        #currently the rig only works if 'Keep Y-Axis Length' is on, so we set that here
        op[c4d.BENDOBJECT_KEEPYAXIS] = True

        #If this isn't the first selected bend, set the 'Previous Bend' user data
        #to the bend that was selected before this one - you can quickly create a
        #chain of linked bends this way
        if(index > 0):
            rigtag[c4d.ID_USERDATA,1] = oplist[index - 1]

    doc.EndUndo()
    if rigcount == 0 and existingcount == 0:
        print('Please apply the "bend chain" script to a Bend object.')
        gui.MessageDialog('Please apply the "bend chain" script to a Bend object.')
        return None
    else:
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        msg = "Bend chain rig added " + str(rigcount) + " times!"
        if existingcount>0:
            msg += " Rig already exists on " + str(existingcount) + " bend objects."
        print(msg)

if __name__=='__main__':
    main()
