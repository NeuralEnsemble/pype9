#ifndef MOCK_NEST_H
#define MOCK_NEST_H

#include <cmath>
#include <vector>
#include <map>
#include <sstream>
#include <algorithm>
#include <cassert>
#include <valarray>
#include "name.h"

#define ARRAY_ALLOC_SIZE 64
#define LONG_MAX  __LONG_MAX__
#define LONG_MIN  (-__LONG_MAX__ -1L)
#define DBL_MAX __DBL_MAX__
#define LDBL_MAX __LDBL_MAX__
#define double_t_max ( DBL_MAX ) // because C++ language designers are apes
#define double_t_min ( DBL_MIN ) // (only integral consts are compile time)

const Name DOUBLE_TYPE("double");
const Name LONG_TYPE("long");
const Name DICTIONARY_TYPE("dictionary");
const Name ARRAY_TYPE("array");
const Name LITERAL_TYPE("literal");

typedef long long_t;
typedef long_t rport;
typedef long_t port;
typedef double_t weight;
typedef long_t delay;

const long_t long_t_max = __LONG_MAX__;
const long_t long_t_min = (-__LONG_MAX__ -1L);
const long_t delay_max = long_t_max;
const long_t delay_min = long_t_min;
const rport invalid_port_ = -1;

typedef long tic_t;
const tic_t tic_t_max = LONG_MAX;
const tic_t tic_t_min = LONG_MIN;

namespace nest {
    class Time;
}

std::ostream& operator<<( std::ostream&, const nest::Time& );

long ld_round( double x ) {
  return ( long ) std::floor((long double)(x + 0.5));
}

class Datum {

  public:

    Datum(const Name* t) :
            type(t) {
    }

    Datum(const Datum& d) :
            type(d.type) {
    }

    virtual ~Datum() {
    }

    virtual Datum* clone() const = 0;

    virtual bool equals( const Datum* d ) const {
        return this == d;
    }

    virtual Datum* get_ptr() {
      return clone();
    }

    void addReference() const {}
    void removeReference() {}

  protected:
    // Putting the following variables here, avoids a number of virtual
    // functions.

    const Name* type;       //!< Pointer to type object.

};

class Token {
  friend class Datum;

  private:
    Datum* p;

  public:
    ~Token() {
        delete p;
    }

    Token(const Token& t) :
            p( NULL) {
        if (t.p)
            p = t.p->clone();
    }

    Token(Datum* d = NULL) //!< use existing pointer to datum, token takes responsibility of the pointer.
    :
            p(d) {
    }

    Token(const Datum& d) //!< copy datum object and store its pointer.
            {
        p = d.clone();
    }

    Token(int);
    Token(unsigned int);
    Token(long);
    Token(bool);
    Token(unsigned long);
    Token(double);
    Token(const char*);
    Token(std::string);
    Token(const std::vector<double>&);
    Token(const std::vector<long>&);
    Token(const std::vector<size_t>&);
    Token(const std::ostream&);
    Token(const std::istream&);
    operator Datum*() const;
    operator size_t() const;
    operator long() const;
    operator double() const;
    operator float() const;
    operator bool() const;
    operator std::string() const;
    //  operator vector<double> const;
    //  operator vector<long> const;

    void clear(void) {
        delete p;
        p = NULL;
    }

    bool empty(void) const {
        return p == NULL;
    }

    bool operator!(void) const {
        return p == NULL;
    }

    Datum* datum(void) const {
        return p;
    }

    bool valid() const {
        return !empty();
    }

    Datum* operator->() const {
        //      assert(p!= NULL);
        return p;
    }

    Datum& operator*() const {
        //      assert(p != NULL);
        return *p;
    }

    Token& operator=(const Token& t) {
        if (t.p != p) {
            if (t.p == NULL)
                clear();
            else
                p = t.p->clone();
        }
        return *this;
    }

    Token& operator=(Datum* p_s) {
        if (p != p_s) {
            clear();
            p = p_s->clone();
        }

        return *this;
    }

    bool operator==(const Token& t) const {
        if (p == t.p)
            return true;

        return p and p->equals(t.p);
    }

    // define != explicitly --- HEP 2001-08-09
    bool operator!=(const Token& t) const {
        return !(*this == t);
    }


    void move( Token& c ) {
      if ( p )
        p->removeReference();
      p = c.p;
      c.p = NULL;
    }


    /**
     * Initialize the token by moving a datum from another token.
     * This function assumes that the token does not
     * point to a valid datum and that the argument token
     * does point to a valid datum.
     * This function does not change the reference count of the datum.
     */
    void init_move( Token& rhs ) {
      p = rhs.p;
      rhs.p = NULL;
    }

    /**
     * Initialize the token by moving a datum from another token.
     * This function assumes that the token does not
     * point to a valid datum and that the argument token
     * does point to a valid datum.
     * This function does not change the reference count of the datum.
     */
    void init_by_copy( const Token& rhs ) {
      p = rhs.p->get_ptr();
    }

