#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import math
import pickle
import matplotlib.pyplot as plt

LIM_LBD = 23
LIM_BMC = 73
LIM_SIZE = 11

MEDIUM_SIZE = 10
BIGGER_SIZE = 15

MAP_LEARNT = "learnt"
MAP_PROPAGATE = "propagate"
MAP_CONFLICT = "conflict"
MAP_TIME = "time"

def parse_and_store(path, solver, out="./"):
    """Read the log files at `path` and create the map:
      {
         file: {
            learnt: [LIM_BMC][LIM_LBD][LIM_SIZE],
            propagate: [LIM_BMC][LIM_LBD][LIM_SIZE],
            conflict: [LIM_BMC][LIM_LBD][LIM_SIZE],
            time: float
         }
      }
      The map is store in the `out` directory as `out`/`solver`.pkl.
   """
    matches = {}
    id = "\d+,"
    # Matching of interesting lines
    for file in os.listdir(path):

        if file.endswith(".log"):
            # Initilisation of the lists

            fd = open(os.path.join(path, file))
            all_file = fd.read()
            fd.close()

            matches[file] = {
                MAP_LEARNT: [
                    [[0] * LIM_SIZE for j in range(LIM_LBD)] for i in range(LIM_BMC)
                ],
                MAP_PROPAGATE: [
                    [[0] * LIM_SIZE for j in range(LIM_LBD)] for i in range(LIM_BMC)
                ],
                MAP_CONFLICT: [
                    [[0] * LIM_SIZE for j in range(LIM_LBD)] for i in range(LIM_BMC)
                ],
                "time": 0,
            }
            win = re.findall("c \[(.*)\] c Winner", all_file, re.M)
            if len(win) == 0:
                win = 6000
            else:
                win = win[0]
                
            matches[file]["time"] = float(win)
            for event, lbd_learnt, bmc, size, count,t in re.findall(
                "^%s(learnt|propagate|conflict),(\d+),\d+,(\d+),(\d+),(\d+),(\d+)$" % id,
                all_file,
                re.M,
            ):
                if "0" in [lbd_learnt, bmc]:
                    continue
                count = int(count)
                lbd_learnt = min(int(lbd_learnt), LIM_LBD) - 1
                bmc = int(bmc) # min(int(communities), LIM_BMC) - 1
                size = min(int(size), LIM_SIZE) - 1
                matches[file][event][bmc][lbd_learnt][size] += count
    afile = open(out + "/" + solver + ".pkl", "wb")
    pickle.dump(matches, afile)
    afile.close()

    return matches

def read_solver(path):
    """Read the map as descibes in `parse_and_store` from the file in `path`
    and return it after deleting the SIZE dimension, eg:
    learnt[LIM_BMC][LIM_LBD][LIM_SIZE] => learnt[LIM_BMC][LIM_LBD]
    """
    afile = open(path, "rb")
    solver = pickle.load(afile)
    for file in solver:
        for event in [MAP_LEARNT, MAP_PROPAGATE, MAP_CONFLICT]:
            for bmc in range(LIM_BMC):
                for lbd in range(LIM_LBD):
                    solver[file][event][bmc][lbd] = sum(solver[file][event][bmc][lbd])
    return solver


def sum_event_matrix(solver, event):
    """ Create a matrix M[LIM_BMC][LIM_LBD] where each case is
    the sum of all the `event` for the corresponding LBD/COM
    combinaison.
    """
    M = [[0] * LIM_LBD for i in range(LIM_BMC)]
    for file in solver:
        for bmc in range(LIM_BMC):
            for lbd in range(LIM_LBD):
                M[bmc][lbd] += solver[file][event][bmc][lbd]
    return M

def line_normalized_matrix(M):

   n_M = [[0] * 11 for i in range(11)]

   for i in range(11):
      max_val = sum(M[i])
      for j in range(11):
         n_M[i][j] = M[i][j] / max_val * 100.

   return n_M

def normalized_matrix_per_volume(solver, event):
    """ Create a matrix M[LIM_BMC][LIM_LBD] where each case is
    the percentage of the corresponding LBD/COM combinaison on
    the set of events.
    """
    M = sum_event_matrix(solver, event)
    new_M = [[0] * LIM_LBD for i in range(LIM_BMC)]
    max_val = sum([sum(row) for row in M])

    if max_val == 0:
        print("Error no event " + event, sys.stderr)
        return new_M

    for bmc in range(LIM_BMC):
        for lbd in range(LIM_LBD):
            new_M[bmc][lbd] = M[bmc][lbd] / max_val * 100.0
    return new_M

