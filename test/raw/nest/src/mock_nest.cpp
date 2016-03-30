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



const TokenArray& TokenArray::operator=( const TokenArray& a )
{
  a.data->add_reference(); // protect from a=a
  data->remove_reference();
  data = a.data;

  return *this;
}


TokenArray::TokenArray( const std::vector< long >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token idt( new IntegerDatum( a[ i ] ) );
    ( *data )[ i ].move( idt );
  }
}

TokenArray::TokenArray( const std::vector< size_t >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token idt( new IntegerDatum( a[ i ] ) );
    ( *data )[ i ].move( idt );
  }
}

TokenArray::TokenArray( const std::vector< double >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token ddt( new DoubleDatum( a[ i ] ) );
    ( *data )[ i ].move( ddt );
  }
}

TokenArray::TokenArray( const std::valarray< long >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token ddt( new IntegerDatum( a[ i ] ) );
    ( *data )[ i ].move( ddt );
  }
}

TokenArray::TokenArray( const std::valarray< double >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token ddt( new DoubleDatum( a[ i ] ) );
    ( *data )[ i ].move( ddt );
  }
}

TokenArray::TokenArray( const std::valarray< float >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token ddt( new DoubleDatum( a[ i ] ) );
    ( *data )[ i ].move( ddt );
  }
}

TokenArray::TokenArray( const std::vector< float >& a )
  : data( new TokenArrayObj( a.size(), Token(), 0 ) )
{
  assert( data != NULL );
  for ( size_t i = 0; i < a.size(); ++i )
  {
    Token ddt( new DoubleDatum( a[ i ] ) );
    ( *data )[ i ].move( ddt );
  }
}


void
TokenArray::toVector( std::vector< long >& a ) const
{
  a.clear();
  a.reserve( size() );
  for ( Token* idx = begin(); idx != end(); ++idx )
  {
    IntegerDatum* targetid = dynamic_cast< IntegerDatum* >( idx->datum() );
    if ( targetid == NULL )
    {
      IntegerDatum const d;
      throw TypeMismatch( d.gettypename().toString(), idx->datum()->gettypename().toString() );
    }

    a.push_back( targetid->get() );
  }
}

void
TokenArray::toVector( std::vector< size_t >& a ) const
{
  a.clear();
  a.reserve( size() );
  for ( Token* idx = begin(); idx != end(); ++idx )
  {
    IntegerDatum* targetid = dynamic_cast< IntegerDatum* >( idx->datum() );
    if ( targetid == NULL )
    {
      IntegerDatum const d;
      throw TypeMismatch( d.gettypename().toString(), idx->datum()->gettypename().toString() );
    }

    a.push_back( targetid->get() );
  }
}

void
TokenArray::toVector( std::vector< double >& a ) const
{
  a.clear();
  a.reserve( size() );
  for ( Token* idx = begin(); idx != end(); ++idx )
  {
    DoubleDatum* targetid = dynamic_cast< DoubleDatum* >( idx->datum() );
    if ( targetid == NULL )
    {
      DoubleDatum const d;
      throw TypeMismatch( d.gettypename().toString(), idx->datum()->gettypename().toString() );
    }
    a.push_back( targetid->get() );
  }
}

void
TokenArray::toVector( std::vector< std::string >& a ) const
{
  a.clear();
  a.reserve( size() );
  for ( Token* idx = begin(); idx != end(); ++idx )
  {
    std::string* target = dynamic_cast< std::string* >( idx->datum() );
    if ( target == NULL )
    {
      StringDatum const d;
      throw TypeMismatch( d.gettypename().toString(), idx->datum()->gettypename().toString() );
    }
    a.push_back( *target );
  }
}

void
TokenArray::toValarray( std::valarray< long >& a ) const
{
  a.resize( size() );
  size_t i = 0;

  for ( Token* idx = begin(); idx != end(); ++idx, ++i )
  {
    IntegerDatum* targetid = dynamic_cast< IntegerDatum* >( idx->datum() );
    if ( targetid == NULL )
    {
      IntegerDatum const d;
      throw TypeMismatch( d.gettypename().toString(), idx->datum()->gettypename().toString() );
    }
    a[ i ] = targetid->get();
  }
}