    /**
     * Initialize the token with a reference.
     * This function assumes that the token does not
     * point to a valid datum and that the argument token
     * does point to a valid datum.
     * This function increases the reference count of the argument.
     */

    void init_by_ref( const Token& rhs ) {
      rhs.p->addReference();
      p = rhs.p;
    }

    /**
     * Initialize the token with a datum pointer.
     * This function assumes that the token does not point to
     * a valid datum.
     * The function assumes that the datum is new and DOES NOT increases its reference count.
     */
    void init_by_pointer( Datum* rhs ) {
      p = rhs;
    }

};


class Token;

class TokenArrayObj
{
private:
  Token* p;
  Token* begin_of_free_storage;
  Token* end_of_free_storage;
  unsigned int alloc_block_size;
  unsigned int refs_;

  //  bool homogeneous;

  void allocate( size_t, size_t, size_t, const Token& = Token() );

  static size_t allocations;

public:
  TokenArrayObj( void )
    : p( NULL )
    , begin_of_free_storage( NULL )
    , end_of_free_storage( NULL )
    , alloc_block_size( ARRAY_ALLOC_SIZE )
    , refs_( 1 ){};

  TokenArrayObj( size_t, const Token& = Token(), size_t = 0 );
  TokenArrayObj( const TokenArrayObj& );

  virtual ~TokenArrayObj();

  Token*
  begin() const
  {
    return p;
  }

  Token*
  end() const
  {
    return begin_of_free_storage;
  }

  size_t
  size( void ) const
  {
    return ( size_t )( begin_of_free_storage - p );
  }

  size_t
  capacity( void ) const
  {
    return ( size_t )( end_of_free_storage - p );
  }

  Token& operator[]( size_t i )
  {
    return p[ i ];
  }

  const Token& operator[]( size_t i ) const
  {
    return p[ i ];
  }

  const Token&
  get( long i ) const
  {
    return *( p + i );
    //      return p[i];
  }

  bool
  index_is_valid( long i ) const
  {
    return ( p + i ) < begin_of_free_storage;
  }

  void rotate( Token*, Token*, Token* );


  // Memory allocation

  bool shrink( void );
  bool reserve( size_t );

  unsigned int
  references( void )
  {
    return refs_;
  }

  unsigned int
  remove_reference()
  {
    --refs_;
    if ( refs_ == 0 )
    {
      delete this;
      return 0;
    }

    return refs_;
  }

  unsigned int
  add_reference()
  {
    return ++refs_;
  }

  void resize( size_t, size_t, const Token& = Token() );
  void resize( size_t, const Token& = Token() );

  void
  reserve_token( size_t n )
  {
    if ( capacity() < size() + 1 + n )
      reserve( size() + n );
  }
  // Insertion, deletion
  void
  push_back( const Token& t )
  {
    if ( capacity() < size() + 1 )
      reserve( size() + alloc_block_size );
    ( begin_of_free_storage++ )->init_by_copy( t );
  }

  void
  push_back_move( Token& t )
  {
    if ( capacity() < size() + 1 )
      reserve( size() + alloc_block_size );

    ( begin_of_free_storage++ )->init_move( t );
    //      ++begin_of_free_storage;
  }

  /**
   * Push back a reference.  This function expects that enough space
   * on the stack has been reserved and that the token points to a
   * valid datum object.
   */
  void
  push_back_by_ref( const Token& t )
  {
    if ( capacity() < size() + 1 )
      reserve( size() + alloc_block_size );
    ( begin_of_free_storage++ )->init_by_ref( t );
  }

  /**
   * Push back a datum pointer.  This function assumes that enough
   * space on the stack has been reserved.  This function expects a
   * valid datum pointer and increases the reference count of the
   * datum.
   */
  void
  push_back_by_pointer( Datum* rhs )
  {
    if ( capacity() < size() + 1 )
      reserve( size() + alloc_block_size );
    begin_of_free_storage->init_by_pointer( rhs );
    ++begin_of_free_storage;
  }

  void
  assign_move( Token* tp, Token& t )
  {
    tp->move( t );
  }

  void
  pop_back( void )
  {
    ( --begin_of_free_storage )->clear();
  }

  // Erase the range given by the iterators.
  void erase( size_t, size_t );
  void erase( Token*, Token* );
  void
  erase( Token* tp )
  {
    erase( tp, tp + 1 );
  }

  // Reduce the array to the range given by the iterators
  void reduce( Token*, Token* );
  void reduce( size_t, size_t );

  void insert( size_t, size_t = 1, const Token& = Token() );
  void
  insert( size_t i, const Token& t )
  {
    insert( i, 1, t );
  }

  void insert_move( size_t, TokenArrayObj& );
  void insert_move( size_t, Token& );

  void assign_move( TokenArrayObj&, size_t, size_t );
  void assign( const TokenArrayObj&, size_t, size_t );

  void replace_move( size_t, size_t, TokenArrayObj& );

  void append_move( TokenArrayObj& );

  void clear( void );


  const TokenArrayObj& operator=( const TokenArrayObj& );

  bool operator==( const TokenArrayObj& ) const;

