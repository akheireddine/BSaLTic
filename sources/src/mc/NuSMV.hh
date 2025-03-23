
#pragma once 

#include <vector>
#include <string>

#include "../../nusmv_wrapper.hh"
#include "ModelChecker.hh"
#include "utils/EnvBMC.hh"


class NuSMV : public ModelChecker
{
public :
	NuSMV() = default ;

	//create new SMV problem in inputFile 
	NuSMV(const char* inputFile, EnvBMC * envi);

	~NuSMV();

	///NuSMV read model
	void read_model();

	//Return a pointer to a new LTL property builded from str_formula
	Prop_ptr get_LTL_Formula(char* str_formula, PropDb_ptr prop_db);

	//Generate a DIMACS file with an LTL property of type 
	//					(0 : always true, 1 : randam, 2 : extract from smv file)
	void generate_cnf_formula(int k_val, int prop_value);

	//Generate the k_max first DIMACS files of the same problem with same type of property 
	void generate_k_cnf_formula(int k_max, int prop_value);

	void dump_dimacs_NuSMV(Be_Cnf_ptr cnf, BeEnc_ptr be_enc);

	//Executes NuSMV commands from file source (batch mode)
	void run_NuSMV(std::string source);

	void print_properties();

protected :

	/// NuSMV Envrionment
	NuSMVEnv_ptr env_nusmv;

	EnvBMC * env;
};