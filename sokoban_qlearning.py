# import
import numpy as np
import math
import random
import time

# input & transSign 
'''
# (hash) Wall
_ (space) empty space
. (period) Empty goal
@ (at) Player on floor
+ (plus) Player on goal 
$ (dollar) Box on floor
* (asterisk) Box on goal  
'''
def loadMap():
    global numRows, numColumns, numBoxs, orgPlayerX, orgPlayerY, orgReached, playerX, playerY, reached
    from google.colab import files
    uploaded = files.upload()
    for file in uploaded.keys():
        f = open(file, 'r')
    # f = open("sokoban00.txt",'r')
        # numRows numColumns
        line = f.readline()
        s = line.split(' ')
        numRows = int(s[0])
        numColumns = int(s[1])
        # buildMap
        gameMap = np.chararray((numRows,numColumns))
        gameMap[:] = ' '    
        # nWallSquares
        line = f.readline()
        s = line.split(' ')
        for i in range(1,int(s[0])+1):
            gameMap[int(s[2*i-1])-1][int(s[2*i])-1] = '#'
        # nBoxes
        line = f.readline()
        s = line.split(' ')
        numBoxs = int(s[0])
        for i in range(1,int(s[0])+1):
            #print(i, int(s[2*i-1])-1, int(s[2*i])-1)
            gameMap[int(s[2*i-1])-1][int(s[2*i])-1] = '$'
        # nStorageLocations
        line = f.readline()
        s = line.split(' ')
        for i in range(1,int(s[0])+1):
            if(gameMap[int(s[2*i-1])-1][int(s[2*i])-1] == b'$'):
                gameMap[int(s[2*i-1])-1][int(s[2*i])-1] = '*'
                reached += 1
            else:
                gameMap[int(s[2*i-1])-1][int(s[2*i])-1] = '.'
        # playerLoc
        line = f.readline()
        s = line.split(' ')
        playerX = int(s[0]) - 1
        playerY = int(s[1]) - 1
        if(gameMap[int(s[0])-1][int(s[1])-1] == b'.'):
            gameMap[int(s[0])-1][int(s[1])-1] = '+'
        else:
            gameMap[int(s[0])-1][int(s[1])-1] = '@'
        orgPlayerX = playerX
        orgPlayerY = playerY
        orgReached = reached
        f.close()
    return gameMap


# qNode
class CqNode:
    state, action = None, None
    def __init__(self, state, action):
        self.state = state
        self.action = action

    def __eq__(self, anotherNode):
        if (not isinstance(anotherNode, CqNode)):
            print("not Cqnode instance.")
            return False
        if (self.state.is_equal_state(anotherNode.state) and self.action == anotherNode.action):
            return True
        else:
            return False

    def __hash__(self): # Record the location of boxes and the player in string, and calculate its hash code.
        posStr = ''
        posStr += str(self.action)
        for i in range(numRows):
            for j in range(numColumns):
                if self.state.map[i][j] == b'$' or self.state.map[i][j] == b'*':
                    posStr += str(i)
                    posStr += str(j)
                elif self.state.map[i][j] == b'@' or self.state.map[i][j] == b'+':
                    tmpPlayerX, tmpPlayerY = i, j
        posStr += str(tmpPlayerX) + str(tmpPlayerY)
        return hash(posStr)

# state
class Cstate:
    map = None
    def __init__(self, inputGameMap):
        self.map = inputGameMap.copy()

    def is_goal_state(self):
        if get_box_on_goal_num() != boxNum:
            return False
        return True

    def is_equal_state(self, state1):
        if (not isinstance(state1, Cstate)):
            return False
        for i in range(numRows):
            for j in range(numColumns):
                if self.map[i][j] == b'$' or self.map[i][j] == b'*' or\
                self.map[i][j] == b'+' or self.map[i][j] == b'@':
                    if self.map[i][j] != state1.map[i][j]: # Comparision based on boxes'/player's position
                        return False
        return True

    def get_box_on_goal_num(self):
        boxOnGoalNum = 0
        for i in range(numRows):
            for j in range(numColumns):
                if self.map[i][j] == b'*':
                    boxOnGoalNum += 1
        return boxOnGoalNum

    def get_state_map(self):
        return self.map

    def get_nearest_box_loc_list(self, i, j):
        direcs=[[-1,0],[1,0],[0,-1],[0,1]]
        boxLocList = []
        origLoc = (i,j)
        visited = set([origLoc])
        que = [origLoc]
        while que:
            i, j = que.pop(0)
            for di, dj in direcs:
                newi, newj = i+di, j+dj
                if 0<=newi<numRows and 0<=newj<numColumns and (newi, newj) not in visited and map[newi][newj] != b'#':
                    if self.map[newi][newj] == b'$' or self.map[newi][newj] == b'*':
                        boxLocList.append((newi,newj))
                    else:
                        que.append((newi, newj))
                    visited.add((newi, newj))
        return boxLocList