  bool
  empty( void ) const
  {
    return size() == 0;
  }

  void info( std::ostream& ) const;

  static size_t
  getallocations( void )
  {
    return allocations;
  }

  bool valid( void ) const; // check integrity
};

std::ostream& operator<<( std::ostream&, const TokenArrayObj& );


class TokenArray
{
private:
  TokenArrayObj* data;

  bool
  clone( void )
  {
    if ( data->references() > 1 )
    {
      data->remove_reference();
      data = new TokenArrayObj( *data );
      return true;
    }
    else
      return false;
  }

  bool
  detach( void )
  {
    if ( data->references() > 1 )
    {
      data->remove_reference();
      data = new TokenArrayObj();
      return true;
    }
    else
      return false;
  }

protected:
  friend class TokenArrayObj;
  friend class TokenStack;
  operator TokenArrayObj() const
  {
    return *data;
  }

public:
  TokenArray( void )
    : data( new TokenArrayObj() ){};

  explicit TokenArray( size_t n, const Token& t = Token(), size_t alloc = 128 )
    : data( new TokenArrayObj( n, t, alloc ) )
  {
  }

  TokenArray( const TokenArray& a )
    : data( a.data )
  {
    data->add_reference();
  }

  TokenArray( const TokenArrayObj& a )
    : data( new TokenArrayObj( a ) )
  {
  }

  TokenArray( const std::vector< size_t >& );
  TokenArray( const std::vector< long >& );
  TokenArray( const std::valarray< long >& );
  TokenArray( const std::valarray< double >& );
  TokenArray( const std::valarray< float >& );
  TokenArray( const std::vector< double >& );
  TokenArray( const std::vector< float >& );

  virtual ~TokenArray()
  {
    data->remove_reference(); // this will dispose data if needed.
  }

  /**
   * Return pointer to the first element.
   */
  Token*
  begin() const
  {
    return data->begin();
  }

  /**
   * Return pointer to next to last element.
   */
  Token*
  end() const
  {
    return data->end();
  }

  /**
   * Return number of elements in the array.
   */
  size_t
  size( void ) const
  {
    return data->size();
  }

  /**
   * Return maximal number of elements that fit into the container.
   */
  size_t
  capacity( void ) const
  {
    return data->capacity();
  }

  // Note, in order to use the const version of operator[]
  // through a pointer, it is in some cases necessary to
  // use an explicit TokenArray const * pointer!
  // Use the member function get(size_t) const to force
  // constness.

  Token& operator[]( size_t i )
  {
    clone();
    return ( *data )[ i ];
  }

  const Token& operator[]( size_t i ) const
  {
    return ( *data )[ i ];
  }

  const Token&
  get( long i ) const
  {
    return data->get( i );
  }

  bool
  index_is_valid( long i ) const
  {
    return data->index_is_valid( i );
  }

  void
  rotate( Token* t1, Token* t2, Token* t3 )
  {
    size_t s1 = t1 - data->begin();
    size_t s2 = t2 - data->begin();
    size_t s3 = t3 - data->begin();

    clone();
    Token* b = data->begin();

    data->rotate( b + s1, b + s2, b + s3 );
  }

  void rotate( long n );

  // The following two members shrink and reserve do
  // NOT invoke cloning, since they have no immediate
  // consequences.

  /**
   * Reduce allocated space such that size()==capacity().
   * Returns true if the array was resized and false otherwhise.
   * If true is returned, all existing pointers into the array are
   * invalidated.
   */
  bool
  shrink( void )
  {
    return data->shrink();
  }

  /**
   * Reserve space such that after the call the new capacity is n.
   * Returns true, if the container was reallocated. In this case all
   * existing pointers are invalidated.
   */
  bool
  reserve( size_t n )
  {
    return data->reserve( n );
  }

  unsigned int
  references( void )
  {
    return data->references();
  }

  /**
   * Resizes the container to size s.
   * If the new size is larger than the old size, the new space is initialized with t.
   */
  void
  resize( size_t s, const Token& t = Token() )
  {
    clone();
    data->resize( s, t );
  }

  // Insertion, deletion
  void
  push_back( const Token& t )
  {
    clone();
    data->push_back( t );
  }

  void
  push_back( Datum* d )
  {
    Token t( d );
    clone();
    data->push_back_move( t );
  }

  void
  push_back_move( Token& t )
  {
    clone();
    data->push_back_move( t );
  }

  void
  push_back_dont_clone( Token& t )
  {
    data->push_back_move( t );
  }

  void assign_move( size_t i, Token& t ) // 8.4.98 Diesmann
  {
    clone();
    data->assign_move( data->begin() + i, t );
  }

  void
  assign_move( TokenArray& a, size_t i, size_t n )
  {
    clear(); // no cloning, because we overwrite everything
    // This is slightly inefficient, because if a has references,
    // cloning is more expensive than just copying the desired range.
    if ( a.references() == 1 )
      data->assign_move( *( a.data ), i, n );
    else
      data->assign( *( a.data ), i, n );
  }

