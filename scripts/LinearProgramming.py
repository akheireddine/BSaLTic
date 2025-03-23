import sys
from gurobipy import *
import matplotlib.pyplot as plt
import numpy as np
from plotly import graph_objs as go
from plotly.offline import plot
import numpy.polynomial.polynomial as polynom
from math import ceil,floor


MEDIUM_SIZE = 10
BIGGER_SIZE = 15

LBD_LIMIT   = 23

class ConfigureBMCFilter :
    
    
    def __init__(self,InFileName=None, eventLabel=None, lbdCSVPath=None, OutFileName=None, titlePlot=""):
        self.fileIN = InFileName
        self.fileOUT = OutFileName
        self.eventL = eventLabel
        self.PointsOfClauseType= dict()          #key : clause type {P,M,J,PM,PJ,MJ,PMJ}, value : list of points [(x1,y1),(x2,y2),...]
        self.ClauseType = set()
        self.LBDPoint = dict()
        self.PointViaLBD = dict()
        self.x_var = dict()
        self.m = None
        self.non_dominated_points = list()
        self.title = titlePlot
        self.LBDFilename =  lbdCSVPath+"/"+eventLabel+".csv"
        self.points_solution = dict()
        self.fig = None
        self.InflexionPoints = list()
        self.pointLBDOnly = dict()

        self.PointsLBDApprox = dict()
        self.PointsDerivClasses = dict()

        if InFileName == None :
            print("Error filename input notfound\n")
            exit(1)
        ################# LAUNCH RESOLUTION ################
        self.read_InPut_file()
        self.read_Input_LBD_file(self.LBDFilename)



    def initialize_Information(self,list_point):
        for point in list_point:
            x,y,I,lbd = point
            if I not in self.PointsOfClauseType.keys() :
                self.PointsOfClauseType[I] = list()
                self.LBDPoint[I] = dict()
                self.PointViaLBD[I] = dict()
            self.PointsOfClauseType[I].append((x,y))
            self.LBDPoint[I][(x,y)] = lbd
            self.PointViaLBD[I][lbd] = (x,y)
            self.ClauseType.add(I)

    def read_InPut_file(self):
        with open(self.fileIN) as f :
            lines = f.readlines()
            for row in lines: 
                elem_line = row.split()
                x,y,I,lbd = elem_line
                x = float(x)
                y = float(y)
                lbd = int(lbd)
                if I not in self.PointsOfClauseType.keys() :
                    self.PointsOfClauseType[I] = list()
                    self.LBDPoint[I] = dict()
                    self.PointViaLBD[I] = dict()
                self.PointsOfClauseType[I].append((x,y))
                self.LBDPoint[I][(x,y)] = lbd
                self.PointViaLBD[I][lbd] = (x,y)
                self.ClauseType.add(I)
        
    
    def read_Input_LBD_file(self, lbdFile=None):
        self.pointLBDOnly = dict()
        if lbdFile != None :
            lineLBD = list()
            with open(lbdFile, "r") as f : 
                lineLBD = f.readlines()
            
            for i,l in zip(range(len(lineLBD)), lineLBD):
                p = l.split(" ")
                p[0] = float(p[0])
                p[1] = float(p[1])
                
                self.pointLBDOnly[i+1] = p
        
    def identify_inflexion_point(self,pointLBD=None):
    
        non_dominated_point_sorted = sorted(self.non_dominated_points)
        nb_points = len(non_dominated_point_sorted)
        coeff = None
        OptimalPoint = None

        for i in range(nb_points - 1) :
            p1 = non_dominated_point_sorted[i]
            p2 = non_dominated_point_sorted[i+1]
            
            current_coeff = (p2[1] - p1[1]) / ( p2[0] - p1[0] ) 
            
            if (coeff == None) or (current_coeff - coeff > 2) :
                coeff = current_coeff
            else :
                if pointLBD != None and p1[0] > pointLBD[0] : 
                    OptimalPoint = p1
                    break
        
        return OptimalPoint
    
    def regressionClass(self,fig=None):
        Label = list()
        X = list()
        Y = list()
        for lbd,p in self.pointLBDOnly.items() :
            X.append(p[0])
            Y.append(p[1])
            Label.append(str(lbd))
        poly = np.poly1d(np.polyfit(X, Y,8))
        d1 = poly.deriv(1)
        roots = list(d1.roots)
        roots = [float(r) for r in roots]
        Xapprox = list()
        Yapprox = list()
        YDeriv = list()
        for x in X :
            val = poly(x)
            if val >= 0 and val <= 100 :
                Xapprox.append(x)
                Yapprox.append(val)
                YDeriv.append(d1(x))

        if fig != None :
            fig.add_trace(go.Scatter(
                        x=Xapprox,
                        y=Yapprox,
                        name=r'$Derivation\ Regression\ x^{'+str(poly.order)+'}$',
                        line=dict(color="blue",width=4),
                        mode="lines",
                    ))
            fig.add_trace(go.Scatter(
                        x=X,
                        y=Y,
                        text=Label,
                        marker_symbol="circle",
                        marker_color="blue",
                        marker={"size":12},
                        line=dict(color="blue",width=4),
                        mode="markers",
                    ))

            fig.add_trace(go.Scatter(
                        x=X,
                        y=YDeriv,
                        text=Label,
                        marker_symbol="triangle-up",
                        marker_color="pink",
                        marker={"size":15},
                        mode="markers",
                    ))
            
        self.PointsLBDApprox = {int(lbd): (x,y) for x,y,lbd in zip(Xapprox,YDeriv,Label)}
        
        
        LBD = [str(i) for i in range(1,LBD_LIMIT)]
        colors={"P":"blue","PMJ": "red","J":"pink","M":"green","PM":"purple","PJ":"yellow","MJ":"peru"}
        Labels_I = {"P":r'$C_\mathcal{P}$',"PMJ":r'$C_\mathcal{PMJ}$',"J":"$C_\mathcal{J}$","M":"$C_\mathcal{M}$","PM":r'$C_\mathcal{PM}$',"PJ":r'$C_\mathcal{PJ}$',"MJ":"$C_\mathcal{MJ}$"}
        for c,Plist in self.PointsOfClauseType.items() :
            X = [ p[0] for p in Plist ]
            Y = [ p[1] for p in Plist ]
            poly = np.poly1d(np.polyfit(X, Y,8))
            d1 = poly.deriv(1)
            roots = list(d1.roots)
            roots = [float(r) for r in roots]
            Xapprox = list()
            Yapprox = list()
            YDeriv = list()
            for x in X :
                val = poly(x)
                if val >= 0 and val <= 100 :
                    Xapprox.append(x)
                    Yapprox.append(val)
                    YDeriv.append(d1(x))

            if fig != None :
                fig.add_trace(go.Scatter(
                            x=Xapprox,
                            y=Yapprox,
                            name=Labels_I[c]+" "+r'$Derivation\ Regression\ x^{'+str(poly.order)+'}$',
                            text=Labels_I[c],
                            line=dict(color=colors[c],width=4),
                            mode="lines",
                        ))
                fig.add_trace(go.Scatter(
                            x=X,
                            y=Y,
                            name=Labels_I[c],
                            text=LBD,
                            marker_symbol="circle",
                            marker_color=colors[c],
                            marker={"size":12},
                            line=dict(color=colors[c],width=4),
                            mode="markers",
                        ))
    
                fig.add_trace(go.Scatter(
                            x=X,
                            y=YDeriv,
                            text=LBD,
                            marker_symbol="triangle-up",
                            marker_color=colors[c],
                            marker={"size":15},
                            mode="markers",
                        ))
                
            self.PointsDerivClasses[c] = {int(lbd): (x,y) for x,y,lbd in zip(Xapprox,YDeriv,LBD) }

    def regressionFunction(self,fig=None,pl=None):
        X = list()
        Y = list()
        
        sorted_non_dominated_point = sorted(self.non_dominated_points)
        for p in sorted_non_dominated_point :
            X.append(p[0])
            Y.append(p[1])
            
        poly = np.poly1d(np.polyfit(X, Y, 3))
        roots = list(poly.roots)
        roots = [float(r) for r in roots]
        
        Xapprox = list()
        Yapprox = list()
        for x in X :
            val = poly(x)
            if val >= 0 and val <= 100 :
                Xapprox.append(x)
                Yapprox.append(val)
    
        if fig != None :
            fig.add_trace(go.Scatter(
                        x=roots,
                        y=[poly(r) for r in roots],
                        name="Root points of f'",
                        text="toto",
                        line=dict(color="purple",width=0.0),
                        marker_symbol="x",
                        marker={"size": 20},
                        mode="lines+markers",
                    ))
            fig.add_trace(go.Scatter(
                        x=Xapprox,
                        y=Yapprox,
                        name=r'$Derivation\ Regression\ x^{'+str(poly.order)+'}$',
                        text="toto",
                        line=dict(color="green",width=4),
                        mode="lines",
                    ))
        if pl != None :
            plt.plot(roots,[poly(r) for r in roots],
                color="purple",
                alpha=2,
                marker="X",
                markersize=10,
                linestyle="None",
                label="Root points of f\'",
                )
            plt.plot(Xapprox, Yapprox,
                color="green",
                alpha=0.7,
                label=r'$Derivation\ Regression \ x^{'+str(poly.order)+'}$',
            )
    
    
    def plot_front(self, eventName, outputdir, lbdFile=None, addedText=""):
        plt.rc('axes',  labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
        plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels

        fig, ax = plt.subplots()
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.6)
    
        if (self.pointLBDOnly) != 0 :
            for lbd,p in self.pointLBDOnly.items(): 
                plt.plot(
                    p[0],
                    p[1],
                    color="blue",
                    alpha=0.7,
                    marker="o",
                    markersize=5,
                    linestyle="None",
                    label="set of clauses: LBDx" if lbd == 1 else None,
                )
                
                annotation_lbd = ""
                if lbd < 21 :
                    annotation_lbd = str(lbd)
                elif lbd == 21:
                    annotation_lbd = "]20, 50]"
                elif lbd == 22:
                    annotation_lbd = " > 50"

                plt.annotate(
                    annotation_lbd, #str(lbd), # this is the text
                    (p[0],p[1]),
                    textcoords="offset points", # how to position the text
                    xytext=(10, -3.5), # distance from text to points (x,y)
                    ha="center", # horizontal alignment can be left, right or center
                )

        for p,l in zip(self.non_dominated_points,range(len(self.non_dominated_points))) :
            plt.plot(p[0], p[1],
                color="red",
                alpha=0.7,
                marker="*",
                markersize=5,
                linestyle="--",
                label="Pareto front " if l == len(self.non_dominated_points)-1 else None,
            )
            plt.annotate(
                "",
                (p[0], p[1]),
                textcoords="offset points", # how to position the text
                xytext={
                     4: (0, 0),
                     5: (-8.5, 3.5),
                }.get(10, (-20, 5)), # distance from text to points (x,y)
                ha="center", # horizontal alignment can be left, right or center
            )

        if output is not None:
            plt.xlabel("% of learnt clauses")
            plt.ylabel("% usage in " + eventName + " - "+addedText)
            plt.legend(numpoints=1, markerfirst=False, loc="best")
            plt.savefig(outputdir+"/"+addedText+"-PL-"+eventName+".pdf", format="pdf",  bbox_inches='tight',dpi=500)

            plt.clf()
            plt.cla()

    def initializeModelVariables(self):
        self.m = Model("BestConfigBMC")
        self.m.Params.LogToConsole = 0
        self.m.Params.OutputFlag = 0
        #CREER VARIABLE DU MODELE
        self.x_var = { c : dict() for c in self.ClauseType }

        for cls_type in self.ClauseType :
            i = 0
            for p in self.PointsOfClauseType[cls_type] :
                self.x_var[cls_type][p] =  self.m.addVar(vtype=GRB.BINARY, name="x_"+cls_type+"_"+str(i) )
                i += 1
            
        self.m.update()   

    def addConstraints(self):
        #CREER LES CONTRAINTES DU MODELE
        for cls_type in self.ClauseType : 
        #UN SEUL PARAMETRE POUR CHAQUE TYPE DE CLAUSE
            self.m.addConstr(quicksum([ self.x_var[cls_type][p] for p in self.PointsOfClauseType[cls_type]]),GRB.EQUAL, 1, "ONE_DECISION_FOR_CLS_TYPE_X")

                
    def getOptimalPoint(self):
        x_value = 0
        y_value = 0
        for cls_type in self.ClauseType :
            for p in self.PointsOfClauseType[cls_type] :
                if int(self.x_var[cls_type][p].X) == 1 :
                    x_value += p[0]
                    y_value += p[1]
        return x_value,y_value


    def getSolution(self):
        s=""
