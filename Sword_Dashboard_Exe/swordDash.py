import dash
from dash import dcc
from dash import html
from dash import dash_table as dt
from dash.dependencies import Input, Output
import plotly.express as px
import webbrowser
import pandas as pd
import numpy as np

#Getting spreadsheet data
sheetid = '1d_sU7knugPopM5QkoDpONIONYGUnal27dvpcP3quHp8'
sheetname = 'Sword Weapon Info Database'
sheetname = sheetname.replace(" ","%20")
gsheet_url = 'https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}'.format(sheetid,sheetname)

#Data into a dataframe
df = pd.read_csv(gsheet_url)
df.drop(index=0,inplace=True)
df.reset_index(drop=True,inplace=True)

#Cleaning the data format and entries
columns = ['Type','Weapons','Attack','Crit','Crit Rate','Crit Dmg (rell to norm dmg)','Blade Instinct','Finesse','Special Mod','Attack 1 MRM','Attack 2 MRM','Attack 3 MRM','Attack 4 MRM','Attack 5 MRM','Bladestorm MRM','Attack 1 Dmg',
          'Attack 2 Dmg','Attack 3 Dmg','Attack 4 Dmg','Attack 5 Dmg','Bladestorm Dmg','Skill Dmg','Attack 1 %','Attack 2 %','Attack 3 %','Attack 4 %','Attack 5 %','Bladestorm %','Passive DoT Rank','Skill Attack','Skill Type',
          'Charge Time','Use Time','Duration - Use Time','Modifier','Combo Time','DoT Cons.','DoT Lvl Slope','Tot Ticks','Tot Time']
for colind,col in enumerate(df.columns):
    df.rename(columns={col:columns[colind]}, inplace=True)
	
for rowind,row in enumerate(df['Type']):
    if not pd.isna(row):
        curr_type = row
    else:
        df['Type'][rowind] = curr_type
		
pd.set_option("display.max_columns",None)