def cumsum_matrix(M):
    """ Return a matrix representing the cumulative sum of the matrix 
    M[LIM_BMC][LIM_LBD] per row and per column.
    """
    cs_M = [[0] * LIM_LBD for i in range(LIM_BMC)]

    for i in range(LIM_BMC):
        for j in range(LIM_LBD):
            cs_M[i][j] = M[i][j]
            if i > 0:
                cs_M[i][j] += cs_M[i - 1][j]
            if j > 0:
                cs_M[i][j] += cs_M[i][j - 1]
            if i > 0 and j > 0:
                cs_M[i][j] -= cs_M[i - 1][j - 1]

    return cs_M


def plot_pareto_LBD(cs_learnt, cs_propagate, cs_conflict, output_dir=None):
    """Take the matrice `learnt`[LIM_BMC][LIM_LBD] and `event`[LIM_BMC][LIM_LBD]
    and plot the curve that shows the percentage of event represented by
    a particular volume of clauses.

    `output` is the path of the resulting pdf file. Leaving this paramater set to
    None is useful to plot multiple curve.
    """
    plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels

    fig, ax = plt.subplots()
    
    for event, label, form, output in [(cs_propagate, "Unit propagation", "o", output_dir + "propagation_LBD.pdf"), (cs_conflict, "Conflict analysis", "^", output_dir + "conflict_analysis_LBD.pdf")]:

        for i in range(LIM_LBD - 1):
            plt.plot(
                cs_learnt[LIM_BMC-1][i],
                event[LIM_BMC-1][i],
                color="blue",
                alpha=0.7,
                marker=form,
                markersize=5,
                linestyle="None",
                label=label if i == LIM_LBD - 2 else None,
            )

            if label == "conflict analysis" and i == 0:
               continue
            plt.annotate(
                str(i+1), # this is the text
                (cs_learnt[LIM_BMC-1][i],
                 event[LIM_BMC-1][i]), # this is the point to label
                textcoords="offset points", # how to position the text
                xytext=(10, -3.5), # distance from text to points (x,y)
                ha="center", # horizontal alignment can be left, right or center
            )
        if output is not None:
            plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.6)
            plt.xlabel("% of learnt clauses")
            # plt.xlim(-5, 105)
            # plt.ylabel("% used in " + ("propagation" if event == cs_propagate else "conflict analysis"))
            plt.ylabel(r'% usage in ' + ("propagation" if event == cs_propagate else "conflict analysis"))
            plt.legend(numpoints=1, markerfirst=False, loc="lower right")
            plt.savefig(output, format="pdf",  bbox_inches='tight')
            plt.clf()
            plt.cla()