  void insert_move( size_t i, TokenArray& a ) // 8.4.98 Diesmann
  {
    clone();   // make copy if others point to representation
    a.clone(); // also for a because we are going to empy it
               //      assert(data->refs==1);    // private copy
               //      assert(a.data->refs==1);  // private copy

    data->insert_move( i, *( a.data ) );
    // the representations insert_move moves the
    // the contens of all Tokens in a.data and marks it empty.

    //      assert(a.data->size()==0); // empty, but memory is still allocated incase
    // it will be used again. data->clear() would
    // free the memory. In any case the destructor
    // finally frees the memory.
  }

  void
  insert_move( size_t i, Token& t )
  {
    clone();
    data->insert_move( i, t );
  }


  void
  replace_move( size_t i, size_t n, TokenArray& a )
  {
    clone();
    a.clone();

    data->replace_move( i, n, *( a.data ) );
  }


  void
  append_move( TokenArray& a )
  {
    clone();   // make copy if others point to representation
    a.clone(); // also for a because we are going to empy it

    data->append_move( *( a.data ) );
  }

  void
  pop_back( void )
  {
    clone();
    data->pop_back();
  }

  void
  clear( void )
  {
    erase();
  }

  void
  erase( void )
  {
    if ( !detach() )
      erase( begin(), end() );
  }


  void
  erase( Token* from, Token* to )
  {
    if ( from != to )
    {
      size_t sf = from - data->begin();
      size_t st = to - data->begin();

      clone();
      data->erase( data->begin() + sf, data->begin() + st );
    }
  }

  void
  erase( size_t i, size_t n )
  {
    if ( i < size() && n > 0 )
    {
      clone();
      data->erase( i, n );
    }
  }

  // Reduce the Array to the Range given by the iterators
  void
  reduce( size_t i, size_t n )
  {
    if ( i > 0 || n < size() )
    {
      clone();
      data->reduce( i, n );
    }
  }

  void reverse();

  void
  swap( TokenArray& a )
  {
    std::swap( data, a.data );
  }

  const TokenArray& operator=( const TokenArray& );
  const TokenArray& operator=( const std::vector< long >& );
  const TokenArray& operator=( const std::vector< double >& );
  const TokenArray& operator=( const std::valarray< long >& );
  const TokenArray& operator=( const std::valarray< double >& );

  bool operator==( const TokenArray& a ) const
  {
    return *data == *a.data;
  }

  bool
  empty( void ) const
  {
    return size() == 0;
  }

  void info( std::ostream& ) const;

  /** Fill vectors with homogenous integer and double arrays */

  void toVector( std::vector< size_t >& ) const;
  void toVector( std::vector< long >& ) const;
  void toVector( std::vector< double >& ) const;
  void toVector( std::vector< std::string >& ) const;
  void toValarray( std::valarray< long >& ) const;
  void toValarray( std::valarray< double >& ) const;

  bool valid( void ) const; // check integrity

  /** Exception classes */
  //  class TypeMismatch {};
  class OutOfRange
  {
  };
};


class Dictionary {
  public:

    const Token& operator[](const Name&) const;
    Token& operator[](const Name&);

    const Token& operator[](const char*) const;
    Token& operator[](const char*);

    Token& insert(const Name& n, const Token& t);
    Token& insert_move(const Name&, Token&);
    const Token& lookup(const Name& n) const;
};


class DictionaryDatum: public Datum {
  public:

    DictionaryDatum(Dictionary* dict) :
            Datum(&DICTIONARY_TYPE), dict(dict) {
    }

    Dictionary* operator->() const {
        return dict;
    }

    Dictionary* operator->() {
        return dict;
    }

    Dictionary& operator*() {
        return *dict;
    }

    Datum* clone() const {
        return new DictionaryDatum(dict);
    }

  protected:
    Dictionary* dict;
};

class DoubleDatum : public Datum {
  public:

    DoubleDatum(double dbl)
      : Datum(&DOUBLE_TYPE), dbl(dbl) {
      }

    const double* operator->() const {
        return &dbl;
    }

    double* operator->() {
        return &dbl;
    }

    double operator*() {
        return dbl;
    }

    Datum* clone() const {
        return new DoubleDatum(dbl);
    }

    double get() const {
        return dbl;
    }

  protected:
    double dbl;

};

class IntegerDatum : public Datum {
  public:

    IntegerDatum(long lng)
      : Datum(&LONG_TYPE), lng(lng) {
      }

    const long* operator->() const {
        return &lng;
    }

    long* operator->() {
        return &lng;
    }

    long& operator*() {
        return lng;
    }

    Datum* clone() const {
      return new IntegerDatum(lng);
    }

    long get() const {
        return lng;
    }

  protected:
    long lng;

};

class ArrayDatum : public Datum, public TokenArray {

  public:

    ArrayDatum()
      : Datum(&ARRAY_TYPE) {
    }

    Datum* clone() const {
        return new ArrayDatum();
    }

};

class LiteralDatum : public Datum, public Name {

  public:
    Datum* clone( void ) const {
        return new LiteralDatum( *this );
    }