#Function to simulate the game
def SWORDOPTDPS(swordType,finesse, damage,skillCooldownVals, skillType, skillCooldown,useTime,duration,modifier,
                dotConstant,dotSlope,dotTicks,dotTime,level, finalTime,skip3 = False,skip4 = False,
                skip5=False,bsCooldown = 0, time = 0,currDmg = 0):
    
    skillCooldownVals = np.array(skillCooldownVals)
    skillCooldownVals/=finesse
    
    #Define some useful variables
    
    #Variables describing a skill's damage over time
    dotTimer = 0
    tickTimer = 0
    tickDmg = dotConstant + dotSlope * level
    
    #Track the attacks that are done
    attacks = [0,0,0,0,0,0,0]
    buffedAttacks = [0,0,0,0,0,0,0]
    
    #Form the animation time lists of attacks
    if "Cutlass" in swordType:
        attackTimes = [.7,.75,1.25,1.6,2,4.2,useTime]
    elif "Broadsword" in swordType:
        attackTimes = [.9,1,1,1,1.4,4.2,useTime]
    elif "Sabre" in swordType:
        attackTimes = [.45,.4,1,1,1.6,4.2,useTime]
    
    ####PRELIMINARIES DONE
    
    ####BEGIN ATTACK SIMULATION
    
    ######Notes
    ##Break attacks use cooldowns between 0 and 1 to represent the portion of bar left to fill
        ##i.e. 0 means it is ready to use, 1 is completely empty
    ##Cooldown skill use time between 0 and max cooldown
    
    ##Adjust start if using buffing skill
    if duration > 0:
        #This occurs for weapons with a "buff" skill that lasts for some time
        #Assume we just used the skill as this will be optimal to be buffed up at the start

        if "Break" in skillType:
            currSkillCooldown = 1
        elif "Cooldown" in skillType:
            currSkillCooldown = finesse * skillCooldown - useTime
        
        durationTimer = duration #Already accounts for the usetime in database
        attacks[6] += 1 #technically used it at the start
    else:
        #Not a buff skill on the sword
        #Start with skill and no buffs
        currSkillCooldown = 0
        durationTimer = 0
        
    #More variables
    currAttInd = 0 #What stage in combos sequence we are at
    #Determine the values for the combo based on what isn't skipped
    attackSequence = [0,1,2,3,4]
    if skip3:
        attackSequence.remove(2)
    if skip4:
        attackSequence.remove(3)
    if skip5:
        attackSequence.remove(4)
    currAtt = attackSequence[currAttInd] #What attack in combos we are at

    ##Basically just a shorthand for later usage
    
    #####START SIM
    
    #print("Start")
    #print("Curr Dmg:",currDmg,"  time:",time)
    while (time < finalTime):
        attackTimeTracker = time #For DoT if needed
        
        #NO SKILL OR SKILL ON COOLDOWN
        if ("None" in skillType or (currSkillCooldown > 0)):
            #Determine if should use BS or combo next
            attDPS = (currDmg + damage[currAtt])/(time+attackTimes[currAtt])
            bsDPS = (currDmg + damage[5])/(time+attackTimes[5])
            
            ##BS WINS
            if attDPS < bsDPS and bsCooldown <=0:
                #print("BS")
                attackNum = 5
                currAttInd = 0
                currAtt = attackSequence[currAttInd] #Reset the combo
                bsCooldown = 30*finesse - attackTimes[5] #put BS on cooldown
            #NORMAL WINS
            else:
                #print("Normal")
                attackNum = currAtt
                bsCooldown -= attackTimes[currAtt]
                if currAtt >= attackSequence[-1]:
                    #If using the last in combo
                    currAttInd = 0
                    currAtt = attackSequence[0]
                else:
                    currAttInd += 1
                    currAtt = attackSequence[currAttInd]
            #Now stuff for either one
            time+=attackTimes[attackNum] #increment time from using attack
            #If we're buffed provide buff damage
            if (durationTimer > 0):
                buffedAttacks[attackNum] += 1
                currDmg += modifier*damage[attackNum]
            else:
                attacks[attackNum] += 1
                currDmg += damage[attackNum]
            #reduce the buff time duration by attack time
            durationTimer -= attackTimes[attackNum]
            if ("Cooldown" in skillType):
                currSkillCooldown -= attackTimes[attackNum]
            elif "Break" in skillType:
                currSkillCooldown -= skillCooldownVals[attackNum]

        #SKILL OFF COOLDOWN, USABLE
        elif currSkillCooldown <= 0:
            ##FIRST GET THE DPS IF IT IS USED
            #THEN USE THE HIGHEST ONE AND ADJUST VARIABLES FROM USING IT
            
            ##DPS if we used these
            attDPS = (currDmg+damage[currAtt])/(time+attackTimes[currAtt])
            bsDPS =  (currDmg + damage[5])/(time+attackTimes[5])
            
            #Get skill DPS
            #First get it for buff skills
            if duration > 0 and durationTimer <= 0: #I.e. buff has a duration and we're not currently under its effects 
                #Assume we use it and recurse back
                tempbsCooldown = bsCooldown - attackTimes[6]
                if time+attackTimes[6]+duration > finalTime:
                    skillDmg = finalTime*SWORDOPTDPS(swordType,finesse, damage,skillCooldownVals,
                                skillType,skillCooldown,useTime,duration,modifier,dotConstant,
                                dotSlope,dotTicks,dotTime, level, finalTime,skip3,skip4,skip5,
                                tempbsCooldown, time+attackTimes[6],currDmg)
                    skillDPS = skillDmg/(finalTime)
                    skillFinalTime = finalTime
                else:
                    skillDmg = (time+attackTimes[6]+duration)*SWORDOPTDPS(swordType,finesse, damage, skillCooldownVals,
                                skillType,skillCooldown,useTime,duration,modifier,dotConstant,
                                dotSlope,dotTicks,dotTime, level,time+attackTimes[6]+duration,skip3,skip4,skip5,
                                tempbsCooldown, time+attackTimes[6],currDmg)
                    skillDPS = skillDmg/(time+attackTimes[6]+duration)
                    skillFinalTime = time+attackTimes[6]+duration
            #Now for non-buff skills
            #Isn't that so much easier!
            else:
                skillDPS = (currDmg + damage[6])/(time+attackTimes[6])
                
            ###Determine what to do
            
            #Only use bladestorm if it happens to be usable AND is the best
            if bsDPS >= attDPS and bsDPS >= skillDPS and bsCooldown <=0:
                #print("BS")
                #Use the bladestorm
                attackNum = 5
                currAttInd = 0
                currAtt = attackSequence[currAttInd] #Reset the combo
                bsCooldown = 30*finesse - attackTimes[5] #put BS on cooldown
            #Ok bladestorm is out, now between attack dps and skill dps
            elif skillDPS > attDPS and duration <= 0:
                #print("Skill")
                #Actually use the skill
                attackNum = 6
                bsCooldown -= attackTimes[6]
                currAttInd = 0
                currAtt = attackSequence[currAttInd]
                #Deal with DoT effects
                dotTimer = dotTime
                if dotTicks != 0:
                    tickTimer = (dotTime/dotTicks)
            else:
                #print("Normal")
                #Combos win
                attackNum = currAtt
                bsCooldown -= attackTimes[currAtt]
                if currAtt == attackSequence[-1]:
                    #If using the last in combo
                    currAttInd = 0
                    currAtt = attackSequence[0]
                else:
                    currAttInd += 1
                    currAtt = attackSequence[currAttInd]
            
            #Now stuff for either one
            time+=attackTimes[attackNum] #increment time from using attack
            #If we're buffed provide buff damage
            if (durationTimer > 0):
                buffedAttacks[attackNum] += 1
                currDmg += modifier*damage[attackNum]
            else:
                attacks[attackNum] += 1
                currDmg += damage[attackNum]
            #reduce the buff time duration by attack time
            durationTimer -= attackTimes[attackNum]
            
            if attackNum != 6:
                #Didn't use skill, adjust normally
                #Adjust skill cooldowns from attack
                if ("Cooldown" in skillType):
                    currSkillCooldown -= attackTimes[attackNum]
                elif "Break" in skillType:
                    currSkillCooldown -= skillCooldownVals[attackNum]
            elif attackNum == 6:
                #Did use the skill
                #Adjust accordingly
                if ("Cooldown" in skillType):
                    currSkillCooldown = skillCooldown*finesse - attackTimes[6]
                elif "Break" in skillType:
                    if duration > 0:
                        durationTimer = duration
                    currSkillCooldown = 1

        #Ok we've chosen our attack/skill for this loop
        
        #Now do DoT ticks for the amount of time spent
        #Doing this particular attack
        #print("PreTick")
        ##print("Curr Dmg:",currDmg,"  time:",time)
        #print(dotTimer,tickTimer)
        if time < finalTime:
            dotEndTime = time
        else:
            dotEndTime = finalTime
        if (dotTimer != 0):
            #Still time on total DoT
            dotTimer -= (dotEndTime-attackTimeTracker)
            tickTimer -= (dotEndTime-attackTimeTracker)
            #Perform damage if decide the time has passed on the next tick
            if (tickTimer <= 0 and dotTicks != 0): ##evaluated we need to do a tick of damage
                currDmg += tickDmg
                tickTimer += dotTime/dotTicks #adjust to next tick time
            if (dotTimer < 0): #Implies gone past time of duration of DoT, so set to 0
                dotTimer = 0
                tickTimer = 0
        #print("PostTick")
        #print("Curr Dmg:",currDmg,"  time:",time)
            
        
    #OUTSIDE OF THE WHILE LOOP NOW
        #print("Curr Dmg:",currDmg,"  time:",time)
    DPS = currDmg/finalTime #average damage per second, choose finalTime since enemy will be dead by this time, can't do damage after
    return DPS

