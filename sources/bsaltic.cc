
#include <cerrno>
#include <string>

#include "painless/painless-src/utils/Parameters.h"
#include "painless/painless-src/decomposition/splitFormula.hh"
#include "painless/painless-src/painless.h"
#include "src/mc/NuSMV.hh"

// Global main variables
string mode;
string fname;
EnvBMC *env;
SplitBMCFormula *splitter;
std::fstream csvfilestream;
std::vector<string> conv_name = {"\"TSEITIN\"", "\"SHERIDAN\""};

bool read_Filename()
{
	splitter->read_NuSMV_dimacs_file(fname.c_str());
	return true;
}

bool run_Conversion()
{
	// int prop_verify = Parameters::getIntParam("prop", 2);

	// with .smv extension
	if ((mode.compare("c") == 0))
	{
		string ffname = Parameters::removeExtensionFromFilename(".smv");
		// Create Model
		ModelChecker *mctool;
		mctool = new NuSMV(ffname.c_str(), env);

		// Convert SMV instance to CNF formula
		clock_t t1 = clock();
		mctool->generate_cnf_formula(env->k, 2);
		t1 = clock() - t1;

		env->opf << "c CONVERSION TO CNF FORMAT USING " << conv_name[env->convertor] << " : " << ((float)t1) / CLOCKS_PER_SEC << endl;

		delete mctool;

		return true;
	}
	return false;
}

bool run_Painless()
{
	SatResult result_code = SAT;
	if ((mode.compare("p") == 0) && ((fname.find(".cnf") != std::string::npos) ||
									 (fname.find(".dimacs") != std::string::npos)))
	{
		read_Filename();

		/// Empty variables
		if (env->max_vars == 0)
		{
			env->opf << "c ERROR no variable found" << endl;
			std::cout << "s ERROR no variable found" << endl;
			exit(1);
		}
		clock_t t1 = clock();
		result_code = run_painless_strategy(env);
		t1 = clock() - t1;
		float total_time = ((float)t1) / CLOCKS_PER_SEC;
		if (csvfilestream.is_open())
		{
			string result_code_str = "SAT";
			if (result_code == UNSAT)
				result_code_str = "UNSAT";
			else if (result_code == UNKNOWN)
				result_code_str = "wall clock limit exceeded";
			string instance_name = fname.substr(fname.find_last_of("/") + 1);
			string solver_name = "MapleCOMSPS";

			if (!env->selector.compare("hf") && !env->protection.compare("e"))
				solver_name = "BSaLTic-EHf";
			else if (!env->selector.compare("hf") && !env->protection.compare("dr"))
				solver_name = "BSaLTic-DHf";

			csvfilestream << solver_name << "," << env->ltl << "," << instance_name << "," << result_code_str << "," << total_time << std::endl;
		}

		env->opf << "c TOTAL RESOLUTION TIME : " << ((float)t1) / CLOCKS_PER_SEC << endl;

		return true;
	}

	return false;
}