    Datum* get_ptr() {
        Datum::addReference();
        return this;
    }

    LiteralDatum( const Name& n ) : Datum(&LITERAL_TYPE), Name(n) {}
    LiteralDatum( const LiteralDatum& n) : Datum(&LITERAL_TYPE), Name(n) {}
};


template<typename FT> void def(DictionaryDatum& d, Name const n, FT const& value) {
    Token t(value); // we hope that we have a constructor for this.
    d->insert_move(n, t);
}

template < typename FT > FT getValue( const Token& t ) {
  FT* value = dynamic_cast< FT* >( t.datum() );
  if ( value == NULL )
      throw std::exception();
  return *value;
}

template < typename FT > void setValue( const Token& t, FT const& value ) {
  FT* old = dynamic_cast< FT* >( t.datum() );
  if ( value == NULL )
      throw std::exception();
  *old = value;
}

template < typename FT > Token newToken( FT const& value );

template <> double getValue< double >( const Token& t ) {
    DoubleDatum* id = dynamic_cast< DoubleDatum* >( t.datum() );
    if ( id == NULL )
        throw std::exception();
    return id->get();
}
template <> void setValue< double >( const Token& t, double const& value ) {
    DoubleDatum* id = dynamic_cast< DoubleDatum* >( t.datum() );
    if ( id == NULL )
        throw std::exception();
    (*id) = value;
}


template <> long getValue< long >( const Token& t ) {
  const IntegerDatum* id = dynamic_cast< const IntegerDatum* >( t.datum() );
  if ( id == NULL )
    throw std::exception();
  return id->get();
}
template <> void setValue< long >( const Token& t, long const& value ) {
    IntegerDatum* id = dynamic_cast< IntegerDatum* >( t.datum() );
    if ( id == NULL )
        throw std::exception();
    (*id) = value;
}

template <> Token newToken< long >( long const& value ) {
    return Token( new IntegerDatum( value ) );
}


template <> Token newToken< double >( double const& value ) {
    return Token( new DoubleDatum( value ) );
}

template < typename FT, typename VT > bool updateValue( DictionaryDatum const& d, Name const n, VT& value ) {
  // We will test for the name, and do nothing if it does not exist,
  // instead of simply trying to getValue() it and catching a possible
  // exception. The latter works, however, but non-existing names are
  // the rule with updateValue(), not the exception, hence using the
  // exception mechanism would be inappropriate. (Markus pointed this
  // out, 05.02.2001, Ruediger.)

  // We must take a reference, so that access information can be stored in the
  // token.
  const Token& t = d->lookup( n );

  if ( t.empty() )
    return false;

  value = getValue< FT >( t );
  return true;
}

typedef double double_t;


namespace librandom {

    class RngPtr;

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

        RngPtr create_knuthlfg_rng(const unsigned long seed);

        const static unsigned long DefaultSeed;

    };

    class RngPtr {
      public:

        RngPtr() : rng(new RandomGen()) {}

        RngPtr(RandomGen* rng)
          : rng(rng) {}

        RandomGen* operator->() const {
            return rng;
        }

        RandomGen* operator->() {
            return rng;
        }

        RandomGen& operator*() {
            return *rng;
        }

      protected:
        RandomGen* rng;

    };

}


namespace nest {

    typedef double double_t;
    typedef double delay;

    namespace names {
        extern const Name receptor_type;
        extern const Name t_spike;
        extern const Name recordables;
        extern const Name receptor_types;
    }

    typedef int synindex;
    typedef long long_t;
    typedef int port;

    class Node;
    class Archiving_Node;

    class KernelException: public std::exception {
      public:
        KernelException(const std::string& name) {
        }
    };

    class GSLSolverFailure : public KernelException {
      public:
        GSLSolverFailure(const std::string& name, int status) : KernelException(name) {}
    };

    class UnknownReceptorType: public std::exception {
      public:
        UnknownReceptorType(const port& port, const std::string& name) {
        }
    };

    class IncompatibleReceptorType: public std::exception {
      public:
        IncompatibleReceptorType(const port& port,
                const std::string& name, const std::string& msg) {
        }
    };

    class Scheduler {
      public:
        static double get_min_delay() { return min_delay; }
        static double min_delay;
    };

    template < class N > inline N time_abs( const N n ) {
      return std::abs( n );
    }

    template <> inline long long time_abs( long long n ) {
      return llabs( n );
    }

    class Time
    {
      // tic_t: tics in  a step, signed long or long long
      // delay: steps, signed long
      // double_t: milliseconds (double!)

      /////////////////////////////////////////////////////////////
      // Range: Limits & conversion factors for different types
      /////////////////////////////////////////////////////////////

    protected:
      struct Range
      {
        static tic_t TICS_PER_STEP;
        static tic_t TICS_PER_STEP_RND;
        static tic_t OLD_TICS_PER_STEP;

        static double_t TICS_PER_MS;
        static double_t MS_PER_TIC;
        static double_t STEPS_PER_MS;
        static double_t MS_PER_STEP;