#Function to simulate poison damage over time
def poisonDoT(rank,level):
    #Poison rank and level determine overall damage
    #Level increases with slope
    #Rank determines constant and slope
    
    #Since the ticks are once per second, its DPS is just the damage
    #So we can just add this at the end
    if rank == 3:
        dmg = 7.5+2.75*level
    elif rank == 2:
        dmg = 2+1.75*level
    else:
        dmg = 0
    return dmg
	
#Simple function to return the weapon multiplier
def modifiers(attack,crit, BI, SM):
    return 1.5*(1+.03*attack)*crit*BI*SM
	
#Helper function to get the total sword DPS
#Calling the simulation * modifiers adding in poison
def extractDPS(df,rownum,level,finalTime,skip3 = False, skip4=False,skip5=False):
    m = modifiers(df["Attack"][rownum],df["Crit"][rownum],df["Blade Instinct"][rownum],df["Special Mod"][rownum])
    dps = SWORDOPTDPS(df["Type"][rownum],df["Finesse"][rownum],[df["Attack 1 Dmg"][rownum],df["Attack 2 Dmg"][rownum],
                    df["Attack 3 Dmg"][rownum],df["Attack 4 Dmg"][rownum],df["Attack 5 Dmg"][rownum],df["Bladestorm Dmg"][rownum],
                    df["Skill Dmg"][rownum]],[df["Attack 1 %"][rownum],df["Attack 2 %"][rownum],df["Attack 3 %"][rownum],
                    df["Attack 4 %"][rownum],df["Attack 5 %"][rownum],df["Bladestorm %"][rownum],0],df["Skill Type"][rownum],
                    df["Charge Time"][rownum], df["Use Time"][rownum], df["Duration - Use Time"][rownum],df["Modifier"][rownum],
                    df["DoT Cons."][rownum],df["DoT Lvl Slope"][rownum],df["Tot Ticks"][rownum],df["Tot Time"][rownum],level,
                    finalTime,skip3,skip4,skip5,0,0,0)
    poisonDPS = poisonDoT(df["Passive DoT Rank"][rownum],level)
    finalDPS = dps*m + poisonDPS
    return finalDPS

