/*
 ============================================================================
 Name        : TestNestPype.cpp
 Author      : 
 Version     :
 Copyright   : Your copyright notice
 Description : Hello World in C++,
 ============================================================================
 */

#include <iostream>

#include "branch.h"
#include "master.h"
#include "mock_nest.h"
#include "status.h"


int main(void) {

    std::cout << "Create model objects" << std::endl;
    
    // Initialise models
    nineml::Master master;
    nineml::Branch branch;
    
    std::cout << "Set Status" << std::endl;
    
    Dictionary status;
    set_status(status);  // From custom "status.h"
    DictionaryDatum status_datum(&status);

    master.set_status(status_datum);
    branch.set_status(status_datum);

    std::cout << "Initialise buffers" << std::endl;
    
    // Init Buffers of models
    master.init_buffers_();
    branch.init_buffers_();

    std::cout << "Calibrate" << std::endl;
    
    master.calibrate();
    branch.calibrate();

    double dt = 0.025;
    
    std::cout << "Run update steps" << std::endl;

    for (int i = 0; i < 100; ++i) {

        nest::Time origin(nest::Time::ms(i * dt));
        nest::long_t from = 0;
        nest::long_t to = 100;

        master.update(origin, from, to);
        branch.update(origin, from, to);

    }

	return 0;
}
