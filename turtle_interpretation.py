import bpy
import re
from math import radians
from mathutils import Vector, Matrix

from lindenmaker import turtle
from lindenmaker.turtle_interpretation_error import TurtleInterpretationError
import imp
imp.reload(turtle)
    
def interpret(lstring, default_length = 2.0, 
                       default_width = 0.5,
                       default_width_growth_factor=1.05,
                       default_angle = 45.0,
                       default_materialindex = 0):
    """Create graphical representation of L-string via Turtle Interpretation. NOTE: Commands that are not supported will be ignored and not raise an error."""
    
    t = turtle.Turtle(default_width, default_materialindex)
    
    # remove all whitespace
    lstring = "".join(lstring.split())
    # apply cut branch commands
    lstring = applyCuts(lstring)
    # split into command symbols with optional parameters
    # e.g. "F(230,24)F[+(45)F]F" will yield ['F(230,24)', 'F', '[', '+(45)', 'F', ']', 'F']
    commands = re.findall(r"[^()](?:\([^()]*\))?", lstring)
    
    for cmd in commands:
        
        args = extractArgs(cmd)
        
        if cmd[0] == 'F':
            # move turtle and draw internode between old and new position
            if len(args) == 2:
                t.draw_internode_module(length=args[0], width=args[1])
                t.move(stepsize=args[0])
            elif len(args) == 1:
                t.draw_internode_module(length=args[0])
                t.move(stepsize=args[0])
            elif len(args) == 0:
                t.draw_internode_module(default_length)
                t.move(default_length)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command 'F' (move turtle and draw).\n"
                      "Usage: 'F' or 'F(step_size)' or 'F(step_size, width)'")
        elif cmd[0] == 'f':
            # move turtle
            if len(args) == 1:
                t.move(stepsize=args[0])
            elif len(args) == 0:
                t.move(default_length)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command 'f' (move turtle).\n"
                      "Usage: 'f' or 'f(step_size)'")
        
        elif cmd[0] == '[':
            # push current turtle state to stack
            if len(args) == 0:
                t.push()
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '['"
                      " (push current turtle state to stack).\n"
                      "Usage: '['")
        elif cmd[0] == ']':
            # restore turtle state from stack
            if len(args) == 0:
                t.pop()
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command ']'"
                      " (restore turtle state from stack).\n"
                      "Usage: ']'")
        
        # rotate commands (turn, pitch, roll)
        elif cmd[0] == '+':
            if len(args) == 1:
                t.turn(-args[0])
            elif len(args) == 0:
                t.turn(-default_angle)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '+' (turn left).\n"
                      "Usage: '+' or '+(angle_degree)'")
        elif cmd[0] == '-':
            if len(args) == 1:
                t.turn(args[0])
            elif len(args) == 0:
                t.turn(default_angle)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '-' (turn right).\n"
                      "Usage: '-' or '-(angle_degree)'")
        elif cmd[0] == '&':
            if len(args) == 1:
                t.pitch(-args[0])
            elif len(args) == 0:
                t.pitch(-default_angle)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '&' (pitch down).\n"
                      "Usage: '&' or '&(angle_degree)'")
        elif cmd[0] == '^':
            if len(args) == 1:
                t.pitch(args[0])
            elif len(args) == 0:
                t.pitch(default_angle)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '^' (pitch up).\n"
                      "Usage: '^' or '^(angle_degree)'")
        elif cmd[0] == '\\':
            if len(args) == 1:
                t.roll(-args[0])
            elif len(args) == 0:
                t.roll(-default_angle)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '\\' (roll right).\n"
                      "Usage: '\\' or '\\(angle_degree)'")
        elif cmd[0] == '/':
            if len(args) == 1:
                t.roll(args[0])
            elif len(args) == 0:
                t.roll(default_angle)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '/' (roll left).\n"
                      "Usage: '/' or '/(angle_degree)'")
        elif cmd[0] == '|':
            if len(args) == 0:
                t.turn(180)
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '|' (turn halfway around).\n"
                      "Usage: '|'")
        
        # drawing attributes
        elif cmd[0] == '_':
            # increase linewidth or set to value
            if len(args) == 1:
                t.linewidth = args[0]
            elif len(args) == 0:
                t.linewidth *= default_width_growth_factor
            else: 
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '_' (increase or set linewidth).\n"
                      "Usage: '_' or '_(width)'")
        elif cmd[0] == '!':
            # decrease linewidth or set to value
            if len(args) == 1:
                t.linewidth = args[0]
            elif len(args) == 0:
                t.linewidth *= 1-(default_width_growth_factor-1)
            else:
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '!' (decrease or set linewidth).\n"
                      "Usage: '!' or '!(width)'")
            t.linewidth = max(t.linewidth, 0.0001)
        elif cmd[0] == ';':
            # increase materialindex or set to value
            if len(args) == 1:
                t.materialindex = max(int(args[0]), 0)
            elif len(args) == 0:
                t.materialindex += 1 # if exceeds mat count, turtle adds new mats
            else:
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command ';'"
                      " (increase or set material index).\n"
                      "Usage: ';' or ';(materialindex)'")
        elif cmd[0] == ',':
            # decrease materialindex or set to value
            if len(args) == 1:
                t.materialindex = int(args[0])
            elif len(args) == 0:
                t.materialindex -= 1
            else:
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command ','"
                      " (decrease or set material index).\n"
                      "Usage: ',' or ',(materialindex)'")
            t.materialindex = max(t.materialindex, 0)
        
        # draw custom object
        elif cmd[0] == '~':
            if len(args) == 4:
                t.draw_module_from_custom_object(objname=args[0],
                                                 objscale=Vector((args[1], args[2], args[3])))
            elif len(args) == 2:
                t.draw_module_from_custom_object(objname=args[0], 
                                                 objscale=Vector((args[1], args[1], args[1])))
            elif len(args) == 1:
                t.draw_module_from_custom_object(objname=args[0])
            else:
                raise TurtleInterpretationError(
                      "Invalid number of arguments for command '~' (draw custom object).\n"
                      "Usage: '~(\"Object\")' or '~(\"Object\", scale)'"
                      " or '~(\"Object\", scale_x, scale_y, scale_z)'")

    t.root.matrix_world *= Matrix.Rotation(radians(-90), 4, 'Y') # rotate object to stand upright
    t.root.name = "Root" # changed to "Root.xxx" on name collision
    bpy.context.scene.last_interpretation_result_objname = t.root.name
    
