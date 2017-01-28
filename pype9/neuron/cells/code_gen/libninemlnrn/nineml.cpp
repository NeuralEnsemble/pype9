/*
 
A library that wraps GSL random routines for use in mod-files:

gsl_rng* get_gsl_rng()
void release_gsl_rng()

double nineml_gsl_normal(double m, double s);
double nineml_gsl_uniform(double a, double b);
double nineml_gsl_binomial(double p, int n);
double nineml_gsl_exponential(double mu);
double nineml_gsl_poisson(double mu);

*/


#include <stdio.h>
#include <stdlib.h>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>





gsl_rng* nineml_gsl_rng = NULL;
unsigned int _seed = NULL;
  
/* FUNCTIONS FOR ALLOCATING & DEALLOCATING RNG */
extern "C"
gsl_rng* get_gsl_rng()
{
    if(nineml_gsl_rng == NULL)
    {
        nineml_gsl_rng = gsl_rng_alloc (gsl_rng_mt19937);
    }
    return nineml_gsl_rng;
}

extern "C"
void release_gsl_rng()
{
    if(nineml_gsl_rng)
    {
        gsl_rng_free (nineml_gsl_rng);
        nineml_gsl_rng = NULL;
    }
}

extern "C"
void nineml_seed_gsl_rng(unsigned int seed) {

    gsl_rng* rng = get_gsl_rng();
    _seed = seed;
    gsl_rng_set(rng, seed);

}


extern "C"
unsigned int nineml_get_gsl_rng_seed() {

    return _seed;

}


// Wrapper Functions:
//

extern "C"
double nineml_gsl_normal(double m, double s)
{
    gsl_rng* r = get_gsl_rng();
    return m + gsl_ran_gaussian(r, s);
}


extern "C"
double nineml_gsl_uniform(double a, double b)
{
    gsl_rng* r = get_gsl_rng();
    return gsl_ran_flat(r, a, b);
}

       
extern "C"
double nineml_gsl_binomial(double p, int n)
{
    gsl_rng* r = get_gsl_rng();
    return gsl_ran_binomial(r, p, n);
}
       
       
extern "C"
double nineml_gsl_exponential(double lambda)
{
    gsl_rng* r = get_gsl_rng();
    return gsl_ran_exponential(r,1.0/lambda);
}
       
       
extern "C"
double nineml_gsl_poisson(double mu)
{
    gsl_rng* r = get_gsl_rng();
    return gsl_ran_poisson(r,mu);
}
       
       
       
