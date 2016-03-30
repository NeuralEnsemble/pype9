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