int main(int argc, char **argv)
{
	// Init parameters
	Parameters::init(argc, argv);

	if (argc < 2 || Parameters::isSet("h"))
	{
		std::cerr << "Missing parameters. At least provide : " << std::endl;
		std::cout << "USAGE: " << argv[0] << " [parameters] filename" << std::endl;
		std::cout << "Parameters:" << std::endl;
		std::cout << "\tfilename  \t  : Filename problem {.smv,.cnf,.dimacs}." << std::endl;
		std::cout << "\t-t=<int> int \t  : timeout (default none)." << std::endl;
		std::cout << "\t-max-memory=<int> : memory limit in Go (default none)." << std::endl;
		std::cout << "\t-mode=<str>       : mode to use default is p (c : Convert SMV instance into DIMACS. " << std::endl;
		std::cout << "\t\t\t\t\t\t      p : Run solving)." << std::endl;
		std::cout << std::endl;
		std::cout << "\t Only for {c} mode : " << std::endl;
		std::cout << "\t    -k=<int> \t   : Bound for the transition relation (bound 0 included : k+1)." << std::endl;
		std::cout << "\t    -conv=0,1 \t   : Conversion algorithm (0 : Tseitin, 1 : Sheridan, default is 1)." << std::endl;

		std::cout << "\t Only for {p} mode : " << std::endl;
		//		std::cout << "\t    -c=<int> \t   : Number of cpus (default is 1)." << std::endl;
		//		std::cout << "\t    -s {maple} \t   : special solver name, default is maple." << std::endl;
		std::cout << "\t    -no-model  \t   : The model will not be printed." << std::endl;
		//		std::cout << "\t    -pin=<int> \t   : Pin threads (-1: don't pin, v >= 0: start pin at value v), default is 0." << std::endl;
		std::cout << "\t    -o=<str> \t   : Print result in csv file format." << std::endl;
		//		std::cout << "\t    -ns=<int> \t   : Number of standard maple solvers (default is 1)." << std::endl;
		std::cout << "\t    -ltl=<str>     : specify the LTL property before negation (default is \"none\",\
									\n\t\t\t\t\t\t\t\t       guarantee,\
									\n\t\t\t\t\t\t\t\t       safety,\
									\n\t\t\t\t\t\t\t\t       obligation,\
									\n\t\t\t\t\t\t\t\t       persistence,\
									\n\t\t\t\t\t\t\t\t       recurrence,\
									\n\t\t\t\t\t\t\t\t       reactivity,\
									\n\t\t\t\t\t\t\t\t       none : default selector (CORE LBD<4 and TIER-2 LBD<7))."
				  << std::endl;
		std::cout << "\t    -r=<int> \t\t : Multiplicative factor (default value is 1)." << std::endl;

		//		std::cout << "\t    -d=0...7  \t   : diversification (0: none,
		//									\n    \t\t\t\t\t      1:sparse,
		//									\n    \t\t\t\t\t      2: dense,
		//									\n    \t\t\t\t\t      3: random,
		//									\n    \t\t\t\t\t      4: native,
		//									\n    \t\t\t\t\t      5: 1&4,
		//									\n    \t\t\t\t\t      6: sparse-random,
		//									\n    \t\t\t\t\t      7: 6&4,
		//									\n    \t\t\t\t\t      default is 0)."
		//				  << std::endl;

		//		std::cout << "\t    -sharing=0...1 : Sharing strategy (0: No sharing,
		//									\n    \t\t\t\t\t       1: All-to-All,
		//									\n    \t\t\t\t\t       2: Hordesat,
		//									\n    \t\t\t\t\t       default is 0)."
		//				  << std::endl;

		std::cout << "\t    -selector=<str> \t : Heuristic for selecting relevant learnt clause (default is \"none\",\
									\n\t\t\t\t\t\t\t\t\t\t   hf: frequency-based heuristic\
									\n\t\t\t\t\t\t\t\t\t\t   none: default heuristic (LBD<7 in tier2))."
				  << std::endl;
		std::cout << "\t    -protect=<str> \t : Protection of learnt clauses's selector (default is \"none\",\
									\n\t\t\t\t\t\t\t\t\t     e:  explicit storage,\
									\n\t\t\t\t\t\t\t\t\t     dr: database reduction\
									\n\t\t\t\t\t\t\t\t\t     none: use default protection)."
				  << std::endl;

		//		std::cout << "\t    -lbd-limit=<int> \t : LBD limit for sharing clauses using All-to-All strategy (default value is 4)." << std::endl;

		//		std::cout << "\t    -shr-heuristic=0...3 : Sharing heuristic based on the selector (0: share clauses with lbd <= lbd-limit,
		//									\n    \t\t\t\t\t\t\t\t\t    1: sharing is based on the CORE selector,
		//									\n    \t\t\t\t\t\t\t\t\t    2: sharing is based on the TIER2 selector,
		//									\n    \t\t\t\t\t\t\t\t\t    3: sharing is based on the LBD<4 selector,
		//									\n    \t\t\t\t\t\t\t\t\t    default is 0)."
		//				  << std::endl;
		std::cout << std::endl;
		return 0;
	}

	// Initialize variables
	env = new EnvBMC();
	splitter = new SplitBMCFormula(env);
	mode = Parameters::getParam("mode", "p");
	fname = Parameters::getFilename();
	string filename_csv = Parameters::getParam("o", "");

	if (!filename_csv.empty())
	{
		csvfilestream.open(filename_csv, ios::in | ios::out | ios::app);
		if (csvfilestream.peek() == std::ofstream::traits_type::eof())
			csvfilestream << "Solver Configuration,LTL,Instance,Result Code,Wall Time" << std::endl;
	}

	// let standard cout output
	env->opf.copyfmt(std::cout);
	env->opf.clear(std::cout.rdstate());
	env->opf.basic_ios<char>::rdbuf(std::cout.rdbuf());

	// Print parameters
	Parameters::printParams(env->opf);

	if (run_Conversion())
		std::cout << "c Conversion done successfully.\n";
	else
	{
		if (run_Painless())
			std::cout << "c Run BSaLTic done successfully.\n";
		else
			std::cerr << "Run nothing..." << std::endl;
	}

	env->opf.close();

	delete splitter;
	delete env;
	std::cout << "c Done." << std::endl;
	return finalResult;
}