# Calculate the # of reachble area of a certain box given the map & playerLoc.
# Suppose we do not move the player. All the calculation are based on the current playerLoc.
def cal_box_reachable_area(map, boxLoc, playerLoc):
    direcs=[[-1,0],[1,0],[0,-1],[0,1]]
    que = [boxLoc]
    visited = set([boxLoc])
    reachableAreaNum = 1
    containGoal = False
    goalLocs = []
    while que:
        i, j = que.pop()
        if map[i][j] == b'.':
            containGoal = True
            goalLocs.append((i,j))
        for di, dj in direcs:
            i_push, j_push = i-di, j-dj
            i_next, j_next = i+di, j+dj
            if 0<=i_push<numRows and 0<=j_push<numColumns and\
                0<=i_next<numRows and 0<=j_next<numColumns and\
                (map[i_next][j_next] == '' or map[i_next][j_next] == b'.') and\
                (i_next, j_next) not in visited and\
                reachable((i_push,i_push), playerLoc):
                    que.append((i_next, j_next))
                    visited.add((i_next, j_next))
                    reachableAreaNum += 1
    return reachableAreaNum, containGoal, goalLocs

# Check if the player can reach the boxLoc
def reachable(map, boxLoc, playerLoc):
    direcs=[[-1,0],[1,0],[0,-1],[0,1]]
    visited = set([playerLoc])
    que = [playerLoc]
    while que:
        i, j = que.pop(0)
        for di, dj in direcs:
            newi, newj = i+di, j+dj
            if 0<=newi<numRows and 0<=newj<numColumns and (newi, newj) not in visited and\
                map[newi][newj] != b'#' and map[newi][newj] != b'$' and map[newi][newj] != b'*':
                    if newi == playerLoc[0] and newj == playerLoc[1]:
                        return True
                    visited.add((newi, newj))
                    que.append((newi, newj))
    return False