        static const tic_t TICS_PER_STEP_DEFAULT;
        static const double_t TICS_PER_MS_DEFAULT;

        static const long_t INF_MARGIN = 8;
      };

    public:
      static tic_t compute_max();

      /////////////////////////////////////////////////////////////
      // The data: longest integer for tics
      /////////////////////////////////////////////////////////////

    protected:
      tic_t tics;

      /////////////////////////////////////////////////////////////
      // Friend declaration for units and binary operators
      /////////////////////////////////////////////////////////////

      friend struct step;
      friend struct tic;
      friend struct ms;
      friend struct ms_stamp;

      friend bool operator==( const Time& t1, const Time& t2 );
      friend bool operator!=( const Time& t1, const Time& t2 );
      friend bool operator<( const Time& t1, const Time& t2 );
      friend bool operator>( const Time& t1, const Time& t2 );
      friend bool operator<=( const Time& t1, const Time& t2 );
      friend bool operator>=( const Time& t1, const Time& t2 );
      friend Time operator+( const Time& t1, const Time& t2 );
      friend Time operator-( const Time& t1, const Time& t2 );
      friend Time operator*( const long_t factor, const Time& t );
      friend Time operator*( const Time& t, long_t factor );
      friend std::ostream&(::operator<<)( std::ostream&, const Time& );

      /////////////////////////////////////////////////////////////
      // Limits for time, including infinity definitions
      /////////////////////////////////////////////////////////////

    protected:
      struct Limit
      {
        tic_t tics;
        delay steps;
        double_t ms;

        Limit( tic_t tics, delay steps, double_t ms )
          : tics( tics )
          , steps( steps )
          , ms( ms )
        {
        }
        Limit( const tic_t& );
      };
      static Limit LIM_MAX;
      static Limit LIM_MIN;
      Time::Limit limit( const tic_t& );

      // max is never larger than tics/INF_MARGIN, and we can use INF_MARGIN
      // to minimize range checks on +/- operations
      static struct LimitPosInf
      {
        static const tic_t tics = tic_t_max / Range::INF_MARGIN + 1;
        static const delay steps = delay_max;
    #define LIM_POS_INF_ms double_t_max // because C++ bites
      } LIM_POS_INF;

      static struct LimitNegInf
      {
        static const tic_t tics = -tic_t_max / Range::INF_MARGIN - 1;
        static const delay steps = -delay_max;
    #define LIM_NEG_INF_ms ( -double_t_max ) // c++ bites
      } LIM_NEG_INF;

      /////////////////////////////////////////////////////////////
      // Unit class for constructors
      /////////////////////////////////////////////////////////////

    public:
      struct tic
      {
        tic_t t;
        explicit tic( tic_t t )
          : t( t ){};
      };

      struct step
      {
        delay t;
        explicit step( delay t )
          : t( t )
        {
        }
      };

      struct ms
      {
        double_t t;

        explicit ms( double_t t )
          : t( t )
        {
        }
        explicit ms( long_t t )
          : t( static_cast< double_t >( t ) )
        {
        }

        static double_t fromtoken( const Token& t );
        explicit ms( const Token& t )
          : t( fromtoken( t ) ){};
      };

      struct ms_stamp
      {
        double_t t;
        explicit ms_stamp( double_t t )
          : t( t )
        {
        }
        explicit ms_stamp( long_t t )
          : t( static_cast< double_t >( t ) )
        {
        }
      };

      /////////////////////////////////////////////////////////////
      // Constructors
      /////////////////////////////////////////////////////////////

    protected:
      explicit Time( tic_t tics )
        : tics( tics )
      {
      } // This doesn't check ranges.
      // Ergo: LIM_MAX.tics >= tics >= LIM_MIN.tics or
      //       tics == LIM_POS_INF.tics or LIM_NEG_INF.tics

    public:
      Time()
        : tics( 0 ){};

      // Default copy constructor: assumes legal time object
      // Defined by compiler.
      // Time(const Time& t);

      Time( tic t )
        : tics( ( time_abs( t.t ) < LIM_MAX.tics ) ? t.t : ( t.t < 0 ) ? LIM_NEG_INF.tics
                                                                       : LIM_POS_INF.tics )
      {
      }

      Time( step t )
        : tics( ( time_abs( t.t ) < LIM_MAX.steps ) ? t.t * Range::TICS_PER_STEP : ( t.t < 0 )
                ? LIM_NEG_INF.tics
                : LIM_POS_INF.tics )
      {
      }

      Time( ms t )
        : tics( ( time_abs( t.t ) < LIM_MAX.ms )
              ? static_cast< tic_t >( t.t * Range::TICS_PER_MS + 0.5 )
              : ( t.t < 0 ) ? LIM_NEG_INF.tics : LIM_POS_INF.tics )
      {
      }

      static tic_t fromstamp( ms_stamp );
      Time( ms_stamp t )
        : tics( fromstamp( t ) )
      {
      }

      /////////////////////////////////////////////////////////////
      // Resolution: set tics per ms, steps per ms
      /////////////////////////////////////////////////////////////

