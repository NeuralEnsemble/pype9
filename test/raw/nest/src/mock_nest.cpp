#include "mock_nest.h"

#include <iostream>
#include <iomanip>

const Name receptor_type( "receptor_type" );
const Name receptor_types( "receptor_types" );
const Name recordables( "recordables" );
const Name t_spike( "t_spike" );

const unsigned long librandom::RandomGen::DefaultSeed = 0xd37ca59fUL;

double min_delay = 0.1;

Token::Token( int value )
{
  p = new IntegerDatum( value );
}

Token::Token( unsigned int value )
{
  p = new IntegerDatum( value );
}

Token::Token( long value )
{
  p = new IntegerDatum( value );
}

Token::Token( unsigned long value )
{
  p = new IntegerDatum( value );
}

Token::Token( double value )
{
  p = new DoubleDatum( value );
}


Token::operator long() const
{
  return getValue< long >( *this );
}

Token::operator size_t() const
{
  return getValue< long >( *this );
}

Token::operator double() const
{
  return getValue< double >( *this );
}


Token& Dictionary::insert_move( const Name& n, Token& t )
{
  Token& result = TokenMap::operator[]( n );
  result.move( t );
  return result;
}

inline Token& Dictionary::insert( const Name& n, const Token& t )
{
  return TokenMap::operator[]( n ) = t;
}

inline Token& Dictionary::operator[]( const Name& n )
{
  return TokenMap::operator[]( n );
}


void nest::RingBuffer::clear()
{
  resize();      // does nothing if size is fine
  buffer_ = 0.0; // clear all elements
}

void nest::RingBuffer::add_value( const long_t offs, const double_t v )
{
 buffer_[ get_index_( offs ) ] += v;
}

double nest::RingBuffer::get_value( const long_t offs ) {
  assert( 0 <= offs && ( size_t ) offs < buffer_.size() );
  assert( ( delay ) offs < Scheduler::get_min_delay() );

  // offs == 0 is beginning of slice, but we have to
  // take modulo into account when indexing
  long_t idx = get_index_( offs );
  double_t val = buffer_[ idx ];
  buffer_[ idx ] = 0.0; // clear buffer after reading
  return val;
}

void nest::Archiving_Node::set_status( const DictionaryDatum& d ) {
  // We need to preserve values in case invalid values are set
  double_t new_tau_minus = tau_minus_;
  double_t new_tau_minus_triplet = tau_minus_triplet_;
  updateValue< double_t >( d, names::tau_minus, new_tau_minus );
  updateValue< double_t >( d, names::tau_minus_triplet, new_tau_minus_triplet );

  if ( new_tau_minus <= 0 || new_tau_minus_triplet <= 0 )
    throw BadProperty( "All time constants must be strictly positive." );

  tau_minus_ = new_tau_minus;
  tau_minus_triplet_ = new_tau_minus_triplet;

  // check, if to clear spike history and K_minus
  bool clear = false;
  updateValue< bool >( d, names::clear, clear );
  if ( clear )
    clear_history();
}

nest::Time const& nest::Network::get_slice_origin() const {
  return Time(0);
}

nest::Network::Network() {
    rng_ = librandom::RandomGen::create_knuthlfg_rng(librandom::RandomGen::DefaultSeed);
}

nest::Network:~Network{
    delete rng_;
}

librandom::RandomGen::create_knuthlfg_rng( unsigned long seed ) {
  return librandom::RngPtr( new librandom::KnuthLFG( seed ) );
}

inline long_t Event::get_rel_delivery_steps( const Time& t ) const
{
  return d_ - 1 - t.get_steps();
}

void nest::Archiving_Node::get_status( DictionaryDatum& d ) const {
  def< double >( d, names::t_spike, get_spiketime_ms() );
  def< double >( d, names::tau_minus, tau_minus_ );
  def< double >( d, names::tau_minus_triplet, tau_minus_triplet_ );
}

const Token& Dictionary::lookup( const Name& n ) const {
  TokenMap::const_iterator where = find( n );
  if ( where != end() )
    return ( *where ).second;
  else
    return Dictionary::VoidToken;
}


namespace nest {

    const nest::double_t Time::Range::TICS_PER_MS_DEFAULT = CONFIG_TICS_PER_MS;
    const tic_t Time::Range::TICS_PER_STEP_DEFAULT = CONFIG_TICS_PER_STEP;

    tic_t Time::Range::OLD_TICS_PER_STEP = Time::Range::TICS_PER_STEP_DEFAULT;
    tic_t Time::Range::TICS_PER_STEP = Time::Range::TICS_PER_STEP_DEFAULT;
    tic_t Time::Range::TICS_PER_STEP_RND = Time::Range::TICS_PER_STEP - 1;

    nest::double_t Time::Range::TICS_PER_MS = Time::Range::TICS_PER_MS_DEFAULT;
    nest::double_t Time::Range::MS_PER_TIC = 1 / Time::Range::TICS_PER_MS;

    nest::double_t Time::Range::MS_PER_STEP = TICS_PER_STEP / TICS_PER_MS;
    nest::double_t Time::Range::STEPS_PER_MS = 1 / Time::Range::MS_PER_STEP;