void
TokenArray::toValarray( std::valarray< double >& a ) const
{
  a.resize( size() );
  size_t i = 0;

  for ( Token* idx = begin(); idx != end(); ++idx, ++i )
  {
    DoubleDatum* targetid = dynamic_cast< DoubleDatum* >( idx->datum() );
    if ( targetid == NULL )
    {
      DoubleDatum const d;
      throw TypeMismatch( d.gettypename().toString(), idx->datum()->gettypename().toString() );
    }
    a[ i ] = targetid->get();
  }
}

bool
TokenArray::valid( void ) const
{
  if ( data == NULL )
  {
    return false;
  }
  return data->valid();
}


std::ostream& operator<<( std::ostream& out, const TokenArray& a )
{

  for ( Token* t = a.begin(); t < a.end(); ++t )
    out << *t << ' ';

  return out;
}


size_t TokenArrayObj::allocations = 0;

TokenArrayObj::TokenArrayObj( size_t s, const Token& t, size_t alloc )
  : p( NULL )
  , begin_of_free_storage( NULL )
  , end_of_free_storage( NULL )
  , alloc_block_size( ARRAY_ALLOC_SIZE )
  , refs_( 1 )
{
  size_t a = ( alloc == 0 ) ? s : alloc;

  resize( s, a, t );
}


TokenArrayObj::TokenArrayObj( const TokenArrayObj& a )
  : p( NULL )
  , begin_of_free_storage( NULL )
  , end_of_free_storage( NULL )
  , alloc_block_size( ARRAY_ALLOC_SIZE )
  , refs_( 1 )
{
  if ( a.p != NULL )
  {
    resize( a.size(), a.alloc_block_size, Token() );
    Token* from = a.p;
    Token* to = p;

    while ( to < begin_of_free_storage )
      *to++ = *from++;
  }
}


TokenArrayObj::~TokenArrayObj()
{
  if ( p )
    delete[] p;
}

void
TokenArrayObj::allocate( size_t new_s, size_t new_c, size_t new_a, const Token& t )
{
  // This resize function is private and does an unconditional resize, using
  // all supplied parameters.

  alloc_block_size = new_a;

  size_t old_s = size();

  assert( new_c != 0 );
  assert( new_a != 0 );

  Token* h = new Token[ new_c ];
  assert( h != NULL );

  if ( t != Token() )
    for ( Token* hi = h; hi < h + new_c; ++hi )
      ( *hi ) = t;

  end_of_free_storage = h + new_c; // [,) convention
  begin_of_free_storage = h + new_s;

  if ( p != NULL )
  {

    size_t min_l;

    if ( old_s < new_s )
    {
      min_l = old_s;
    }
    else
    {
      min_l = new_s;
    }

    for ( size_t i = 0; i < min_l; ++i ) // copy old parts
      h[ i ].move( p[ i ] );
    delete[] p;
  }
  p = h;
  assert( p != NULL );

  ++allocations;
}

void
TokenArrayObj::resize( size_t s, size_t alloc, const Token& t )
{
  alloc_block_size = ( alloc == 0 ) ? alloc_block_size : alloc;

  if ( ( s != size() && ( s != 0 ) ) || ( size() == 0 && alloc_block_size != 0 ) )
    allocate( s, s + alloc_block_size, alloc_block_size, t );
}

void
TokenArrayObj::resize( size_t s, const Token& t )
{
  resize( s, alloc_block_size, t );
}

