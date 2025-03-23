
import sys

def parse_model_variables(filename):
    
    map_vars = dict()            # key : variable name, value : number of bit it took at most
    signed_vars = set()           
    process = False                    
    with open(filename,"r") as f:
        lines = f.readlines()
        
        for l in lines :
            if "c " in l :
                continue  
            if ":" in l :
                varname,vtype = l.split(":")
                
                if "_p" in varname :
                    process=True
                    continue
                
                varname = varname.replace(" ","")
                varname = varname.replace("\n","")
                
                if  "boolean" in vtype :
                    map_vars[varname] = [1]
                elif "signed word" in vtype :
                    map_vars[varname] = list(range(32))
                    signed_vars.add(varname)
                    
                elif "{" in vtype :
                    ltype = vtype.replace(" ","")
                    ltype = ltype.replace("\n","")
                    ltype = ltype.replace("{","")
                    ltype = ltype.replace("}","")
                    ltype = ltype.split(",")
                    #if ltype[0].isdigit() :
                    #    nmax = [i for i in range(int(ltype[-1]))]
                    #    map_vars[varname] = nmax
                    #else :
                    map_vars[varname] = list(ltype)
                    
    print_map(map_vars, signed_vars, process)
    
    
def print_map(map_vars, signed_vars, process_on) :
    res = ""
    for k,v in map_vars.items():
        if len(v) == 1 : 
            res += str(k)+" "
        else :
            for i in v :
                if process_on :
                    res += "sup."
                if str(k) in signed_vars : 
                    res += str(k) + "=" + "swconst("+str(i)+",32) "
                else :
                    res += str(k)+"="+str(i)+" "
    
    print(res)
    
    
def combine_smv_ltl(filename, ltlfile, new_smv_name):
    
    with open(filename,"r") as fin, open(new_smv_name,"w") as fout: 
        lines = fin.readlines()
        print("OK")
        for l in lines :
            if "LTLSPEC" in l  : 
                fout.write("\nLTLSPEC "+ltlfile)
                print("formula ",ltlfile)
                return
            fout.write(l)
            
def write_dimacs(filename, clauses, text):
    
    with open(filename, "r") as f, open(filename+"."+text+".dimacs", "w") as fout:
        for l in f.readlines():
            if "p cnf " in l :
                fout.write(l)
            if "c " in l :
                fout.write(l)
        for c in clauses : 
            fout.write(c)
            
def split_problem_into_three_subproblems(filename):
    
    end_model = 0
    unit_property_var = 0
    property_variables = set()
    
    clauses = list()
    clauses_string = list()
    
    with open(filename, "r") as f:
        lines = f.readlines()
        for l in lines :
            if "c M " in l :
                end_model = int(l.split()[-1])
                continue
            elif "c P " in l :
                unit_property_var = int(l.split()[-1])
                property_variables.add(unit_property_var)
                continue 
            elif "c " in l or "p cnf " in l :
                continue
            cls_split = l.split(" ")
            aclause = list()

            absolute_clause = [ abs(int(v)) for v in cls_split[:-1] ]
            if unit_property_var in absolute_clause:
                property_variables = property_variables.union(absolute_clause)
            for c in cls_split[:-1] :
                aclause.append( int(c) )
            clauses.append(aclause)
            clauses_string.append(l)
    
    cls_cp_cm = list()
    cls_cp_cj = list()    
    cls_cm_cj = list()
    cls_all   = list()
    cls_flower= list()
    
    print("Nb vars Property "+str(len(property_variables)))
    print(" size ",len(clauses),"   ,   ",len(clauses_string))
    for c,cs in zip(clauses,clauses_string):
        Model = False
        Property = False
        Junction = False
        JOnly = True
        MOnly = True
        POnly = True
        for var in c:
            if abs(var) in property_variables:
                Property = True
                JOnly = False
                MOnly = False
            elif abs(var) <= end_model:
                Model = True
                JOnly = False
                POnly = False
            else:
                Junction = True
                POnly = False
                MOnly = False

    ## Cp & Cm
        if POnly or MOnly or (Property and Model) :
            cls_cp_cm.append(cs)
    ## Cp & Cj
        if POnly or JOnly or (Property and Junction) :
            cls_cp_cj.append(cs)
    ## Cm & Cj
        if MOnly or JOnly or (Model and Junction) :
            cls_cm_cj.append(cs)
            
        if Model and Property and Junction:
            cls_all.append(cs)
            
        if (Property and Model) or (Property and Junction) or(Model and Junction) or (Model and Property and Junction) :
            cls_flower.append(cs)
            
    write_dimacs(filename, cls_cp_cm, "PROP_MODEL")
    write_dimacs(filename, cls_cp_cj, "PROP_JUNC")
    write_dimacs(filename, cls_cm_cj, "MODEL_JUNC")
    write_dimacs(filename, cls_all, "ALL")
    write_dimacs(filename, cls_flower, "INTERSECT")




            
    
            



filename = str(sys.argv[1])

if ".txt" in filename :
    parse_model_variables(filename)
    
elif ".dimacs" in filename:
    split_problem_into_three_subproblems(filename)
    
else :
    if len(sys.argv) < 2 : 
        print("Need more parameters : SMVFilename LTLformula NewSMVFilename\n" )
        exit(1)
    ltl = sys.argv[2]
    new_smv_name = str(sys.argv[3])
    combine_smv_ltl(filename, ltl, new_smv_name)
    
    
    
    