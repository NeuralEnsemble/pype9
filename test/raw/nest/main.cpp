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
#include "dictdatum.h"
#include "network.h"
#include "IzhikevichMaster.h"
#include "IzhikevichBranch.h"


int main(void) {

    // Initialise network
    SLIInterpreter sli;
    nest::Network network(sli);

    // Initialise models
    nineml::IzhikevichMaster reference;
    nineml::IzhikevichBranch generated;

    // Set statuses of models
    Dictionary reference_status;
    Dictionary generated_status;

    reference_status.insert(Name("test"), Token(1.0));

    DictionaryDatum reference_datum(reference_status);
    DictionaryDatum generated_datum(generated_status);

    // Init Buffers of models
    reference.init_buffers();
    generated.init_buffers();

    std::cout << "Hello Nest 3" << std::endl; /* prints Hello World */

    reference.calibrate();
    generated.calibrate();

    double dt = 0.025;

    for (int i = 0; i < 100; ++i) {

        nest::Time origin(nest::Time::ms(i * dt));
        nest::long_t from = 0;
        nest::long_t to = 100;

        reference.update(origin, from, to);
        generated.update(origin, from, to);

    }

	return 0;
}
