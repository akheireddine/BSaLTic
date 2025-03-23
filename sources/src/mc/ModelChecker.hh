
#pragma once

#include <stdlib.h>
#include <stdio.h>
#include <vector>
#include <string>

class ModelChecker;


class ModelChecker
{
public :
	//Constructor
	ModelChecker() = default;
	
	//Destructor
	virtual ~ModelChecker() = default;

	//Generate a DIMACS file with an LTL property of type 
	//					(0 : always true, 1 : randam, 2 : extract from smv file)
	virtual void generate_cnf_formula(int k_val, int prop_value) = 0;

    //Getter for k_ variable
	inline int get_k(){ return k_; };

    //Setter for k_ variable
	inline void set_k(int k){ k_ = k; };

protected :
	// Filename of input model
	std::string modelFile_;

	// Bound of the transition relation
	int k_;
};