def is_deadlock(current_state):
    deadlock = False

    # case 1: wall side
    # If (the front of the moved box is wall) and (more boxes than goals are next to the wall)
    goal_num, box_num = 0, 0
    for a in range(0, numRows):
        if current_state[a][1] == b'.' or current_state[a][1] == b'+':
            goal_num += 1
        elif current_state[a][1] == b'$':
            box_num += 1
        elif current_state[a][1] == b'#':
            if goal_num < box_num: # if the box num is greater than goal_num in a corner surrounded by walls
                return True
            goal_num, box_num = 0, 0

    goal_num, box_num = 0, 0
    for a in range(0, numRows):
        if current_state[a][numColumns-2] == b'.' or current_state[a][1] == b'+':
            goal_num += 1
        elif current_state[a][numColumns-2] == b'$':
            box_num += 1
        elif current_state[a][numColumns-2] == b'#':
            if goal_num < box_num: # if the box num is greater than goal_num in a corner surrounded by walls
                return True
            goal_num, box_num = 0, 0

    goal_num, box_num = 0, 0
    for c in range(0, numColumns):
        if current_state[1][c] == b"." or current_state[1][c] ==b'+':
            goal_num += 1
        elif current_state[1][c] == b'$':
            box_num += 1
        elif current_state[1][c] == b'#':
            if goal_num < box_num: # if the box num is greater than goal_num in a corner surrounded by walls
                return True
            goal_num, box_num = 0, 0

    goal_num = 0
    box_num = 0
    for c in range(0, numColumns):
        if current_state[numRows-2][c] == b"." or current_state[numRows-2][c] == b'+':
            goal_num += 1
        elif current_state[numRows-2][c] == b'$':
            box_num += 1
        elif current_state[numRows-2][c] == b'#':
            if goal_num < box_num: # if the box num is greater than goal_num in a corner surrounded by walls
                return True
            goal_num, box_num = 0, 0

    for i in range(1, numRows-1):
        for j in range(1, numColumns-1):
            if current_state[i][j] == b'$':
                # store the eight directions' situation of a box
                up_wall = bool(current_state[i - 1][j] == b'#')
                up_box = bool(current_state[i - 1][j] == b'$' or current_state[i - 1][j] == b'*')
                down_wall = bool(current_state[i + 1][j] == b'#')
                down_box = bool(current_state[i + 1][j] == b'$' or current_state[i + 1][j] == b'*')
                left_wall = bool(current_state[i][j - 1] == b'#')
                left_box = bool(current_state[i][j - 1] == b'$' or current_state[i][j - 1] == b'*')
                right_wall = bool(current_state[i][j + 1] == b'#')
                right_box = bool(current_state[i][j + 1] == b'$' or current_state[i][j + 1] == b'*')
                up_left_wall = bool(current_state[i - 1][j - 1] == b'#')
                up_left_box = bool(current_state[i - 1][j - 1] == b'$' or current_state[i - 1][j - 1] == b'*')
                down_left_wall = bool(current_state[i + 1][j - 1] == b'#')
                down_left_box = bool(current_state[i + 1][j - 1] == b'$' or current_state[i + 1][j - 1] == b'*')
                up_right_wall = bool(current_state[i - 1][j - 1] == b'#')
                up_right_box = bool(current_state[i - 1][j - 1] == b'$' or current_state[i - 1][j - 1] == b'*')
                down_right_wall = bool(current_state[i + 1][j + 1] == b'#')
                down_right_box = bool(current_state[i + 1][j + 1] == b'$' or current_state[i + 1][j + 1] == b'*')

                # case 2: block
                # If the moved box attached L-shaped boxes/walls and formed a 2x2 block
                if (up_wall or up_box) and (up_left_wall or up_left_box) and (left_wall or left_box):
                    deadlock = True
                elif (up_wall or up_box) and (up_right_wall or up_right_box) and (right_wall or right_box):
                    deadlock = True
                elif (down_wall or down_box) and (down_left_wall or down_left_box) and (left_wall or left_box):
                    deadlock = True
                elif (down_wall or down_box) and (down_right_wall or down_right_box) and (right_wall or right_box):
                    deadlock = True
                
                # case 3:
                # If the moved box shaped a L-shaped block with two walls
                elif up_wall and (left_wall or right_wall):
                    deadlock = True
                elif down_wall and (left_wall or right_wall):
                    deadlock = True
            else:
                pass

    return deadlock

# QLearn(callee)
import random
def FindAct(origState):
    actions = []
    x = playerX
    y = playerY
    state = origState.map
    # Up
    if(x-1 >= 0):
        if(state[x-1][y] == b'$' or state[x-1][y] == b'*'):
        # Push
            if(x-2 >= 0):
                if(state[x-2][y] != b'#' and state[x-2][y] != b'$' and state[x-2][y] != b'*'): # if there is no wall or box next to box.
                    actions.append(1)
        else:
        # Move
            if(state[x-1][y] != b'#'):
                actions.append(5)
    # Down
    if(x+1 < numRows):
        if(state[x+1][y] == b'$' or state[x+1][y] == b'*'):
        # Push
            if(x+2 < numRows):
                if(state[x+2][y] != b'#' and state[x+2][y] != b'$' and state[x+2][y] != b'*'):
                    actions.append(2)
        else:
        # Move
            if(state[x+1][y] != b'#'):
                actions.append(6)
    # Left
    if(y-1 >= 0):
        if(state[x][y-1] == b'$' or state[x][y-1] == b'*'):
        # Push
            if(y-2 >= 0):
                if(state[x][y-2] != b'#' and state[x][y-2] != b'$' and state[x][y-2] != b'*'):
                    actions.append(3)
        else:
        # Move
            if(state[x][y-1] != b'#'):
                actions.append(7)
    # Right
    if(y+1 < numColumns):
        if(state[x][y+1] == b'$' or state[x][y+1] == b'*'):
        # Push
            if(x+2 < numRows):
                if(state[x][y+2] != b'#' and state[x][y+2] != b'$' and state[x][y+2] != b'*'):
                    actions.append(4)
        else:
        # Move
            if(state[x][y+1] != b'#'):
                actions.append(8)
    return actions

def getRandAct(state, actions):
    global qTable
    r = random.choice(actions)
    return r

def getOptAct(state, actions):
    global qTable
    optAct = actions[0]
    max = -math.inf
    for act in actions:
        tmpNode = CqNode(state, act)
        if tmpNode not in qTable:
            qTable[tmpNode] = -1.0 # insert a new node with default
        val = qTable[tmpNode]
        if(val > max):
            max = val
            optAct = act
    return optAct

