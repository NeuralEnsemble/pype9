#ifndef RANDOM_H
#define RANDOM_H

#include <cmath>
#include <vector>
#include <list>
#include <map>
#include <sstream>
#include <algorithm>
#include <cassert>
#include <unistd.h>
#include <iostream>
#include <fstream>
#include <gsl/gsl_rng.h>
//#include "nest_time.h"
//#include "nest.h"
#include "lockptr.h"
//#include "mock_sli.h"
//#include "arraydatum.h"

namespace librandom {
    
    class RandomGen;

    typedef lockPTR< RandomGen > RngPtr;

    class RandomGen {
      public:
        /**
         * @note All classes derived from RandomGen should
         *       have only a single constructor, taking
         *       an unsigned long as seed value. Use
         *       RandomGen::DefaultSeed if you want to
         *       create a generator with a default seed value.
         */
        RandomGen() {}

        // ensures proper clean up
        virtual ~RandomGen() {}

        /**
         The following functions implement the user interface of the
         RandomGen class. The actual interface to the underlying
         random generator is provided by protected member functions below.
         */
        double drand(void);                    //!< draw from [0, 1)
        double operator()( void ) { return drand(); }                   //!< draw from [0, 1)
        double drandpos(void);                 //!< draw from (0, 1)

        static RngPtr create_knuthlfg_rng(const unsigned long seed);

        const static unsigned long DefaultSeed;

    };

    class KnuthLFG : public RandomGen
    {
    public:
      //! Create generator with given seed
      explicit KnuthLFG( unsigned long );

      ~KnuthLFG(){};

      RngPtr
      clone( unsigned long s )
      {
        return RngPtr( new KnuthLFG( s ) );
      }

    private:
      //! implements seeding for RandomGen
      void seed_( unsigned long );

      //! implements drawing a single [0,1) number for RandomGen
      double drand_();

    private:
      static const long KK_;          //!< the long lag
      static const long LL_;          //!< the short lag
      static const long MM_;          //!< the modulus
      static const long TT_;          //!< guaranteed separation between streams
      static const long QUALITY_;     //!< number of RNGs to fill for each cycle
      static const double I2DFactor_; //!< int to double factor

      static long mod_diff_( long, long ); //!< subtraction module MM
      static bool is_odd_( long );

      std::vector< long > ran_x_;                     //!< the generator state
      std::vector< long > ran_buffer_;                //!< generated numbers, 0..KK-1 are shipped
      const std::vector< long >::const_iterator end_; //!< marker past last to deliver
      std::vector< long >::const_iterator next_;      //!< next number to deliver

      /**
       * Generates numbers, refilling buffer.
       * @note Buffer must be passed as argument, since ran_start_() and
       *       self_test_() must pass other buffers than ran_buffer_.
       */
      void ran_array_( std::vector< long >& rbuff );
      void ran_start_( long seed ); //!< initializes buffer
      long ran_draw_();             //!< deliver integer random number from ran_buffer_

      /**
       * Perform minimal self-test given by Knuth.
       * The test will break an assertion if it fails. This is acceptable,
       * since failure indicates either lack of two's complement arithmetic
       * or problems with the size of data types.
       */
      void self_test_();
    };

    inline void
    KnuthLFG::seed_( unsigned long seed )
    {
      ran_start_( seed );
    }


    inline double
    KnuthLFG::drand_()
    {
      return I2DFactor_ * ran_draw_();
    }


    inline long
    KnuthLFG::mod_diff_( long x, long y )
    {
      // modulo computation assumes two's complement
      return ( x - y ) & ( MM_ - 1 );
    }

    inline bool
    KnuthLFG::is_odd_( long x )
    {
      return x & 1;
    }

    inline long
    KnuthLFG::ran_draw_()
    {
      if ( next_ == end_ )
      {
        ran_array_( ran_buffer_ ); // refill
        next_ = ran_buffer_.begin();
      }

      return *next_++; // return next and increment
    }

    class GslRandomGen : public RandomGen
    {
      friend class GSL_BinomialRandomDev;

    public:
      explicit GslRandomGen( const gsl_rng_type*, //!< given RNG, given seed
        unsigned long );

      ~GslRandomGen();

      RngPtr
      clone( unsigned long s )
      {
        return RngPtr( new GslRandomGen( rng_type_, s ) );
      }


    private:
      void seed_( unsigned long );
      double drand_( void );

    private:
      gsl_rng_type const* rng_type_;
      gsl_rng* rng_;
    };

    inline void
    GslRandomGen::seed_( unsigned long s )
    {
      gsl_rng_set( rng_, s );
    }

    inline double
    GslRandomGen::drand_( void )
    {
      return gsl_rng_uniform( rng_ );
    }

    //! Factory class for GSL-based random generators
    class GslRNGFactory {
      public:
        GslRNGFactory( gsl_rng_type const* const );
        RngPtr create( unsigned long ) const;

      private:
        //! GSL generator type information
        gsl_rng_type const* const gsl_rng_;
    };

}

#endif