def plot_pareto_ILBD(learnt, propagate, conflict, log=False, output_dir=None, titlePlot=""):
    """Take the matrice `learnt`[LIM_BMC][LIM_LBD] and `event`[LIM_BMC][LIM_LBD]
    and plot the curve that shows the percentage of event represented by
    a particular volume of clauses.

    `output` is the path of the resulting pdf file. Leaving this paramater set to
    None is useful to plot multiple curve.
    """
    plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels

    colors={1:"blue",2: "red",4:"pink",5:"green",6:"purple",7:"yellow",8:"peru",9:"black"}
    List_filter_I = [1,2,4,5,6,7,8]
    Labels_I = {1:r'$C_\mathcal{P}$',2:r'$C_\mathcal{PMJ}$',4:"$C_\mathcal{J}$",5:"$C_\mathcal{M}$",6:r'$C_\mathcal{PM}$',7:r'$C_\mathcal{PJ}$',8:"$C_\mathcal{MJ}$"}

    for event, form, output in [(propagate, "o", output_dir +titlePlot+"_propagate_LBD-BMC.pdf"), (conflict, "o", output_dir + titlePlot + "_conflict_LBD-BMC.pdf")]:
        fig, ax = plt.subplots()
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.6)
        for bmc in List_filter_I :
            for i in range(LIM_LBD-1):
                if bmc == 1:
                    x_val =  sum([learnt[bmc][i_] + learnt[11][i_] + learnt[12][i_] for i_ in range(i)])
                    y_val =  sum([event[bmc][i_]  + event[11][i_]  + event[12][i_]  for i_ in range(i)])
                    if log :
                        x_val = math.log10(x_val+1)
                        y_val = math.log10(y_val+1)
                    plt.plot(
                        x_val, y_val,
                        color=colors[bmc],
                        alpha=0.7,
                        marker="^",
                        markersize=5,
                        linestyle="--",
                        label=Labels_I[bmc] if i == LIM_LBD-2 else None,
                    )
                    plt.annotate(
                        str(i+1), # this is the text
                        (x_val,y_val),
                        textcoords="offset points", # how to position the text
                        xytext={
                             4: (9, -9),
                             5: (-8.5, 3.5),
                        }.get(bmc, (-10.5, -3.5)), # distance from text to points (x,y)
                        ha="center", # horizontal alignment can be left, right or center
                    )
                elif bmc == 2 :
                    x_val = sum([learnt[bmc][i_] + learnt[21][i_] + learnt[22][i_] for i_ in range(i)])
                    y_val = sum([event[bmc][i_]  + event[21][i_]  + event[22][i_]  for i_ in range(i)])
                    if log :
                        x_val = math.log10(x_val+1)
                        y_val = math.log10(y_val+1)

                    plt.plot(
                        x_val, y_val,
                        color=colors[bmc],
                        alpha=0.7,
                        marker="^",
                        markersize=5,
                        linestyle="--",
                        label=Labels_I[bmc] if i == LIM_LBD-2 else None,
                    )
                    plt.annotate(
                        str(i+1), # this is the text
                        (x_val,y_val),
                        textcoords="offset points", # how to position the text
                        xytext={
                             4: (9, -9),
                             5: (-8.5, 3.5),
                        }.get(bmc, (-10.5, -3.5)), # distance from text to points (x,y)
                        ha="center", # horizontal alignment can be left, right or center
                    )
                elif bmc == 6 :

                    x_val = sum([learnt[bmc][i_] + learnt[61][i_] + learnt[62][i_] for i_ in range(i)])
                    y_val = sum([event[bmc][i_]  + event[61][i_]  + event[62][i_]  for i_ in range(i)])

                    if log :
                        x_val = math.log10(x_val+1)
                        y_val = math.log10(y_val+1)
                    plt.plot(
                        x_val,y_val,
                        color=colors[bmc],
                        alpha=0.7,
                        marker="^",
                        markersize=5,
                        linestyle="--",
                        label=Labels_I[bmc] if i == LIM_LBD-2 else None,
                    )
                    plt.annotate(
                        str(i+1), # this is the text
                        (x_val,y_val),
                        textcoords="offset points", # how to position the text
                        xytext={
                             4: (9, -9),
                             5: (-8.5, 3.5),
                        }.get(bmc, (-10.5, -3.5)), # distance from text to points (x,y)
                        ha="center", # horizontal alignment can be left, right or center
                    )
                elif bmc == 7 :
                    x_val = sum([learnt[bmc][i_] + learnt[71][i_] + learnt[72][i_] for i_ in range(i)])
                    y_val = sum([event[bmc][i_]  + event[71][i_]  + event[72][i_]  for i_ in range(i)])
                    if log :
                        x_val = math.log10(x_val+1)
                        y_val = math.log10(y_val+1)
                    plt.plot(
                        x_val, y_val,
                        color=colors[bmc],
                        alpha=0.7,
                        marker="^",
                        markersize=5,
                        linestyle="--",
                        label=Labels_I[bmc] if i == LIM_LBD-2 else None,
                    )
                    plt.annotate(
                        str(i+1), # this is the text
                        (x_val,y_val),
                        textcoords="offset points", # how to position the text
                        xytext={
                             4: (9, -9),
                             5: (-8.5, 3.5),
                        }.get(bmc, (-10.5, -3.5)), # distance from text to points (x,y)
                        ha="center", # horizontal alignment can be left, right or center
                    )
                else :
                    x_val = sum([learnt[bmc][i_] for i_ in range(i)])
                    y_val = sum([event[bmc][i_] for i_ in range(i)])
                    if log :
                        x_val = math.log10(x_val+1)
                        y_val = math.log10(y_val+1)
                    plt.plot(
                        x_val,y_val,
                        color=colors[bmc],
                        alpha=0.7,
                        marker="^",
                        markersize=5,
                        linestyle="--",
                        label=Labels_I[bmc] if i == LIM_LBD-2 else None,
                    )
                    plt.annotate(
                        str(i+1), # this is the text
                        (x_val,y_val),
                        textcoords="offset points", # how to position the text
                        xytext={
                             4: (9, -9),
                             5: (-8.5, 3.5),
                        }.get(bmc, (-10.5, -3.5)), # distance from text to points (x,y)
                        ha="center", # horizontal alignment can be left, right or center
                    )

        if output is not None:
            plt.xlabel((r'$LOG_{10}$' if log else "") +"% of learnt clauses")
            plt.ylabel((r'$LOG_{10}$' if log else "")+"% usage in " + ("propagation" if event == propagate else "conflict analysis") + " - "+titlePlot)
            plt.legend(numpoints=1, markerfirst=False)
            plt.savefig(output, format="pdf",  bbox_inches='tight',dpi=500)
            plt.clf()
            plt.cla()
            
            