      static void set_resolution( double_t tics_per_ms );
      static void set_resolution( double_t tics_per_ms, double_t ms_per_step );
      static void reset_resolution();
      static void reset_to_defaults();

      static Time
      get_resolution()
      {
        return Time( Range::TICS_PER_STEP );
      }

      static bool
      resolution_is_default()
      {
        return Range::TICS_PER_STEP == Range::TICS_PER_STEP_DEFAULT;
      }

      /////////////////////////////////////////////////////////////
      // Common zero-ary or unary operations
      /////////////////////////////////////////////////////////////

      void
      set_to_zero()
      {
        tics = 0;
      }

      void
      advance()
      {
        tics += Range::TICS_PER_STEP;
        range();
      }

      Time
      succ() const
      {
        return tic( tics + Range::TICS_PER_STEP );
      } // check range
      Time
      pred() const
      {
        return tic( tics - Range::TICS_PER_STEP );
      } // check range

      /////////////////////////////////////////////////////////////
      // Subtypes of Time (bool tests)
      /////////////////////////////////////////////////////////////

      bool
      is_finite() const
      {
        return tics != LIM_POS_INF.tics && tics != LIM_NEG_INF.tics;
      }

      bool
      is_neg_inf() const
      {
        return tics == LIM_NEG_INF.tics;
      }

      bool
      is_grid_time() const
      {
        return ( tics % Range::TICS_PER_STEP ) == 0;
      }
      bool
      is_step() const
      {
        return tics > 0 && is_grid_time();
      }

      bool
      is_multiple_of( const Time& divisor ) const
      {
        assert( divisor.tics > 0 );
        return ( tics % divisor.tics ) == 0;
      }

      /////////////////////////////////////////////////////////////
      // Singleton'ish types
      /////////////////////////////////////////////////////////////

      static Time
      max()
      {
        return Time( LIM_MAX.tics );
      }
      static Time
      min()
      {
        return Time( LIM_MIN.tics );
      }
      static double_t
      get_ms_per_tic()
      {
        return Range::MS_PER_TIC;
      }
      static Time
      neg_inf()
      {
        return Time( LIM_NEG_INF.tics );
      }
      static Time
      pos_inf()
      {
        return Time( LIM_POS_INF.tics );
      }

      /////////////////////////////////////////////////////////////
      // Overflow checks & recalibrate after resolution setting
      /////////////////////////////////////////////////////////////

      void
      range()
      {
        if ( time_abs( tics ) < LIM_MAX.tics )
          return;
        tics = ( tics < 0 ) ? LIM_NEG_INF.tics : LIM_POS_INF.tics;
      }

      void
      calibrate()
      {
        range();
      }

      /////////////////////////////////////////////////////////////
      // Unary operators
      /////////////////////////////////////////////////////////////

      Time& operator+=( const Time& t )
      {
        tics += t.tics;
        range();
        return *this;
      }

      /////////////////////////////////////////////////////////////
      // Convert to external units
      /////////////////////////////////////////////////////////////

      tic_t
      get_tics() const
      {
        return tics;
      }
      static tic_t
      get_tics_per_step()
      {
        return Range::TICS_PER_STEP;
      }
      static double_t
      get_tics_per_ms()
      {
        return Range::TICS_PER_MS;
      }

      double_t
      get_ms() const
      {
        if ( tics == LIM_POS_INF.tics )
          return LIM_POS_INF_ms;
        if ( tics == LIM_NEG_INF.tics )
          return LIM_NEG_INF_ms;
        return Range::MS_PER_TIC * tics;
      }

      delay
      get_steps() const
      {
        if ( tics == LIM_POS_INF.tics )
          return LIM_POS_INF.steps;
        if ( tics == LIM_NEG_INF.tics )
          return LIM_NEG_INF.steps;

        // round tics up to nearest step
        // by adding TICS_PER_STEP-1 before division
        return ( tics + Range::TICS_PER_STEP_RND ) / Range::TICS_PER_STEP;
      }

      /**
       * Convert between delays given in steps and milliseconds.
       * This is not a reversible operation, since steps have a finite
       * rounding resolution. This is not a truncation, but rounding as per ld_round,
       * which is different from ms_stamp --> Time mapping, which rounds
       * up. See #903.
       */
      static double_t
      delay_steps_to_ms( delay steps )
      {
        return steps * Range::MS_PER_STEP;
      }

      static delay
      delay_ms_to_steps( double_t ms )
      {
        return ld_round( ms * Range::STEPS_PER_MS );
      }
    };

    /////////////////////////////////////////////////////////////
    // Non-class definitions
    /////////////////////////////////////////////////////////////

    // Needs to be outside the class to get internal linkage to
    // maybe make the zero visible for optimization.
    const Time TimeZero;

    /////////////////////////////////////////////////////////////
    // Binary operators
    /////////////////////////////////////////////////////////////

    inline bool operator==( const Time& t1, const Time& t2 )
    {
      return t1.tics == t2.tics;
    }

    inline bool operator!=( const Time& t1, const Time& t2 )
    {
      return t1.tics != t2.tics;
    }