#        s = "-------------------------------------------------------\n"
        for cls_type in self.ClauseType :
            for p in self.PointsOfClauseType[cls_type] :
                if int(self.x_var[cls_type][p].X) ==1 :
                    s += cls_type+ " : "+str(self.LBDPoint[cls_type][p])+"\n"
        return s



    def Solve_Model_ParetoFront(self,additionnalConstraints_bis=None):
        OBJ_point = set()
        self.points_solution = dict()
        stop = False
        additionalConstraints = list()
        epsilon = 0.1
        round = 0
        
        while stop == False :
            round += 1
            try:
                self.initializeModelVariables()
                self.addConstraints()
                
                if additionnalConstraints_bis != None :
                    for t,p,b in additionnalConstraints_bis[:-1] : 
                        if p not in self.x_var[t].keys():
                            print("pb value ",p)
                        self.m.addConstr(self.x_var[t][p], GRB.LESS_EQUAL, b, "DO_NOT_CHOOSE_THIS_OPTION")
                    self.m.addConstr(quicksum([ quicksum([ p[1] * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType ]),">", additionnalConstraints_bis[-1][1]+0.01)
                    self.m.addConstr(quicksum([ quicksum([ p[0] * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType ]),">", additionnalConstraints_bis[-1][0]+0.01)

                OPTObj1 = quicksum([ quicksum([ p[0] * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType])
                #ADDITIONAL CONSTRAINTS
                for c in additionalConstraints :
                    self.m.addConstr(OPTObj1, GRB.LESS_EQUAL, c - epsilon, "OPTObj1_"+str(c))

                #FIXER L'OBJECTIVE
                self.m.ModelSense = GRB.MAXIMIZE
                self.m.setObjective( quicksum([ quicksum([ p[1] * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType ]))#, 0,1)
                self.m.update()

                #LANCER LE MODELE
                self.m.optimize()

                if self.m.Status == GRB.OPTIMAL :
                    objValue = self.getOptimalPoint()
                    OBJ_point.add(objValue)
                    self.points_solution[objValue] = self.getSolution()
                    additionalConstraints.append(float(objValue[0]))
                else :
                    print("KO")
                    stop = True
            
            except GurobiError as e:
                print('Error code ' + str(e.errno) + ": " + str(e))
            
            except AttributeError:
                print('Encountered an attribute error')
        
        Pareto_point = list()
        OBJ_point    = list(OBJ_point)
        for l1 in range(len(OBJ_point)) :
            p1_is_dominated = False
            p1 = OBJ_point[l1]
            for l2 in range(len(OBJ_point)) :
                p2 = OBJ_point[l2]
                if (p2[0] < p1[0]) and (p2[1] > p1[1]) :#or ( abs(p2[0]-p1[0]) <= 0.1  and  abs(p2[1]-p1[1]) <= 0.1) :
                    p1_is_dominated = True
                    break
            if p1_is_dominated == False:
                Pareto_point.append(p1)

        return Pareto_point


    def plot_LBD(self, figure,lbdFile=None):
        pointLBD = None
        if lbdFile != None :
            LBD_PointX = list()
            LBD_PointY = list()
            LBD_Annotate = list()
            lineLBD = list()

            with open(lbdFile, "r") as f : 
                lineLBD = f.readlines()
            
            for i,l in zip(range(len(lineLBD)), lineLBD):
                p = l.split(" ")
                p[0] = float(p[0])
                p[1] = float(p[1])
                if i+1 == 3 : 
                    pointLBD = p
                LBD_PointX.append(p[0])
                LBD_PointY.append(p[1])
                LBD_Annotate.append(str(i+1)+ "  ratio="+str(p[1]/p[0]))

            LBDText = [ str(i) for i in range(1,len(LBD_PointX)+1) ]
            figure.add_trace(go.Scatter(
                x=LBD_PointX,
                y=LBD_PointY,
                name="LBD",
                text=LBDText,
                textposition='top left',
                line=dict(color="blue",width=0.2),
                marker_symbol="diamond",
                mode="lines+markers+text"
            ))

    def plot_interactive(self, eventName, outputdir, lbdFile=None,addedText="",reset=True):
        
        if reset :
            self.fig = go.Figure()
            self.plot_LBD(self.fig,lbdFile)

        BMC_PointX = list()
        BMC_PointY = list()
        BMC_Label  = list()

        sorted_non_dominated_point = sorted(self.non_dominated_points)
        for p in sorted_non_dominated_point :
            BMC_PointX.append(p[0])
            BMC_PointY.append(p[1])
            BMC_Label.append(self.points_solution[p] + "   -ratio="+str(p[1]/p[0]))

        self.fig.add_trace(go.Scatter(
            x=BMC_PointX,
            y=BMC_PointY,
            name="Pareto front",
            text=BMC_Label,
            line=dict(color="red",width=0.1),
            marker_symbol="circle",
            mode="lines+markers",
        ))
        # style all the traces
        self.fig.update_traces(
            hoverinfo="name+x+y+text",
            marker={"size": 12},
            showlegend=True
        )
        
        self.fig.update_layout(
            autosize=False,
            width=1000,
            height=1000,
            margin=go.layout.Margin(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad = 4
            ),
            title="Pareto front "+addedText,
            xaxis_title="% of learnt clauses",
            yaxis_title="% usage in "+eventName,
            font=dict(
                size=18,
            )
        )
            
        if reset == False:
            self.fig.show()
        
            self.fig.write_html(outputdir+"/"+addedText+"-PL-"+eventName+".html")
    
    
    def compute_configurationToPoint(self, configuration):
        config = configuration.replace("\n",":")
        config = config.split(":")
        learnt = 0 
        usage  = 0
        for i_c,i_lbd in zip(range(0,len(config),2),range(1,len(config),2)) : 
            classCls = config[i_c].strip()
            lbd = int(config[i_lbd])
            if lbd > len(self.PointViaLBD[classCls]) :
                lbd = len(self.PointViaLBD[classCls]) - 1
            q = self.PointViaLBD[classCls][lbd]
            learnt += float(q[0])
            usage  += float(q[1])
        return (learnt,usage)
    

    def is_dominated(self,point):
        for p in self.non_dominated_points :
            if (p[0] <= point[0])  and  (p[1] >= point[1])  and p != point:
                return True
        return False

    def add_new_solution(self, new, non_dominated_solution):
        old_non_dominated_solution = non_dominated_solution.copy()
        for p1 in old_non_dominated_solution :
            for p2 in old_non_dominated_solution :
                if p2[0] <= p1[0]  and   p2[1] >= p1[1]   and   p2 != p1:
                    non_dominated_solution.remove(p1)

        old_non_dominated_solution = non_dominated_solution
        for p in old_non_dominated_solution:
            if new[0] >= p[0]  and   new[1] <= p[1]   and   p != new:
                return

        non_dominated_solution.add(new)

    def plot_inflexionPoints_of_2Events_interactive(self, otherEvent, plot_fig=False):
        
        fig2 = go.Figure()
        InfPoints1 = sorted(self.non_dominated_points)
        InfPoints2 = sorted(otherEvent.non_dominated_points)
        All_non_domianted_point = set()
        InflectionPointX = list()
        InflectionPointY = list()
        InflectionPointReverseX = list()
        InflectionPointReverseY = list()
        Label = list()
        ratio = list()
        
        self.plot_LBD(fig2,self.LBDFilename)
        self.plot_LBD(fig2,otherEvent.LBDFilename)


        for p in InfPoints1 :
            xval,yval = otherEvent.compute_configurationToPoint(self.points_solution[p])
            if otherEvent.is_dominated((xval,yval)) == False :
                self.add_new_solution(p,All_non_domianted_point)
                otherEvent.points_solution[(xval,yval)] = self.points_solution[p]
                InflectionPointX.append(p[0])
                InflectionPointY.append(p[1])
                Label.append(self.points_solution[p]+"    "+str(p[1]/p[0]))

                InflectionPointReverseX.append(xval)
                InflectionPointReverseY.append(yval)
                ratio.append(self.points_solution[p])

        
        fig2.add_trace(go.Scatter(
            x=InflectionPointX,
            y=InflectionPointY,
            name=self.eventL,
            text=Label,
            line=dict(color="orange",width=0.1),
            marker_symbol="hexagon",
            mode="lines+markers",
            ))
        
        fig2.add_trace(go.Scatter(
            x=InflectionPointReverseX,
            y=InflectionPointReverseY,
            name=self.eventL+" projected into "+otherEvent.eventL,
            text=Label,
            line=dict(color="yellowgreen",width=0.3),
            marker_symbol="cross",
            mode="markers",
            ))
        
        InflectionPointX = list()
        InflectionPointY = list()
        InflectionPointReverseX = list()
        InflectionPointReverseY = list()
        ratio = list()
        Label = list()
        for p in InfPoints2 :
            xval,yval = self.compute_configurationToPoint(otherEvent.points_solution[p])
            if self.is_dominated((xval,yval)) == False :
                self.add_new_solution((xval,yval),All_non_domianted_point)
                self.points_solution[(xval,yval)] = otherEvent.points_solution[p]
                InflectionPointX.append(p[0])
                InflectionPointY.append(p[1])
                Label.append(otherEvent.points_solution[p]+"    "+str(p[1]/p[0]))
            
                InflectionPointReverseX.append(xval)
                InflectionPointReverseY.append(yval)
                ratio.append(otherEvent.points_solution[p])
        
    
        fig2.add_trace(go.Scatter(
            x=InflectionPointX,
            y=InflectionPointY,
            name=otherEvent.eventL,
            text=Label,
            line=dict(color="green",width=0.1),
            marker_symbol="hexagon",
            mode="lines+markers",
            ))

        fig2.add_trace(go.Scatter(
            x=InflectionPointReverseX,
            y=InflectionPointReverseY,
            name=otherEvent.eventL+" projected into "+self.eventL,
            text=Label,
            line=dict(color="orangered",width=0.3),
            marker_symbol="cross-dot",
            mode="markers",
            ))
        

        # style all the traces
        fig2.update_traces(
            hoverinfo="name+x+y+text",
            marker={"size": 12},
            showlegend=True
        )
        
        fig2.update_layout(
            autosize=False,
            width=1000,
            height=1000,
            margin=go.layout.Margin(
                    l=50,
                    r=50,
                    b=100,
                    t=100,
                    pad = 4
            ),
            title="Inflexion points of both Pareto front "+self.title,
            xaxis_title="% of learnt clauses",
            yaxis_title="% usage in both conflict and propagation",
            font=dict(
                size=18,
            )
        )
        
        if plot_fig :
            fig2.show()
    
        return All_non_domianted_point
        

    def Select_Config_approximated_to_PointLBD(self, Points, lbdvalue, prev_class_lbd=None):
        LBDPoint = self.pointLBDOnly[lbdvalue]
        PointsSorted   = sorted(Points)
        points_approx_size = dict()
        ref_size = LBDPoint[0]

        if prev_class_lbd != None :
            for lbd in self.PointViaLBD[prev_class_lbd[0]]:
                if lbd <= prev_class_lbd[1] and lbd < (LBD_LIMIT - 1):
                    PointsSorted.remove(self.PointViaLBD[prev_class_lbd[0]][lbd])
        
        for p in PointsSorted : 
            curr_size = p[0]
            points_approx_size[p] = abs(curr_size - ref_size)

        best_point = min(points_approx_size, key=points_approx_size.get)
        return best_point,self.points_solution[best_point]
    

    def Strategy_with_Recomputation_of_ParetoF(self, otherEvent, plot=False):
        all_non_dominated_points = self.plot_inflexionPoints_of_2Events_interactive(otherEvent, plot_fig=plot)

        ## CORE section
        elected_point,configuration = self.Select_Config_approximated_to_PointLBD(all_non_dominated_points, 3)
        otherEvent_pointValue = otherEvent.compute_configurationToPoint(configuration)
        print("CORE : "+self.eventL+" ("+str(round(elected_point[0],2))+","+str(round(elected_point[1],2))+")     "+otherEvent.eventL+" ("+str(round(otherEvent_pointValue[0],2))+","+str(round(otherEvent_pointValue[1],2))+")")
        print(configuration)
        
        ## TIER-2 section
        elected_point,configuration = self.Select_Config_approximated_to_PointLBD(all_non_dominated_points, 6)
        otherEvent_pointValue = otherEvent.compute_configurationToPoint(configuration)
        print("TIER-2 : "+self.eventL+" ("+str(round(elected_point[0],2))+","+str(round(elected_point[1],2))+")     "+otherEvent.eventL+" ("+str(round(otherEvent_pointValue[0],2))+","+str(round(otherEvent_pointValue[1],2))+")")
        print(configuration)


    def compute_point_configuration(self, eventName, config):
        Class = ["J","M","MJ","P","PJ","PMJ","PM"]

        learnt = 0
        usage  = 0
        for i in range(len(Class)):
            point   = self.PointViaLBD[Class[i]][float(config[i])]
            learnt += point[0]
            usage  += point[1]
            
        print("Configuration for  "+eventName+" : "+str(round(learnt,2))+"  &  "+str(round(usage,2)))


#***********************************************************************************************************************************************

    def constraintLBDWithHighProba(self,lbdmin):
        ratio_of_each_class = dict()
        for cls_type in self.ClauseType : 
            p = self.PointViaLBD[cls_type][LBD_LIMIT - 1]
            ratio_of_each_class[cls_type] = p[1]/p[0]
            
        weights = {c : float(i)/sum(ratio_of_each_class.values()) for c,i in ratio_of_each_class.items()}
        
        for cls_type in self.ClauseType :
            if weights[cls_type] >= 0.2 :
                for lbd in range(1,lbdmin) :
                    p = self.PointViaLBD[cls_type][lbd]
                    self.m.addConstr( self.x_var[cls_type][p] ,GRB.EQUAL, 0, "DO_NOT_CHOOSE_THIS_LBD_VALUE")


    def Solve_Model_Ratio(self,lbd,eps=0.1):
        OBJ_point = set()
        self.points_solution = dict()
        self.non_dominated_points = list()
        stop = False
        epsilon = eps
        round = 0
        
        while stop == False :
            round += 1
            try:
                self.initializeModelVariables()
                self.addConstraints()
                LBDiSize=0
                LBDiUsage=0
                for classe in self.PointsOfClauseType.keys():
                    LBDiSize += self.PointViaLBD[classe][lbd][0]
                    LBDiUsage += self.PointViaLBD[classe][lbd][1]
                    
                self.m.addConstr( quicksum([ quicksum([ p[0] * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType ]), GRB.LESS_EQUAL, LBDiSize - epsilon)
                self.m.addConstr( quicksum([ quicksum([ p[1] * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType ]), GRB.GREATER_EQUAL, LBDiUsage)

                self.constraintLBDWithHighProba(lbd)
                #FIXER L'OBJECTIVE
                self.m.ModelSense = GRB.MAXIMIZE
                self.m.setObjective( quicksum([ quicksum([ (p[1]/p[0]) * self.x_var[t][p] for p in self.PointsOfClauseType[t]]) for t in self.ClauseType ]))#, 0,1)
                self.m.update()

                #LANCER LE MODELE
                self.m.optimize()

                if self.m.Status == GRB.OPTIMAL :
                    objValue = self.getOptimalPoint()
                    if objValue in OBJ_point:
                        stop = True
                    OBJ_point.add(objValue)
                    self.points_solution[objValue] = self.getSolution()
                else :
                    stop = True
            
            except GurobiError as e:
                print('Error code ' + str(e.errno) + ": " + str(e))
            
            except AttributeError:
                stop = True
                print('Encountered an attribute error')
        
        Pareto_point = list()
        OBJ_point    = list(OBJ_point)
        for l1 in range(len(OBJ_point)) :
            p1_is_dominated = False
            p1 = OBJ_point[l1]
            for l2 in range(len(OBJ_point)) :
                p2 = OBJ_point[l2]
                if (p2[0] < p1[0]) and (p2[1] > p1[1]) :#or ( abs(p2[0]-p1[0]) <= 0.1  and  abs(p2[1]-p1[1]) <= 0.1) :
                    p1_is_dominated = True
                    break
            if p1_is_dominated == False:
                Pareto_point.append(p1)

        return Pareto_point


    def MonoLinearProgram_basedOn_Ratio(self,otherEvent,lbd,db) :
        found = False
        for i in reversed(np.arange(0,5.2,0.2)):
            
            self.non_dominated_points = self.Solve_Model_Ratio(lbd,i)
            if len(self.non_dominated_points) != 0 :
                found=True
                # for p in self.non_dominated_points :
                #     configuration_p = self.points_solution[p]
                #     otherEvent_pointValue = otherEvent.compute_configurationToPoint(configuration_p)
                #     print(db+" : "+self.eventL+" ("+str(round(p[0],2))+","+str(round(p[1],2))+")    "+otherEvent.eventL+" ("+str(round(otherEvent_pointValue[0],2))+","+str(round(otherEvent_pointValue[1],2))+")")
                #     print(configuration_p)
                # print("OPTIMAL EPSILON for the "+db+" "+str(i) +" in "+self.eventL)        
                #self.plot_interactive(self.eventL, self.fileOUT,self.LBDFilename,self.title)
                break
        if not found :
            print("Empty Pareto!")
            exit(2)
            
    def BiLinearProgram_basedOn_Size(self,otherEvent, run_solving=False, plot=False):
        if run_solving :
            self.non_dominated_points = self.Solve_Model_ParetoFront()
            otherEvent.non_dominated_points = otherEvent.Solve_Model_ParetoFront()
        self.Strategy_with_Recomputation_of_ParetoF(otherEvent, plot=plot)
    

    def plot_two_points_on_LBD(self, p1, config1, p2, config2) :
        self.fig.add_trace(go.Scatter(
            x=[p1[0]],
            y=[p1[1]],
            name="CORE selector",
            text=config1,
            line=dict(color="red",width=3),
            marker_symbol="star",
            marker_size=15,
            mode="lines+markers",
        ))
        self.fig.add_trace(go.Scatter(
            x=[p2[0]],
            y=[p2[1]],
            name="TIER-2 selector",
            text=config2,
            line=dict(color="red",width=3),
            marker_symbol="star",
            marker_size=15,
            mode="lines+markers",
        ))
        self.fig.show()


    def print_Point(self, p, config, otherEvent, db,lbd=6):
        LBDiSize=0
        LBDiUsage=0
        for classe in self.PointsOfClauseType.keys():
            LBDiSize += self.PointViaLBD[classe][lbd][0]
            LBDiUsage += self.PointViaLBD[classe][lbd][1]
        otherEvent_pointValue = otherEvent.compute_configurationToPoint(config)
        print(self.eventL+" ("+str(round(p[0],2))+","+str(round(p[1],2))+")\n"+otherEvent.eventL+" ("+str(round(otherEvent_pointValue[0],2))+","+str(round(otherEvent_pointValue[1],2))+")\n"+"original ("+str(round(LBDiSize,2))+","+str(round(LBDiUsage,2))+")\n")
        print(config)

if __name__ == '__main__':

    if len(sys.argv[1:]) < 3 : 
        print("Need 4 parameters :\n 1. <repository of csvfiles LBD-BMC-\{propagate,conflict\}.csv>\n 2. <Output path for figures>\n 3. <text title>\n 4. <heuristic: Hf> \n")
        exit(1)

    filename  = sys.argv[1]+"/LBD-BMC-propagate.csv"
    eventName = "propagate"
    filename2 = sys.argv[1]+"/LBD-BMC-conflict.csv"
    eventName2= "conflict"
    lbdcsv    = sys.argv[1]
    output    = sys.argv[2]
    textTitle = sys.argv[3]
    strategy  = sys.argv[4]

    PROPAGATE  = ConfigureBMCFilter(filename, eventName, lbdcsv, output, textTitle)
    CONFLICT   = ConfigureBMCFilter(filename2, eventName2, lbdcsv, output, textTitle)
    
    
    if strategy == "Hf" :
        print("********************************  Hf Heuristic ********************************\n")

        PROPAGATE.MonoLinearProgram_basedOn_Ratio(CONFLICT,3,"CORE")
        Pcore_solution = PROPAGATE.non_dominated_points[0]
        Pcore_configue = PROPAGATE.points_solution[Pcore_solution]
        CONFLICT.MonoLinearProgram_basedOn_Ratio(PROPAGATE,3,"CORE")
        Ccore_solution = CONFLICT.non_dominated_points[0]
        Ccore_configue = CONFLICT.points_solution[Ccore_solution]

        PROPAGATE.MonoLinearProgram_basedOn_Ratio(CONFLICT,6,"TIER2")
        Ptier2_solution = PROPAGATE.non_dominated_points[0]
        Ptier2_configue = PROPAGATE.points_solution[Ptier2_solution]
        CONFLICT.MonoLinearProgram_basedOn_Ratio(PROPAGATE,6,"TIER2")
        Ctier2_solution = CONFLICT.non_dominated_points[0]
        Ctier2_configue = CONFLICT.points_solution[Ctier2_solution]


#        PROPAGATE.MonoLinearProgram_basedOn_Ratio(CONFLICT,6,"TIER2")
#        Ptier2_solution = PROPAGATE.non_dominated_points[0]
#        Ptier2_configue = PROPAGATE.points_solution[Ptier2_solution]
#        CONFLICT.MonoLinearProgram_basedOn_Ratio(PROPAGATE,6,"TIER2")
#        Ctier2_solution = CONFLICT.non_dominated_points[0]
#        Ctier2_configue = CONFLICT.points_solution[Ctier2_solution]

	print("--------------------- CONFLICT-ANALYSIS SOLUTION ---------------------")
        CONFLICT.print_Point(Ctier2_solution,Ctier2_configue,PROPAGATE, "TIER-2",6)
	print("--------------------- UNIT-PROPAGATION  SOLUTION ---------------------")
        PROPAGATE.print_Point(Ptier2_solution,Ptier2_configue, CONFLICT, "TIER-2",6)

        print("\n**********************************************************************************")
