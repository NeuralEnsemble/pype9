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
#include "conditions.h"

#define MASTER
#define BRANCH

int main(void) {

    std::cout << "Create model objects" << std::endl;
    
    // Initialise models
#ifdef MASTER
    nineml::Master master;
#endif
#ifdef BRANCH
    nineml::Branch branch;
#endif
    
    std::cout << "Set Status" << std::endl;
    
    Dictionary status;
    set_status(status);  // From custom "status.h"
    DictionaryDatum status_datum(&status);

#ifdef MASTER
    master.set_status(status_datum);
#endif
#ifdef BRANCH
    branch.set_status(status_datum);
#endif

    std::cout << "Initialise buffers" << std::endl;
    
    // Init Buffers of models
#ifdef MASTER
    master.init_buffers_();
#endif
#ifdef BRANCH
    branch.init_buffers_();
#endif

    std::cout << "Calibrate" << std::endl;
    
#ifdef MASTER
    master.calibrate();
#endif
#ifdef BRANCH
    branch.calibrate();
#endif

    std::cout << "Set current and event buffers" << std::endl;
    
#ifdef MASTER
    set_ring_buffers<nineml::Master>(master);
#endif
#ifdef BRANCH
    set_ring_buffers<nineml::Branch>(branch);
#endif
    
    std::cout << "Run update steps" << std::endl;

    nest::Time origin(nest::Time::ms(0.0));
    
    for (int i = 0; i < NUM_SLICES; ++i) {

#ifdef MASTER
        master.update(origin, nest::Scheduler::min_delay * i, nest::Scheduler::min_delay * (i + 1));
#endif
#ifdef BRANCH
        branch.update(origin, nest::Scheduler::min_delay * i, nest::Scheduler::min_delay * (i + 1));
#endif

    }

    std::cout << "To plot comparison:" << std::endl;
    std::cout << "plot_comparison.py";
#ifdef MASTER
    std::cout << " " << get_data_path<nineml::Master>();
#endif
#ifdef BRANCH
    std::cout << " " << get_data_path<nineml::Branch>();
#endif
    std::cout << std::endl;
    
	return 0;
}
