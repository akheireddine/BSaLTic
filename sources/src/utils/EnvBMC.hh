
#pragma once

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_set>

#include "../../painless/painless-src/clauses/ClauseExchange.h"
#include "../../painless/painless-src/clauses/ClauseManager.h"
#include "../../painless/painless-src/utils/Parameters.h"


typedef struct variableBelonging
{
  int num_step;
  int num_partition;
  std::unordered_set<int> step_connection;
  bool in_property;
} VB;

class EnvBMC
{
public:
  EnvBMC()
  {
    stop_at_first_unsat = false;
    max_vars = 0;
    max_vars_plusone = 0;
    maxVarsPure = -1;
    minVarsPure = -1;
    std_solver_num = 0;
    sp_solver_num  = 0;
    selector = Parameters::getParam("selector","none");
    shr_strat = Parameters::getIntParam("shr-heuristic", 0);
    shr_approach = Parameters::getIntParam("sharing", 0);
    lbd_limit = Parameters::getIntParam("lbd-limit", 4);
    ltl = Parameters::getParam("ltl", "none");
    diversification = Parameters::getIntParam("d", 0);
    num_solvers = Parameters::getIntParam("ns", 1);
    cpus = Parameters::getIntParam("c", 1); // std::thread::hardware_concurrency());
    timeout = Parameters::getIntParam("t", -1);
    memory = Parameters::getIntParam("max-memory", -1) * 1024 * 1024;
    nb_leaf = Parameters::getIntParam("nleafs", 1);
    k = Parameters::getIntParam("k",1);
    solver_type = Parameters::getParam("s","maple");
    split_name = Parameters::getParam("split", "b");
    reducer = Parameters::getIntParam("r", -1);
    protection = Parameters::getParam("protect","none");
    convertor = Parameters::getIntParam("conv",1);

  }

  ~EnvBMC()
  {
    for (ClauseExchange *i : clause_database)
      ClauseManager::releaseClause(i);
  }
  /**************************** BSaLTic main parameters ****************************/

  // stdout
  std::ofstream opf;

  /********************************** Clauses and variable info from NuSMV or lecture *******************************/
  std::vector<ClauseExchange *> clause_database;

  std::vector<std::unordered_set<int>> pure_vars;

  std::vector<std::vector<bool>> pure_vars_bitset;

  /*************************************************************************************/

  std::vector<bool> pure_variables_of_step(int i)
  {
    std::vector<bool> variables_step(maxVarsPure + 1, false);
    for (int var = 0; var < maxVarsPure; var++)
    {
      if (info_variables[var].num_step == i)
        variables_step[var] = true;
    }
    return variables_step;
  }

  void initialize_info_variables()
  {
    maxVarsPure = -1;
    info_variables.resize(max_vars_plusone);
    for (unsigned i = 0; i < pure_vars.size(); i++)
    {
      for (int var : pure_vars[i])
      {
        info_variables[var].num_step = i;
        info_variables[var].num_partition = -1;
        info_variables[var].step_connection.insert(i);
        info_variables[var].in_property = false;
        maxVarsPure = maxVarsPure < var ? var : maxVarsPure;
        minVarsPure = ((minVarsPure > var) || (minVarsPure == -1)) ? var : minVarsPure;
      }
    }
    for (int i = maxVarsPure + 1; i < max_vars_plusone; i++)
    {
      info_variables[i].num_step = -1;
      info_variables[i].num_partition = -1;
      info_variables[i].in_property = false;
    }
    extract_property_variables();
  }

  void extract_property_variables()
  {
    clauses_property.clear();
    property_variables.resize(max_vars_plusone, false);
    for (auto c : clause_database)
    {
      for (int i = 0; i < c->size; i++)
      {
        if (std::abs(c->lits[i]) == max_vars)
        {
          clauses_property.emplace_back(c);
          break;
        }
      }
    }
    for (auto cl : clauses_property)
    {
      for (int i = 0; i < cl->size; i++)
      {
        int var = std::abs(cl->lits[i]);
        property_variables[var] = true;
        info_variables[var].in_property = true;
      }
    }
  }

  void save_variable_information(std::string filename)
  {
    std::ofstream f(filename + "_n" + std::to_string(nb_leaf) + ".csv");

    f << "Num Variable,Related Steps,Partition,Pure Variable" << std::endl;
    for (int i = minVarsPure; i < max_vars_plusone; i++)
    {
      if (info_variables[i].step_connection.empty())
        continue;
      f << i << ",";
      for (int v : info_variables[i].step_connection)
        f << v << " ";
      f << "," << info_variables[i].num_partition;
      if (i <= maxVarsPure)
        f << ",TRUE" << std::endl;
      else
        f << ",FALSE" << std::endl;
    }
  }

  void update_variable_bloc_bitset()
  {
    pure_vars_bitset.clear();
    pure_vars_bitset.resize(pure_vars.size(), std::vector<bool>(max_vars_plusone, false));
    for (unsigned i = 0; i < pure_vars.size(); i++)
    {
      for (int var : pure_vars[i])
        pure_vars_bitset[i][var] = true;
    }
  };


  void setStopFirstUnsat(std::string stop)
  {
    stop_at_first_unsat = !stop.compare("0") ? false : true;
  }

  /// Working strategies BMC parameters
  bool stop_at_first_unsat;

  int max_vars;

  int max_vars_plusone;

  int maxVarsPure;
  int minVarsPure;

  int std_solver_num;
  int sp_solver_num;

  std::vector<ClauseExchange *> clauses_property;

  std::vector<bool> property_variables;
  std::vector<VB> info_variables;


  string  selector;
  string  protection;
  int  shr_strat;
  int  shr_approach;
  int lbd_limit;
  string  ltl;
  int  diversification;
  int  num_solvers;
  int  cpus;
  int  timeout;
  int  convertor;
  int  memory;
  int  nb_leaf;
  int  k;
  string  solver_type;
  string  split_name;
  int reducer;

};