const TokenArrayObj& TokenArrayObj::operator=( const TokenArrayObj& a )
{
  if ( capacity() >= a.size() )
  // This branch also covers the case where a is the null-vector.
  {
    Token* to = begin();
    Token* from = a.begin();
    while ( from < a.end() )
      *to++ = *from++;

    while ( to < end() )
    {
      to->clear();
      to++;
    }
    begin_of_free_storage = p + a.size();

    assert( begin_of_free_storage <= end_of_free_storage );
  }
  else
  {

    if ( p != NULL )
    {
      delete[] p;
      p = NULL;
    }

    resize( a.size(), a.alloc_block_size );
    Token* to = begin();
    Token* from = a.begin();
    while ( from < a.end() )
      *to++ = *from++;
    begin_of_free_storage = to;
    assert( begin_of_free_storage <= end_of_free_storage );
  }

  return *this;
}


// re-allocate, if the actual buffer is larger
// than alloc_block_size

// bool TokenArrayObj::shrink(void)
// {
//     static const size_t hyst=1;
//     size_t old_size = size();

//     size_t n = old_size/alloc_block_size + 1 + hyst;
//     size_t new_capacity = n*alloc_block_size;

//     if( new_capacity < capacity())
//     {
//       allocate(old_size, new_capacity, alloc_block_size);
//       return true;
//     }
//     return false;
// }

bool
TokenArrayObj::shrink( void )
{
  size_t new_capacity = size();

  if ( new_capacity < capacity() )
  {
    allocate( size(), new_capacity, alloc_block_size );
    return true;
  }
  return false;
}

bool
TokenArrayObj::reserve( size_t new_capacity )
{
  if ( new_capacity > capacity() )
  {
    allocate( size(), new_capacity, alloc_block_size );
    return true;
  }
  return false;
}


void
TokenArrayObj::rotate( Token* first, Token* middle, Token* last )
{

  // This algorithm is taken from the HP STL implementation.
  if ( ( first < middle ) && ( middle < last ) )
    for ( Token* i = middle;; )
    {

      first->swap( *i );
      i++;
      first++;

      if ( first == middle )
      {
        if ( i == last )
          return;
        middle = i;
      }
      else if ( i == last )
        i = middle;
    }
}

void
TokenArrayObj::erase( Token* first, Token* last )
{
  // this algorithm we also use in replace_move
  // array is decreasing. we move elements after point of
  // erasure from right to left
  Token* from = last;
  Token* to = first;
  Token* end = begin_of_free_storage; // 1 ahead  as conventional

  while ( from < end )
  {
    if ( to->p )
      to->p->removeReference(); // deleting NULL pointer is safe in ISO C++
    to->p = from->p;            // move
    from->p = NULL;             // might be overwritten or not
    ++from;
    ++to;
  }

  while ( last > to ) // if sequence we have to erase is
  {                   // longer than the sequence to the
    --last;           // right of it, we explicitly delete the
    if ( last->p )
      last->p->removeReference(); // elements which are still intact
    last->p = NULL;               // after the move above.
  }

  begin_of_free_storage = to;
}

// as for strings erase tolerates i+n >=  size()
//
void
TokenArrayObj::erase( size_t i, size_t n )
{
  if ( i + n < size() )
    erase( p + i, p + i + n );
  else
    erase( p + ( i ), p + size() );
}

void
TokenArrayObj::clear( void )
{
  if ( p )
    delete[] p;
  p = begin_of_free_storage = end_of_free_storage = NULL;
  alloc_block_size = 1;
}

// reduce() could be further optimized by testing wether the
// new size leads to a resize. In this case, one could simply
// re-construct the array with the sub-array.

void
TokenArrayObj::reduce( Token* first, Token* last )
{
  assert( last <= end() );
  assert( first >= p );

  // First step: shift all elements to the begin of
  // the array.
  Token *i = p, *l = first;

  if ( first > begin() )
  {
    while ( l < last )
    {
      i->move( *l );
      i++;
      l++;
    }
    assert( l == last );
  }
  else
    i = last;

  assert( i == p + ( last - first ) );

  while ( i < end() )
  {
    i->clear();
    i++;
  }
  begin_of_free_storage = p + ( size_t )( last - first );
  // shrink();
}

