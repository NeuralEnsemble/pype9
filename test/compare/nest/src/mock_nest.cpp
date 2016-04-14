#include "mock_nest.h"
#include "nest_time.h"
#include "nest_names.h"

#include <iostream>
#include <iomanip>
#include <vector>

const Name receptor_type( "receptor_type" );
const Name receptor_types( "receptor_types" );
const Name recordables( "recordables" );
const Name t_spike( "t_spike" );

const unsigned long librandom::RandomGen::DefaultSeed = 0xd37ca59fUL;

delay nest::Scheduler::min_delay = 1000;
delay nest::Scheduler::max_delay = 10000;
unsigned int moduli_size = 100;

void nest::RingBuffer::add_value( const long_t offs, const double_t v ) {
  buffer_[ get_index_( offs ) ] += v;
}

void nest::RingBuffer::set_value( const long_t offs, const double_t v ) {
  buffer_[ get_index_( offs ) ] = v;
}

double nest::RingBuffer::get_value( const long_t offs ) {
  assert( 0 <= offs && ( size_t ) offs < buffer_.size() );
  assert( ( delay ) offs < nest::Scheduler::min_delay );

  // offs == 0 is beginning of slice, but we have to
  // take modulo into account when indexing
  long_t idx = get_index_( offs );
  double_t val = buffer_[ idx ];
  buffer_[ idx ] = 0.0; // clear buffer after reading
  return val;
}

size_t nest::RingBuffer::get_index_( const delay d ) const {
  const long_t idx = get_modulo( d );
  assert( 0 <= idx );
  assert( ( size_t ) idx < buffer_.size() );
  return idx;
}

delay nest::RingBuffer::get_modulo( delay d ) {

  // Note, here d may be 0, since bin 0 represents the "current" time
  // when all evens due are read out.

  // This is usually read from the moduli_ buffer but we don't care about that
  // as we will only have the time "slice"
  return d;
}

nest::RingBuffer::RingBuffer()
  : buffer_( 0.0, nest::Scheduler::min_delay + nest::Scheduler::max_delay ) {}

void nest::RingBuffer::resize() {
  size_t size = nest::Scheduler::min_delay + nest::Scheduler::max_delay;
  if ( buffer_.size() != size )
  {
    buffer_.resize( size );
    buffer_ = 0.0;
  }
}

void nest::RingBuffer::clear() {
  resize();      // does nothing if size is fine
  buffer_ = 0.0; // clear all elements
}

void nest::Archiving_Node::set_status( const DictionaryDatum& d ) {
//
//  // We need to preserve values in case invalid values are set
//  double_t new_tau_minus = tau_minus_;
//  double_t new_tau_minus_triplet = tau_minus_triplet_;
//  updateValue< double_t >( d, names::tau_minus, new_tau_minus );
//  updateValue< double_t >( d, names::tau_minus_triplet, new_tau_minus_triplet );
//
//  if ( new_tau_minus <= 0 || new_tau_minus_triplet <= 0 )
//    throw BadProperty( "All time constants must be strictly positive." );
//
//  tau_minus_ = new_tau_minus;
//  tau_minus_triplet_ = new_tau_minus_triplet;
//
//  // check, if to clear spike history and K_minus
//  bool clear = false;
//  updateValue< bool >( d, names::clear, clear );
//  if ( clear )
//    clear_history();
}

nest::Time const& nest::Network::get_slice_origin() const {
  return TimeZero;
}

nest::Network::Network(long seed) :
   rng_(new librandom::GslRandomGen(gsl_rng_knuthran2002, seed)) {}


librandom::RngPtr librandom::RandomGen::create_knuthlfg_rng( unsigned long seed ) {
  return librandom::RngPtr( new librandom::KnuthLFG( seed ) );
}


librandom::GslRandomGen::GslRandomGen( const gsl_rng_type* type, unsigned long seed )
  : RandomGen()
{
  rng_ = gsl_rng_alloc( type );
  rng_type_ = type;
  assert( rng_ != NULL );
  gsl_rng_set( rng_, seed );
}

librandom::GslRandomGen::~GslRandomGen()
{
  gsl_rng_free( rng_ );
}


librandom::GslRNGFactory::GslRNGFactory( gsl_rng_type const* const t )
  : gsl_rng_( t )
{
  assert( t != 0 );
}

librandom::RngPtr
librandom::GslRNGFactory::create( unsigned long s ) const
{
  return RngPtr( new GslRandomGen( gsl_rng_, s ) );
}