def Move(origState, action, i, j):
    # Push UpDownLeftRight	1/2/3/4
    # Move UpDownLeftRight	5/6/7/8
    # rewardList = [100.0, -100.0, 1000.0, -1000.0] # OnTarget/OffTarget/AllOnTargets/Deadlock
    global playerX, playerY, reached
    x = playerX
    y = playerY
    reward = -3.0
    situ = 0
    state = origState.map.copy()
    # remove player
    if(state[x][y] == b'@'):
        # leave the space
        state[x][y] = ' '
    else:
        # leave the goal+
        state[x][y] = '.'

    if(action==1):
    # Push Up
        playerX -= 1
        if(state[x - 1][y] == b'$'):
            if(state[x - 2][y] == b'.'):
                # OnTarget
                state[x - 2][y] = b'*'
                state[x - 1][y] = b'@' 
                reward = rewardList[0]
                reached += 1
                if(reached==numBoxs):
                    situ = 1
            else:
                # space
                state[x - 2][y] = '$'
                state[x - 1][y] = '@'
        else:
        # BoxOnTarget*
            if(state[x - 2][y] == b'.'):
                # OnTarget
                state[x - 2][y] = '*'
                state[x - 1][y] = '+'
            else:
                # OffTarget
                state[x - 2][y] = '$'
                state[x - 1][y] = '+'
                reward = rewardList[1]
                reached -= 1
        # check dead&situ        
        if(is_deadlock(state)):
            reward = rewardList[3]
            situ = -1        
    elif(action==2): 
    # Push Down
        playerX += 1
        if(state[x + 1][y] == b'$'):
            if(state[x + 2][y] == b'.'):
                # OnTarget
                state[x + 2][y] = '*'
                state[x + 1][y] = '@'
                reward = rewardList[0]
                reached += 1
                if(reached==numBoxs):
                    situ = 1
            else:
                # space
                state[x + 2][y] = '$'
                state[x + 1][y] = '@'
        else:
        # BoxOnTarget*
            if(state[x + 2][y] == b'.'):
                # OnTarget
                state[x + 2][y] = '*'
                state[x + 1][y] = '+'
            else:
                # OffTarget
                state[x + 2][y] = '$'
                state[x + 1][y] = '+'
                reward = rewardList[1]
                reached -= 1
        # check dead&situ
        if(is_deadlock(state)):
            reward = rewardList[3]
            situ = -1
    elif(action==3):
    # Push Left
        playerY -= 1
        if(state[x][y - 1] == b'$'):
            if(state[x][y - 2] == b'.'):
                # OnTarget
                state[x][y - 2] = '*'
                state[x][y - 1] = '@'
                reward = rewardList[0]
                reached += 1
                if(reached==numBoxs): 
                    situ = 1
            else:
                # space
                state[x][y - 2] = '$'
                state[x][y - 1] = '@'
        else:
        # BoxOnTarget*
            if(state[x][y - 2] == b'.'):
                # OnTarget
                state[x][y - 2] = '*'
                state[x][y - 1] = '+'
            else:
                # OffTarget
                state[x][y - 2] = '$'
                state[x][y - 1] = '+'
                reward = rewardList[1]
                reached -= 1
        # check dead&situ
        if(is_deadlock(state)):
            reward = rewardList[3]
            situ = -1
    elif(action==4):
    # Push Right
        playerY += 1
        if(state[x][y + 1] == b'$'):
            if(state[x][y + 2] == b'.'):
                # OnTarget
                state[x][y + 2] = '*'
                state[x][y + 1] = '@'
                reward = rewardList[0]
                reached += 1
                if(reached==numBoxs):
                    situ = 1
            else:
                # space
                state[x][y + 2] = '$'
                state[x][y + 1] = '@'
        else:
        # BoxOnTarget*
            if(state[x][y + 2] == b'.'):
                # OnTarget
                state[x][y + 2] = '*'
                state[x][y + 1] = '+'
            else:
                # OffTarget
                state[x][y + 2] = '$'
                state[x][y + 1] = '+'
                reward = rewardList[1]
                reached -= 1
        # check dead&situ
        if(is_deadlock(state)):
            reward = rewardList[3]
            situ = -1
    elif(action==5):
    # Move Up
        playerX -= 1
        if(state[x - 1][y] == b'.'):
            # leave the space
            state[x - 1][y] = '+'
        else:
            state[x - 1][y] = '@'
    elif(action==6):
    # Move Down
        playerX += 1
        if(state[x + 1][y] == b'.'):
            # leave the space
            state[x + 1][y] = '+'
        else:
            state[x + 1][y] = '@'
    elif(action==7):
    # Move Left
        playerY -= 1
        if(state[x][y - 1] == b'.'):
            # leave the space
            state[x][y - 1] = '+'
        else:
            state[x][y - 1] = '@'
    elif(action==8):
    # Move Right
        playerY += 1
        if(state[x][y + 1] == b'.'):
            # leave the space
            state[x][y + 1] = '+'
        else:
            state[x][y + 1] = '@'
    else:
        pass
    newState = Cstate(state)
    return newState, reward, situ
  