#Function to extract DPS with times from 1 to 30 second values
#Returns dataframe
def timelineDPS(df,level,skips):

    #Get skipvals
    bool3 = False
    bool4 = False
    bool5 = False
    for skip in skips:
        if "3" in skip:
            bool3 = True
        elif "4" in skip:
            bool4 = True
        elif "5" in skip:
            bool5 = True
    timeDF = pd.DataFrame()
    for rownum in range(len(df)):
        weaponName = df["Weapons"][rownum]
        dpsList = []
        for time in range(1,32):
            dpsList.append(extractDPS(df,rownum,level,time,skip3=bool3,skip4=bool4,skip5=bool5))
        timeDF[weaponName] = dpsList
    return timeDF

#The dashboard application
#Presents two of the same graph and options
#So the user may compare differing graphs of DPS vs time
#Baseline Graph
    
app = dash.Dash(__name__)
app.layout = html.Div([
    ##LEFT SIDE GRAPH
    html.Div([
        ##Graph
        dcc.Graph(id='DPS vs Time 1'),
        #Sword Picker
        html.Div([
            "Swords To Graph",
            dcc.Dropdown(
                id='sword-dropdown 1', clearable=False,
                value='Top 10', options=[{'label':y, 'value':y} for x in [["Top 5","Top 10","All"],timelineDPS(df,1,[]).columns.sort_values()] for y in x]
                )
        ],style = {'padding-bottom':'10px','padding-top':'10px'}),
        #Skip values picker
        html.Div([
            "Combo Attacks To Skip",
            dcc.Checklist(
                id='skip-list 1',
                value=[], options=[{'label':'Skip 3rd', 'value':'Skip 3rd'},{'label':'Skip 4th', 'value':'Skip 4th'},{'label':'Skip 5th', 'value':'Skip 5th'}]
                )
        ],style = {'padding-bottom':'10px','padding-top':'10px'})
    ], style = {'width': '49%', 'height' : '33%','display': 'inline-block'}),

    #RIGHT SIDE GRAPH
    html.Div([
        dcc.Graph(id='DPS vs Time 2'),
        #Sword Picker
        html.Div([
            "Swords To Graph",
            dcc.Dropdown(
                id='sword-dropdown 2', clearable=False,
                value='Top 10', options=[{'label':y, 'value':y} for x in [["Top 5","Top 10","All"],timelineDPS(df,1,[]).columns.sort_values()] for y in x]
                )
        ],style = {'padding-bottom':'10px','padding-top':'10px'}),
        #Skip values picker
        html.Div([
            "Combo Attacks To Skip",
            dcc.Checklist(
                id='skip-list 2',
                value=[], options=[{'label':'Skip 3rd', 'value':'Skip 3rd'},{'label':'Skip 4th', 'value':'Skip 4th'},{'label':'Skip 5th', 'value':'Skip 5th'}]
                )
        ],style = {'padding-bottom':'10px','padding-top':'10px'})
    ],style={'width': '49%', 'height' : '33%','float': 'right','display': 'inline-block'}),

    #LEVEL DROPDOWN
    html.Div([
        "Enemy Level",
        dcc.Dropdown(
            id='level-dropdown', clearable=False,
            value='50', options=[{'label':y, 'value':y} for y in range(1,51)]
        )
    ],style = {'padding-bottom':'10px','padding-top':'10px'}),
    ##TIME SLIDER
    html.Div([
        "Graph Time Endpoints",
        dcc.RangeSlider(
        id = 'time-range',
        min = 1,
        max = 30,
        step = 1,
        value = [1,30],
        marks = dict(enumerate([str(i) for i in range(0,31)]))
        )
    ],style = {'padding-bottom':'20px','padding-top':'10px'}),

    #LEFT AVG TABLE
    html.Div([
        dt.DataTable(
            id='avgtbll',
            data = [],
            columns = [{"name":"Weapon","id":"sword"},{"name":"Left Graph Avg DPS","id":"mean"}]
        )
    ],style = {'width': '49%', 'display': 'inline-block'}),

    #RIGHT AVG TABLE
    html.Div([
        dt.DataTable(
            id='avgtblr',
            data = [],
            columns = [{"name":"Weapon","id":"sword"},{"name":"Right Graph Avg DPS","id":"mean"}]
        )
    ],style = {'width': '49%', 'float':'right','display': 'inline-block','padding-top':'15px'}),
])