def plot_pareto_ILBD_REFINED(learnt, propagate, conflict, log=False, output_dir=None, titlePlot=""):
    """Take the matrice `learnt`[LIM_BMC][LIM_LBD] and `event`[LIM_BMC][LIM_LBD]
    and plot the curve that shows the percentage of event represented by
    a particular volume of clauses.

    `output` is the path of the resulting pdf file. Leaving this paramater set to
    None is useful to plot multiple curve.
    """
    print("coucou________________________________________********************************************************")
    plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels

    colors={1:"blue",11:"powderblue",12:"cyan",2: "red",21:"indianred",22:"tomato",4:"pink",5:"green",6:"purple",61:"violet",62:"indigo",7:"yellow",71:"orange",72:"khaki",8:"peru",9:"black"}
    List_filter_I = [1,11,12,2,21,22,4,5,6,61,62,7,71,72,8]
    Labels_I = {1:r'$C_\mathcal{P}$',11:r'$C_{\mathcal{P}_{M}}$',12:r'$C_{\mathcal{P}_{J}}$',2:r'$C_\mathcal{PMJ}$',21:r'$C_{\mathcal{P}_{M}MJ}$',22:r'$C_{\mathcal{P}_{J}MJ}$',
                4:"$C_\mathcal{J}$",5:"$C_\mathcal{M}$",6:r'$C_\mathcal{PM}$',61:r'$C_{\mathcal{P}_{M}M}$',62:r'$C_{\mathcal{P}_{J}M}$',7:r'$C_\mathcal{PJ}$',71:r'$C_{\mathcal{P}_{M}J}$',
                72:r'$C_{\mathcal{P}_{J}J}$',8:"$C_\mathcal{MJ}$"}

    for event, form, output in [(propagate, "o", output_dir + "propagate_LBD-BMC.jpeg"), (conflict, "o", output_dir + "conflict_LBD-BMC.jpeg")]:
        fig, ax = plt.subplots()
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.6)
        for bmc in List_filter_I :
            for i in range(LIM_LBD-1):
                x_val = sum([learnt[bmc][i_] for i_ in range(i)])
                y_val = sum([event[bmc][i_] for i_ in range(i)])
                if log :
                    x_val = math.log10(x_val+1)
                    y_val = math.log10(y_val+1)
                plt.plot(
                    x_val,y_val,
                    color=colors[bmc],
                    alpha=0.7,
                    marker="^",
                    markersize=5,
                    linestyle="--",
                    label=Labels_I[bmc] if i == LIM_LBD-2 else None,
                )
                plt.annotate(
                    str(i+1), # this is the text
                    (x_val,y_val),
                    textcoords="offset points", # how to position the text
                    xytext={
                         4: (9, -9),
                         5: (-8.5, 3.5),
                    }.get(bmc, (-10.5, -3.5)), # distance from text to points (x,y)
                    ha="center", # horizontal alignment can be left, right or center
                )

        if output is not None:
            plt.xlabel((r'$LOG_{10}$' if log else "") +"% of learnt clauses")
            plt.ylabel((r'$LOG_{10}$' if log else "")+"% usage in " + ("propagation" if event == propagate else "conflict analysis") + " - "+titlePlot)
            plt.legend(numpoints=1, markerfirst=False)
#            plt.savefig(output, format="pdf",  bbox_inches='tight',dpi=400)
            plt.savefig(output, format="jpeg",  bbox_inches='tight',dpi=500)

            plt.clf()
            plt.cla()





