/*
 *  numerics.cpp
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 */


#include "numerics.h"
#include <gsl/gsl_math.h>

const double numerics::e = M_E;
const double numerics::pi = M_PI;


// later also in namespace
long
ld_round( double x )
{
  return ( long ) std::floor( x + 0.5 );
}

double
dround( double x )
{
  return std::floor( x + 0.5 );
}

double
dtruncate( double x )
{
  double ip;

  std::modf( x, &ip );
  return ip;
}