#OUTPUTS
#Graphs
@app.callback(
    [Output('DPS vs Time 1', 'figure'),Output('DPS vs Time 2', 'figure')],
    [Input("level-dropdown", "value"),
    Input('time-range','value'),
    Input('sword-dropdown 1','value'),
    Input('sword-dropdown 2','value'),
    Input('skip-list 1','value'),
    Input('skip-list 2','value')])


def update_DPS_Fig(level,time_range,swords,swords2,skips,skips2):
    #Dataframe
    swordInputs = [swords,swords2]
    skipInputs = [skips,skips2]
    timeDFList = [timelineDPS(df,int(level),skip) for skip in skipInputs]
    #Time range 1 to 30
    graphs = []
    for listIndex in range(0,2):
        xtime = [i for i in range(1,len(timeDFList[listIndex])+1)]
        #Find the y columns to use
        if swordInputs[listIndex] == "Top 10":
            avg = timeDFList[listIndex].mean().sort_values(ascending=False)
            ycols = list(avg[0:10].index)
        elif swordInputs[listIndex] == "Top 5":
            avg = timeDFList[listIndex].mean().sort_values(ascending=False)
            ycols = list(avg[0:5].index)
        elif swordInputs[listIndex] == "All":
            ycols = list(timeDFList[listIndex].columns.sort_values())
        else:
            ycols = [str(swordInputs[listIndex])]
        graph = px.line(timeDFList[listIndex],x=xtime,y=ycols,labels={"value":"DPS","x":"Time (s)","variable":"Sword"})
        graph.update_xaxes(range = time_range)
        rangemin = time_range[0]
        rangemax = time_range[1]
        #Those define the rows to check through
        ymax = 0
        ymin = 999999
        #Since time_range is fixed up by 1 to help fit the plot
        #better, muust dec the min and max down 1
        #when searching through the rows in the df
        for rownum in range(rangemin-1,rangemax):
            for weapon in ycols:
                if ymax < timeDFList[listIndex][weapon][rownum]:
                    ymax = timeDFList[listIndex][weapon][rownum]
                if timeDFList[listIndex][weapon][rownum] < ymin:
                    ymin = timeDFList[listIndex][weapon][rownum]
        #Should have the max value in the time frame selected for all weapons
        #Update graph
        graph.update_yaxes(range = [ymin,ymax])
        graphs.append(graph)
    return graphs

#Tables
@app.callback(
    [Output('avgtbll', 'data'),Output('avgtblr', 'data')],
    [Input("level-dropdown", "value"),
    Input('time-range','value'),
    Input('sword-dropdown 1','value'),
    Input('sword-dropdown 2','value'),
    Input('skip-list 1','value'),
    Input('skip-list 2','value')])


def update_table(level,time_range,swords,swords2,skips,skips2):
    #Dataframe
    swordInputs = [swords,swords2]
    skipInputs = [skips,skips2]
    timeDFList = [timelineDPS(df,int(level),skip) for skip in skipInputs]
    #Find the y columns to use
    tables=[]
    for listIndex in range(0,2):
        #Find the y columns to use
        if swordInputs[listIndex] == "Top 10":
            avg = timeDFList[listIndex].mean().sort_values(ascending=False)
            ycols = list(avg[0:10].index)
        elif swordInputs[listIndex] == "Top 5":
            avg = timeDFList[listIndex].mean().sort_values(ascending=False)
            ycols = list(avg[0:5].index)
        elif swordInputs[listIndex] == "All":
            ycols = list(timeDFList[listIndex].columns.sort_values())
        else:
            ycols = [str(swordInputs[listIndex])]
        avg = []
        for col in ycols:
            avg.append(timeDFList[listIndex][col].mean())

        subsetDF = timeDFList[listIndex][ycols]
        avgs = list(subsetDF.mean())
        avgDF = pd.DataFrame(data = [avgs],columns = [ycols],index = ['mean'])
        avgDF = avgDF.transpose()
        avgDF['sword'] = avgDF.index
        tables.append(avgDF.to_dict(orient='records'))
    return tables

##Run it

if __name__ == '__main__':
	port = 8050
	webbrowser.open_new("http://localhost:{}".format(port))
	app.run_server(port=port)