// as assign for strings reduce tolerates i+n >= size()
//
void
TokenArrayObj::reduce( size_t i, size_t n )
{
  if ( i + n < size() )
    reduce( p + i, p + i + n );
  else
    reduce( p + ( i ), p + size() );
}

void
TokenArrayObj::insert( size_t i, size_t n, const Token& t )
{
  // pointer argument pos would not be efficient because we
  // have to recompute pointer anyway after reallocation

  reserve( size() + n ); // reallocate if necessary

  Token* pos = p + i;                      // pointer to element i (starting with 0)
  Token* from = begin_of_free_storage - 1; // first Token which has to be moved
  Token* to = from + n;                    // new location of first Token

  while ( from >= pos )
  {
    to->p = from->p; // move
    from->p = NULL;  // knowing that to->p is
    --from;
    --to; // NULL before
  }

  for ( size_t i = 0; i < n; ++i ) // insert n copies of Token t;
    *( pos++ ) = t;

  begin_of_free_storage += n; // new size is old + n
}

void
TokenArrayObj::insert_move( size_t i, TokenArrayObj& a )
{
  reserve( size() + a.size() );                                      // reallocate if necessary
  assert( begin_of_free_storage + a.size() <= end_of_free_storage ); // check

  Token* pos = p + i;                      // pointer to element i (starting with 0)
  Token* from = begin_of_free_storage - 1; // first Token which has to be moved
  Token* to = from + a.size();             // new location of first Token


  while ( from >= pos )
  {
    to->p = from->p; // move
    from->p = NULL;  // knowing that to->p is
    --from;
    --to; // NULL before
  }

  from = a.p;
  to = p + i;

  while ( from < a.end() )
  {
    to->p = from->p; // we cannot do this in the loop
    from->p = NULL;  // above because of overlapping
    ++from;
    ++to;
  }

  begin_of_free_storage += a.size(); // new size is old + n
  a.begin_of_free_storage = a.p;     // a is empty.
}

void
TokenArrayObj::assign_move( TokenArrayObj& a, size_t i, size_t n )
{
  reserve( n );

  Token* from = a.begin() + i;
  Token* end = a.begin() + i + n;
  Token* to = p;

  while ( from < end )
  {
    to->p = from->p;
    from->p = NULL;
    ++from;
    ++to;
  }

  begin_of_free_storage = p + n;
}

void
TokenArrayObj::assign( const TokenArrayObj& a, size_t i, size_t n )
{
  reserve( n );

  Token* from = a.begin() + i;
  Token* end = a.begin() + i + n;
  Token* to = p;

  while ( from < end )
  {
    *to = *from;
    ++from;
    ++to;
  }

  begin_of_free_storage = p + n;
}

void
TokenArrayObj::insert_move( size_t i, Token& t )
{
  reserve( size() + 1 );                                      // reallocate if necessary
  assert( begin_of_free_storage + 1 <= end_of_free_storage ); // check

  Token* pos = p + i;                      // pointer to element i (starting with 0)
  Token* from = begin_of_free_storage - 1; // first Token which has to be moved
  Token* to = from + 1;                    // new location of first Token


  while ( from >= pos )
  {
    to->p = from->p; // move
    from->p = NULL;  // knowing that to->p is
    --from;
    --to; // NULL before
  }

  ( p + i )->p = t.p; // move contens of t
  t.p = NULL;

  begin_of_free_storage += 1; // new size is old + 1
}


