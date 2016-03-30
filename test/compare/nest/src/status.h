//
//  set_parameters_and_state.h
//
//  Created by Tom Close on 12/04/2016.
//  Copyright © 2016 Tom Close. All rights reserved.
//

#ifndef status_h
#define status_h

#include "mock_nest.h"

inline void set_status(Dictionary& status) {
    status.insert(Name("C_m"), Token(1.0));
    status.insert(Name("a"), Token(0.2));
    status.insert(Name("alpha"), Token(0.04));
    status.insert(Name("b"), Token(0.025));
    status.insert(Name("beta"), Token(5.0));
    status.insert(Name("c"), Token(-75.0));
    status.insert(Name("d"), Token(0.2));
    status.insert(Name("theta"), Token(-50.0));
    status.insert(Name("zeta"), Token(140.0));
    status.insert(Name("U"), Token(-14.0));
    status.insert(Name("V"), Token(-65.0));
}

#endif /* status_h */