def getNextMaxQ(nextState, prevAct):
    global qTable
    legalActions = FindAct(nextState)
    legalActions = delDup(legalActions, prevAct)
    max = -math.inf
    for act in legalActions:
        tmpNode = CqNode(nextState, act)
        if tmpNode not in qTable:
            qTable[tmpNode] = -1.0
        val = qTable[tmpNode]
        if(val > max):
            max = val
    return max

def delDup(actions, prevAct):
    if prevAct > 4:
        if prevAct%2: # 5or7
            toDel = prevAct + 1
        else: # 6or8
            toDel = prevAct - 1        
        if toDel in actions:
            actions.remove(toDel)
    return actions

# QLearn(core)
def QLearning():
    global alpha, epsilon, minMoves, playerX, playerY, reached, qTable
    situ = 0
    for i in range(0,epochLimit):
        prevAct = 0
        path = ""
        BoxPath = []
        alpha = 0.8
        epsilon = 0.9
        state = initState   
        prevState = initState  
        playerX = orgPlayerX
        playerY = orgPlayerY
        reached = orgReached
        for j in range(0,actionLimit):
            alpha = max(min_alpha, alpha*decay)
            epsilon = max(min_epsilon, epsilon*decay)
            # selAct
            legalActions = FindAct(state)
            legalActions = delDup(legalActions, prevAct)
            if(len(legalActions) == 0):
                # updateQVal
                tmpNode = CqNode(prevState, prevAct)
                origQVal = qTable[tmpNode]
                reward = -50.0
                qVal = origQVal + alpha * (reward - origQVal)
                qTable[tmpNode] = qVal
                legalActions.append(5)
                if prevAct%2: # 5or7
                    legalActions.append(prevAct + 1)
                else: # 6or8
                    legalActions.append(prevAct - 1)
            rand = random.random()            
            optAct = getOptAct(state, legalActions)
            randAct = getRandAct(state, legalActions)
            if(rand <= epsilon):
                action = randAct
            else:
                action = optAct
            # path += action
            if(action%4 == 1):
                path += 'U'
            elif(action%4 == 2):
                path += 'D'
            elif(action%4 == 3):
                path += 'L'
            else:
                path += 'R'
            # getMaxQandR
            nextState, reward, situ = Move(state, action, i, j)
            nextMaxQ = getNextMaxQ(nextState, action)
            tmpNode = CqNode(state, action)

            # updateQVal
            origQVal = qTable[tmpNode]
            qVal = origQVal + alpha * (reward + gamma * nextMaxQ - origQVal)
            qTable[tmpNode] = qVal
            
            #situ 0:none, 1:done, -1: deadlock
            if(situ == -1):
                break
            elif(situ == 1):
                return path
            else:
                prevState = state
                state = nextState
                prevAct = action
    return path

# para
alpha = 0.8
gamma = 0.9
decay = 0.9
epsilon = 0.9
min_alpha = 0.3
min_epsilon = 0.2
rewardList = [100.0, -100.0, 1000.0, -1000.0] # OnTarget/OffTarget/AllOnTargets/Deadlock
epochLimit = 10000
actionLimit = 5000
numRows = 0
numColumns = 0
numBoxs = 0
orgPlayerX = 0
orgPlayerY = 0
orgReached = 0
playerX = 0
playerY = 0
reached = 0

# main
# execute
gameMap = loadMap()
initState = Cstate(gameMap)
qTable = { } # qTable dict
start = time.time()
bestPath = QLearning()
runTime = time.time() - start
print(runTime//60, "min", runTime%60, "sec")
print(len(bestPath), bestPath)