def get_lbd_bmc_points(learnt, event):
    List_filter_I = [1,2,4,5,6,7,8]
    Labels_I = {1:"P",2:"PMJ",4:"J",5:"M",6:"PM",7:"PJ",8:"MJ"}
    points_event = list()
    for bmc in List_filter_I :
        x_val = 0 
        y_val = 0
        for i in range(LIM_LBD):
            if bmc == 1:
                x_val =  sum([learnt[bmc][i_] + learnt[11][i_] + learnt[12][i_] for i_ in range(i)])
                y_val =  sum([event[bmc][i_]  + event[11][i_]  + event[12][i_]  for i_ in range(i)])
            elif bmc == 2 :
                x_val = sum([learnt[bmc][i_] + learnt[21][i_] + learnt[22][i_] for i_ in range(i)])
                y_val = sum([event[bmc][i_]  + event[21][i_]  + event[22][i_]  for i_ in range(i)])

            elif bmc == 6 :
                x_val = sum([learnt[bmc][i_] + learnt[61][i_] + learnt[62][i_] for i_ in range(i)])
                y_val = sum([event[bmc][i_]  + event[61][i_]  + event[62][i_]  for i_ in range(i)])

            elif bmc == 7 :
                x_val = sum([learnt[bmc][i_] + learnt[71][i_] + learnt[72][i_] for i_ in range(i)])
                y_val = sum([event[bmc][i_]  + event[71][i_]  + event[72][i_]  for i_ in range(i)])

            else :
                x_val = sum([learnt[bmc][i_] for i_ in range(i)])
                y_val = sum([event[bmc][i_] for i_ in range(i)])
            if x_val == 0 and y_val == 0 :
#                print("xval yxal",x_val,y_val)
                continue
            points_event.append( (x_val,y_val,Labels_I[bmc],i) )
            
    return points_event


def save_pareto_LBD_for_Linear_Programming(learnt, propagate, conflict, output_dir=None):

    cs_learnt = cumsum_matrix(learnt)
    cs_propagate = cumsum_matrix(propagate)
    cs_conflict = cumsum_matrix(conflict)

    for event_cs, event, eventName in [(cs_propagate, propagate, "propagate"), (cs_conflict, conflict, "conflict")]:
        f = open(output_dir+"/"+eventName+".csv","w")
        for i in range(LIM_LBD - 1):
            f.write(str(cs_learnt[LIM_BMC-1][i])+" "+str(event_cs[LIM_BMC-1][i])+"\n")
        f.close()

        f = open(output_dir+"/LBD-BMC-"+eventName+".csv","w")
        point_event = get_lbd_bmc_points(learnt,event)
        for l in point_event : 
            f.write(str(l[0])+" "+str(l[1])+" "+str(l[2])+" "+str(l[3])+"\n")
        f.close()



def get_lbd_refined_bmc_points(learnt, event):
    Labels_I = {1:"P",11:"Pm",12:"Pj",2:"PMJ",21:"PmMJ",22:"PjMJ",4:"J",5:"M",6:"PM",61:"PmM",62:"PjM",7:"PJ",71:"PmJ",72:"PjJ",8:"MJ"}
    List_filter_I = list(Labels_I.keys())
    points_event = list()
    for bmc in List_filter_I :
        x_val = 0 
        y_val = 0
        for i in range(LIM_LBD):
            x_val = sum([learnt[bmc][i_] for i_ in range(i)])
            y_val = sum([event[bmc][i_] for i_ in range(i)])
            if x_val == 0 and y_val == 0 :
#                print("xval yxal",x_val,y_val)
                continue
            points_event.append( (x_val,y_val,Labels_I[bmc],i) )

    return points_event