def applyCuts(lstring):
    """Remove branch segments following a cut command ('%') until their end of branch (i.e. until next unmatched closing bracket or end of string"""
    segments_to_cut = []
    searching_end_of_branch = False
    bracketBalance = 0
    cut_start = cut_end = None
    # find start and end of all segments to cut
    for i, c in enumerate(lstring):
        if searching_end_of_branch:
            # look for unmatched right bracket (end of branch to cut)
            if c == '[':
                bracketBalance += 1
            elif c == ']':
                bracketBalance -= 1
            if bracketBalance < 0:
                searching_end_of_branch = False
                bracketBalance = 0 
                cut_end = i
                segments_to_cut.append((cut_start, cut_end))
        elif c == '%':
            # found start of segment to cut
            searching_end_of_branch = True
            cut_start = i
    # no closing bracket found, thus cut until end of string
    if searching_end_of_branch:
        segments_to_cut.append((cut_start, len(lstring)+1))
    # cut segments
    result = lstring
    for (start, end) in segments_to_cut:
        result = result[:start] + '%'*(end-start) + result[end:]
    return result.replace('%', '')

def extractArgs(command):
    """Return a list of the arguments of a command statement, e.g. A(arg1, arg2, .., argn) will return [arg1, arg2, .., argn]"""
    argstring_list = re.findall(r"\((.+)\)", command)
    if len(argstring_list) == 0:
        return []
    result = []
    for arg in re.split(',', argstring_list[0]):
        try:
            result.append(float(arg)) # try to cast to float
        except ValueError:
            result.append(arg) # else just add string argument
    return result