long_t nest::Event::get_rel_delivery_steps( const nest::Time& t ) const
{
  return d_ - 1 - t.get_steps();
}

void nest::Archiving_Node::get_status( DictionaryDatum& d ) const {
  def< double >( d, names::t_spike, get_spiketime_ms() );
//  def< double >( d, names::tau_minus, tau_minus_ );
//  def< double >( d, names::tau_minus_triplet, tau_minus_triplet_ );
}


const long librandom::KnuthLFG::KK_ = 100;
const long librandom::KnuthLFG::LL_ = 37;
const long librandom::KnuthLFG::MM_ = 1L << 30;
const long librandom::KnuthLFG::TT_ = 70;
const long librandom::KnuthLFG::QUALITY_ = 1009;
const double librandom::KnuthLFG::I2DFactor_ = 1.0 / librandom::KnuthLFG::MM_;

librandom::KnuthLFG::KnuthLFG( unsigned long seed )
  : ran_x_( KK_ )
  , ran_buffer_( QUALITY_ )
  , end_( ran_buffer_.begin() + KK_ )
  , next_( end_ )
{
  self_test_(); // minimal check
  ran_start_( seed );
}

void librandom::KnuthLFG::ran_array_( std::vector< long >& rbuff ) {
  const int n = rbuff.size();
  int i, j;
  for ( j = 0; j < KK_; j++ )
    rbuff[ j ] = ran_x_[ j ];
  for ( ; j < n; j++ )
    rbuff[ j ] = mod_diff_( rbuff[ j - KK_ ], rbuff[ j - LL_ ] );
  for ( i = 0; i < LL_; i++, j++ )
    ran_x_[ i ] = mod_diff_( rbuff[ j - KK_ ], rbuff[ j - LL_ ] );
  for ( ; i < KK_; i++, j++ )
    ran_x_[ i ] = mod_diff_( rbuff[ j - KK_ ], ran_x_[ i - LL_ ] );
}

/* the following routines are from exercise 3.6--15 */
/* after calling ran_start, get new randoms by, e.g., "x=ran_arr_next()" */
void librandom::KnuthLFG::ran_start_( long seed ) {
  int t, j;
  std::vector< long > x( KK_ + KK_ - 1 ); /* the preparation buffer */
  long ss = ( seed + 2 ) & ( MM_ - 2 );
  for ( j = 0; j < KK_; j++ )
  {
    x[ j ] = ss; /* bootstrap the buffer */
    ss <<= 1;
    if ( ss >= MM_ )
      ss -= MM_ - 2; /* cyclic shift 29 bits */
  }
  x[ 1 ]++; /* make x[1] (and only x[1]) odd */
  for ( ss = seed & ( MM_ - 1 ), t = TT_ - 1; t; )
  {
    for ( j = KK_ - 1; j > 0; j-- )
      x[ j + j ] = x[ j ], x[ j + j - 1 ] = 0; /* "square" */
    for ( j = KK_ + KK_ - 2; j >= KK_; j-- )
      x[ j - ( KK_ - LL_ ) ] = mod_diff_( x[ j - ( KK_ - LL_ ) ], x[ j ] ),
                           x[ j - KK_ ] = mod_diff_( x[ j - KK_ ], x[ j ] );
    if ( is_odd_( ss ) )
    { /* "multiply by z" */
      for ( j = KK_; j > 0; j-- )
        x[ j ] = x[ j - 1 ];
      x[ 0 ] = x[ KK_ ]; /* shift the buffer cyclically */
      x[ LL_ ] = mod_diff_( x[ LL_ ], x[ KK_ ] );
    }
    if ( ss )
      ss >>= 1;
    else
      t--;
  }
  for ( j = 0; j < LL_; j++ )
    ran_x_[ j + KK_ - LL_ ] = x[ j ];
  for ( ; j < KK_; j++ )
    ran_x_[ j - LL_ ] = x[ j ];
  for ( j = 0; j < 10; j++ )
    ran_array_( x ); /* warm things up */

  // mark as needing refill
  next_ = end_;
}

void librandom::KnuthLFG::self_test_() {
  int m;
  std::vector< long > tbuff( 1009 ); // buffer for test data
  ran_start_( 310952L );
  for ( m = 0; m <= 2009; m++ )
    ran_array_( tbuff );
  assert( tbuff[ 0 ] == 995235265 );

  tbuff.resize( 2009 );
  ran_start_( 310952L );
  for ( m = 0; m <= 1009; m++ )
    ran_array_( tbuff );
  assert( tbuff[ 0 ] == 995235265 );
}