def save_pareto_LBD_IREFINED_for_Linear_Programming(learnt, propagate, conflict, output_dir=None):
    """Take the matrice `learnt`[LIM_COM][LIM_LBD] and `event`[LIM_COM][LIM_LBD]
    and plot the curve that shows the percentage of event represented by
    a particular volume of clauses.

    `output` is the path of the resulting pdf file. Leaving this paramater set to
    None is useful to plot multiple curve.
    """

    cs_learnt = cumsum_matrix(learnt)
    cs_propagate = cumsum_matrix(propagate)
    cs_conflict = cumsum_matrix(conflict)

    for event_cs, event, eventName in [(cs_propagate, propagate, "propagate"), (cs_conflict, conflict, "conflict")]:
        f = open(output_dir+"/"+eventName+".csv","w")
        for i in range(LIM_LBD - 1):
            f.write(str(cs_learnt[LIM_BMC-1][i])+" "+str(event_cs[LIM_BMC-1][i])+"\n")
        f.close()

        f = open(output_dir+"/LBD-BMC-"+eventName+".csv","w")
        point_event = get_lbd_refined_bmc_points(learnt,event)
        for l in point_event : 
            f.write(str(l[0])+" "+str(l[1])+" "+str(l[2])+" "+str(l[3])+"\n")
        f.close()




def main(log_path, raw_path, plot_path, option, enable_log, titleText=""):

    ############################ PLOT PARETO EXAMPLE ###########################
    def main_pareto(pathnamePKL, plot_path, option,enable_log):
        solver = read_solver(pathnamePKL)
        learnt = normalized_matrix_per_volume(solver, MAP_LEARNT)
        cs_learnt = cumsum_matrix(learnt)
        propagate = normalized_matrix_per_volume(solver, MAP_PROPAGATE)
        cs_propagate = cumsum_matrix(propagate)
        conflict = normalized_matrix_per_volume(solver, MAP_CONFLICT)
        cs_conflict = cumsum_matrix(conflict)

        if option == "lbd" :
            plot_pareto_LBD(
                    cs_learnt, cs_propagate, cs_conflict, output_dir=plot_path)

        if option == "pl" :
            save_pareto_LBD_for_Linear_Programming(
                    learnt, propagate, conflict, output_dir=plot_path)
        if option == "pl-refined" :
            save_pareto_LBD_IREFINED_for_Linear_Programming(
                    learnt, propagate, conflict, output_dir=plot_path)

        if option == "lbd-bmc-refined" :
            plot_pareto_ILBD_REFINED(
                    learnt, propagate, conflict, log=enable_log, output_dir=plot_path, titlePlot=titleText)

        if option == "lbd-bmc" :
            plot_pareto_ILBD(
                    learnt, propagate, conflict, log=enable_log, output_dir=plot_path, titlePlot=titleText)
            
        
#        if option == "lbd-size" :
#            plot_pareto_ISIZE_REFINED(
#                    learnt, propagate, "sequentiel", output="plot/pareto_maplelog.pdf"
#            )
        
    ########################### PLOT USAGE PER INSTANCE (RAINBOW) ##############
    # Appelez plot_instance en laissant output=None et définir output pour le
    # dernier appel pour avoir toutes les courbes dans le même fichier
#    def main_plot_per_instance():
#        solverName = "seqMapleLOG"
#        solver = read_solver("./raw/" + solverName + ".pkl")
#        event = MAP_CONFLICT
#
#        for event in [MAP_PROPAGATE, MAP_CONFLICT]:
#            for lbd, com, color, output in [
#                # (4, 2, "red", None),
#                # (4, 3, "green", "plot/debit_C23" + event + "_" + solverName + ".pdf"),
#                # (4, 4, "blue", None),
#                (4, 5, "purple_3", "plot/debit_C23_" + event + "_" + solverName + ".pdf"),
#            ]:
#                plot_instance(lbd, com, solver, event, color=color, output=output)

    ######################### PLOT AVEC SCRIPT #################################
    parse_and_store(log_path, "currentLOG", raw_path)
    main_pareto(raw_path+"/currentLOG.pkl", plot_path, option, enable_log)
    
    
    # main_plot_per_instance()
    
    #main_boxplot_usage_rate_parallel()






if __name__ == "__main__":
    if len(sys.argv) < 2 :
        print("Need parameters : \n 1: log path for .log files\n 2: raw path for pkl file\n 3: output plot\n 4: option=lbd, lbd-bmc\n 5: enable LOGarithmic value plot 1 otherwise 0\n")
        exit(1)
    log_path  = sys.argv[1]+"/" #"./res_log_noRefineOfP/others/"
    raw_path  = sys.argv[1]+"/" #"./raw/"
    plot_path = sys.argv[2]+"/" #"./plot/"
    option    = sys.argv[3] #"lbd"
    enable_log = 0 #True if int(sys.argv[5]) > 0 else False 
    titleText = sys.argv[4] #title optional


    main(log_path,raw_path,plot_path,option,enable_log, titleText)