    tic_t
    Time::compute_max()
    {
      const long_t lmax = std::numeric_limits< long_t >::max();
      const tic_t tmax = std::numeric_limits< tic_t >::max();

      tic_t tics;
      if ( lmax < tmax / Range::TICS_PER_STEP ) // step size is limiting factor
        tics = Range::TICS_PER_STEP * ( lmax / Range::INF_MARGIN );
      else // tic size is limiting factor
        tics = tmax / Range::INF_MARGIN;
      // make sure that tics and steps match so that we can have simple range
      // checking when going back and forth, regardless of limiting factor
      return tics - ( tics % Range::TICS_PER_STEP );
    }

    Time::Limit::Limit( const tic_t& t )
      : tics( t )
      , steps( t / Range::TICS_PER_STEP )
      , ms( steps * Range::MS_PER_STEP )
    {
    }

    Time::Limit Time::LIM_MAX( +Time::compute_max() );
    Time::Limit Time::LIM_MIN( -Time::compute_max() );

    void
    Time::set_resolution( double_t ms_per_step )
    {
      assert( ms_per_step > 0 );

      Range::OLD_TICS_PER_STEP = Range::TICS_PER_STEP;
      Range::TICS_PER_STEP = static_cast< tic_t >( dround( Range::TICS_PER_MS * ms_per_step ) );
      Range::TICS_PER_STEP_RND = Range::TICS_PER_STEP - 1;

      // Recalculate ms_per_step to be consistent with rounding above
      Range::MS_PER_STEP = Range::TICS_PER_STEP / Range::TICS_PER_MS;
      Range::STEPS_PER_MS = 1 / Range::MS_PER_STEP;

      const tic_t max = compute_max();
      LIM_MAX = +max;
      LIM_MIN = -max;
    }

    void
    Time::set_resolution( double_t tics_per_ms, double_t ms_per_step )
    {
      Range::TICS_PER_MS = tics_per_ms;
      Range::MS_PER_TIC = 1 / tics_per_ms;
      set_resolution( ms_per_step );
    }

    void
    Time::reset_resolution()
    {
      // When resetting the kernel, we have to reset OLD_TICS as well,
      // otherwise we get into trouble with regenerated synapse prototypes,
      // see ticket #164.
      Range::OLD_TICS_PER_STEP = Range::TICS_PER_STEP_DEFAULT;
      Range::TICS_PER_STEP = Range::TICS_PER_STEP_DEFAULT;
      Range::TICS_PER_STEP_RND = Range::TICS_PER_STEP - 1;

      const tic_t max = compute_max();
      LIM_MAX = +max;
      LIM_MIN = -max;
    }

    nest::double_t
    Time::ms::fromtoken( const Token& t )
    {
      IntegerDatum* idat = dynamic_cast< IntegerDatum* >( t.datum() );
      if ( idat )
        return static_cast< double_t >( idat->get() );

      DoubleDatum* ddat = dynamic_cast< DoubleDatum* >( t.datum() );
      if ( ddat )
        return ddat->get();

      throw TypeMismatch(
        IntegerDatum().gettypename().toString() + " or " + DoubleDatum().gettypename().toString(),
        t.datum()->gettypename().toString() );
    }

    tic_t
    Time::fromstamp( Time::ms_stamp t )
    {
      if ( t.t > LIM_MAX.ms )
        return LIM_POS_INF.tics;
      else if ( t.t < LIM_MIN.ms )
        return LIM_NEG_INF.tics;

      // why not just fmod STEPS_PER_MS? This gives different
      // results in corner cases --- and I don't think the
      // intended ones.
      tic_t n = static_cast< tic_t >( t.t * Range::TICS_PER_MS );
      n -= ( n % Range::TICS_PER_STEP );
      long_t s = n / Range::TICS_PER_STEP;
      double ms = s * Range::MS_PER_STEP;
      if ( ms < t.t )
        n += Range::TICS_PER_STEP;

      return n;
    }

    void
    Time::reset_to_defaults()
    {
      // reset the TICS_PER_MS to compiled in default values
      Range::TICS_PER_MS = Range::TICS_PER_MS_DEFAULT;
      Range::MS_PER_TIC = 1 / Range::TICS_PER_MS_DEFAULT;

      // reset TICS_PER_STEP to compiled in default values
      Range::TICS_PER_STEP = Range::TICS_PER_STEP_DEFAULT;
      Range::TICS_PER_STEP_RND = Range::TICS_PER_STEP - 1;

      Range::MS_PER_STEP = Range::TICS_PER_STEP / Range::TICS_PER_MS;
      Range::STEPS_PER_MS = 1 / Range::MS_PER_STEP;
    }

    std::ostream& operator<<( std::ostream& strm, const Time& t )
    {
      if ( t.tics == Time::LIM_NEG_INF.tics )
        strm << "-INF";
      else if ( t.tics == Time::LIM_POS_INF.tics )
        strm << "+INF";
      else
        strm << t.get_ms() << " ms (= " << t.get_tics() << " tics = " << t.get_steps()
             << ( t.get_steps() != 1 ? " steps)" : " step)" );

      return strm;
    }

}