void
TokenArrayObj::replace_move( size_t i, size_t n, TokenArrayObj& a )
{
  assert( i < size() );                        // assume index in range
  n = ( size() - i < n ) ? ( size() - i ) : n; // n more than available is allowed


  long d = a.size() - n; // difference size after the replacement,
                         // positive for increase

  reserve( size() + d ); // reallocate if necessary


  if ( d > 0 )
  {
    // array is increasing. we move elements after point of
    // replacement from left to right
    Token* from = begin_of_free_storage - 1;
    Token* to = begin_of_free_storage - 1 + d;
    Token* end = p + i + n - 1; // 1 ahead (before)  as conventional

    while ( from > end )
    {
      to->p = from->p; // move
      from->p = NULL;  // might be overwritten or not
      --from;
      --to;
    }
  }
  else if ( d < 0 )
  {
    // array is decreasing. we move elements after point of
    // replacement from right to left
    Token* last = p + i + n;
    Token* from = last;
    Token* to = p + i + a.size();
    Token* end = begin_of_free_storage; // 1 ahead  as conventional

    while ( from < end )
    {
      if ( to->p )
        to->p->removeReference(); // deleting NULL pointer is safe in ISO C++
      to->p = from->p;            // move
      from->p = NULL;             // might be overwritten or not
      ++from;
      ++to;
    }

    while ( last > to ) // if sequence we have to erase is
    {                   // longer than a plus the sequence to the
      --last;           // right of it, we explicitly delete the
      if ( last->p )
        last->p->removeReference(); // elements which are still intact
      last->p = NULL;               // after the move above.
    }
  }

  begin_of_free_storage += d; // set new size


  // move contens of array a
  Token* to = p + i;
  Token* end = a.end(); // 1 ahead as conventional
  Token* from = a.begin();

  while ( from < end )
  {
    if ( to->p )
      to->p->removeReference(); // delete target before
    to->p = from->p;            // movement, it is typically
    from->p = NULL;             // not the NULL pointer
    ++from;
    ++to;
  }
}

void
TokenArrayObj::append_move( TokenArrayObj& a )
{
  reserve( size() + a.size() );                                      // reallocate if necessary
  assert( begin_of_free_storage + a.size() <= end_of_free_storage ); // check

  Token* from = a.p;
  Token* to = begin_of_free_storage;

  while ( from < a.end() ) // move
  {                        // knowing that to->p is
    to->p = from->p;       // NULL before
    from->p = NULL;
    ++from;
    ++to;
  }

  begin_of_free_storage += a.size(); // new size is old + n
  a.begin_of_free_storage = a.p;     // a is empty.
}


bool TokenArrayObj::operator==( const TokenArrayObj& a ) const
{

  // std::cout << "comparison of TokenArrayObj" << std::endl;
  // std::cout << "p:   " << p << std::endl;
  // std::cout << "a.p: " << a.p << std::endl;

  if ( p == a.p )
    return true;

  // experimentally replaced by line below 090120, Diesmann
  // because [] cvx has non NULL p
  //
  //    if( p == NULL || a.p == NULL || size() != a.size())
  //    return false;

  if ( size() != a.size() )
    return false;

  Token *i = begin(), *j = a.begin();
  while ( i < end() )
    if ( !( *i++ == *j++ ) )
      return false;
  return true;
}

void
TokenArrayObj::info( std::ostream& out ) const
{
  out << "TokenArrayObj::info\n";
  out << "p    = " << p << std::endl;
  out << "bofs = " << begin_of_free_storage << std::endl;
  out << "eofs = " << end_of_free_storage << std::endl;
  out << "abs  = " << alloc_block_size << std::endl;
}

bool
TokenArrayObj::valid( void ) const
{
  if ( p == NULL )
  {
    std::cerr << "TokenArrayObj::valid: Data pointer missing!" << std::endl;
    return false;
  }

  if ( begin_of_free_storage == NULL )
  {
    std::cerr << "TokenArrayObj::valid: begin of free storage pointer missing!" << std::endl;
    return false;
  }

  if ( end_of_free_storage == NULL )
  {
    std::cerr << "TokenArrayObj::valid: end of free storage pointer missing!" << std::endl;
    return false;
  }

  if ( begin_of_free_storage > end_of_free_storage )
  {
    std::cerr << "TokenArrayObj::valid: begin_of_free_storage  > end_of_free_storage !"
              << std::endl;
    return false;
  }

  return true;
}


std::ostream& operator<<( std::ostream& out, const TokenArrayObj& a )
{

  for ( Token* i = a.begin(); i < a.end(); ++i )
    out << *i << ' ';

  return out;
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