    inline bool operator<( const Time& t1, const Time& t2 )
    {
      return t1.tics < t2.tics;
    }

    inline bool operator>( const Time& t1, const Time& t2 )
    {
      return t1.tics > t2.tics;
    }

    inline bool operator<=( const Time& t1, const Time& t2 ) {
      return t1.tics <= t2.tics;
    }

    inline bool operator>=( const Time& t1, const Time& t2 ) {
      return t1.tics >= t2.tics;
    }

    inline Time operator+( const Time& t1, const Time& t2 ) {
      return Time::tic( t1.tics + t2.tics ); // check range
    }

    inline Time operator-( const Time& t1, const Time& t2 ) {
      return Time::tic( t1.tics - t2.tics ); // check range
    }

    inline Time operator*( const long_t factor, const Time& t ) {
      const tic_t n = factor * t.tics;
      // if no overflow:
      if ( t.tics == 0 || n / t.tics == factor )
        return Time::tic( n ); // check range

      if ( ( t.tics > 0 && factor > 0 ) || ( t.tics < 0 && factor < 0 ) )
        return Time( Time::LIM_POS_INF.tics );
      else
        return Time( Time::LIM_NEG_INF.tics );
    }

    inline Time operator*( const Time& t, long_t factor ) {
      return factor * t;
    }



    class Event {
      public:
        Event() : d_(0), w_(0), rp_(0) {}
        void set_sender(Archiving_Node& node) {}
        double_t get_delay() const { return d_; }
        double get_weight() const { return w_; }
        int get_rel_delivery_steps(const Time& time) const;
        int get_rport() const { return rp_; }

        // Public members
        delay d_;
        weight w_;
        int rp_;
    };

    class SpikeEvent : public Event {
      public:
        SpikeEvent() : m_(0) {}
        void set_multiplicity(long_t m) { m_ = m; }
        double_t get_delay() const { return d_; }
        double get_weight() const { return w_; }

        // Public members
        long_t m_;

    };

    class CurrentEvent : public Event {
      public:
        CurrentEvent() : c_(0.0) {}
        double get_current() const { return c_; }

        //Public members
        double c_;

    };

    class DataLoggingRequest {
      public:
        void handle(const SpikeEvent& e) {}
        void handle(const CurrentEvent& e) {}
    };


    template<class NodeType> class RecordablesMap : public std::map< Name, double_t> {
        typedef std::map< Name, double_t> Base_;
      public:
        typedef double_t ( NodeType::*DataAccessFct )() const;

        ArrayDatum get_list() const {
          ArrayDatum recordables;
          for ( typename Base_::const_iterator it = this->begin(); it != this->end(); ++it )
            recordables.push_back( new LiteralDatum( it->first ) );
          return recordables;

          // the entire function should just be
          // return recordables_;
        }
        void create() {}
        void insert_(const char* name, DataAccessFct f) {}
    };

    template<class NodeType> class UniversalDataLogger {
      public:
        UniversalDataLogger(NodeType& node) {}
        port connect_logging_device(DataLoggingRequest& request,
                RecordablesMap<NodeType>& map);
        void init() {}
        void reset() {}
        void record_data(long_t step) {}
        void handle(const DataLoggingRequest& dlr) {}
    };

    class RingBuffer {
      public:
        void add_value(const long_t offs, const double_t);
        void set_value(const long_t offs, const double_t);
        double get_value(const long_t offs);
        void clear();
        void resize();
    };


    class Network {
      public:
        Network();
        ~Network();
        void send(Node& node, SpikeEvent& se, long_t lag) {}
        librandom::RngPtr get_rng(int dummy) { return rng_; }
        Time get_slice_origin();
        librandom::RngPtr rng_;
    };

    class Node {
      public:
        Node() : net_(new Network()) {}
        virtual ~Node() { delete net_; }
        void handle(SpikeEvent& event);
        void handle(CurrentEvent& event);
        port handles_test_event(nest::SpikeEvent& event, nest::port receptor_type);
        port handles_test_event(nest::CurrentEvent& event, nest::port receptor_type);

        std::string get_name() { return "TestNode"; }
        void set_spiketime(Time const& t_sp ) {}
        int get_thread() const { return 0; }

        template < typename ConcreteNode > const ConcreteNode& downcast( const Node& n ) {
          ConcreteNode const* tp = dynamic_cast< ConcreteNode const* >( &n );
          assert( tp != 0 );
          return *tp;
        }

        Network* network() { return net_; }

      protected:
        Network *net_;

    };

    class Archiving_Node: public Node {
      public:
        Archiving_Node() : last_spike_(-1.0) {}
        virtual ~Archiving_Node() {}
        virtual void get_status(DictionaryDatum& d) const = 0;
        virtual void set_status(const DictionaryDatum& d) = 0;
        double_t get_spiketime_ms() const { return last_spike_; }
        void set_spiketime_ms(double_t st) { last_spike_ = st; }
        void clear_history() {}

        double_t last_spike_;

    };

}


#endif
