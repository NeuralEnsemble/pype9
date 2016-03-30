#ifndef MOCKSLI_H
#define MOCKSLI_H

#include <vector>
#include "name.h"

const Name DOUBLE_TYPE("double");
const Name LONG_TYPE("long");
const Name DICTIONARY_TYPE("dictionary");
const Name ARRAY_TYPE("array");
const Name STRING_TYPE("string");
const Name LITERAL_TYPE("literal");

class TypeMismatch : public std::exception {
  std::string expected_;
  std::string provided_;

public:
  ~TypeMismatch() throw() {}

  TypeMismatch() {}

  TypeMismatch(const std::string& expectedType)
    : expected_(expectedType) { }

  TypeMismatch(const std::string& expectedType, const std::string& providedType)
    : expected_( expectedType ), provided_( providedType ) {}

  std::string message();
};

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
    virtual void print( std::ostream& o ) const = 0;
    virtual void pprint( std::ostream& o ) const = 0;
    const Name& gettypename() const {
      return *type;
    }

  protected:
    // Putting the following variables here, avoids a number of virtual
    // functions.

    const Name* type;       //!< Pointer to type object.

};

class Token {
  friend class Datum;
  friend class TokenArrayObj;

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


    void swap( Token& c ) {
        std::swap( p, c.p );
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

std::ostream& operator<<( std::ostream&, const Token& );

typedef std::map< Name, Token, std::less< Name > > TokenMap;

class Dictionary : private TokenMap {
  public:

    const Token& operator[](const Name&) const;
    Token& operator[](const Name&);

    const Token& operator[](const char*) const;
    Token& operator[](const char*);

    Token& insert(const Name& n, const Token& t);
    Token& insert_move(const Name&, Token&);
    const Token& lookup(const Name& n) const;
    static const Token VoidToken;
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

    void print( std::ostream& o ) const {
      o << dict;
    }

    void pprint( std::ostream& o ) const {
      o << dict;
    }


  protected:
    Dictionary* dict;
};

class DoubleDatum : public Datum {
  public:

    DoubleDatum(double dbl=0.0)
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

    void print( std::ostream& o ) const {
      o << dbl;
    }

    void pprint( std::ostream& o ) const {
      o << dbl;
    }


  protected:
    double dbl;

};

class IntegerDatum : public Datum {
  public:

    IntegerDatum(long lng=0)
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

    void print( std::ostream& o ) const {
      o << lng;
    }

    void pprint( std::ostream& o ) const {
      o << lng;
    }


  protected:
    long lng;

};

class StringDatum : public Datum {
  public:

    StringDatum()
      : Datum(&STRING_TYPE) {}

    StringDatum(const std::string& str)
      : Datum(&STRING_TYPE), str(str) {
      }

    const std::string* operator->() const {
        return &str;
    }

    std::string* operator->() {
        return &str;
    }

    std::string& operator*() {
        return str;
    }

    Datum* clone() const {
      return new StringDatum(str);
    }

    std::string get() const {
        return str;
    }

    void print( std::ostream& o ) const {
      o << str;
    }

    void pprint( std::ostream& o ) const {
      o << str;
    }


  protected:
    std::string str;

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

    void print( std::ostream& o ) const {
      o << (Name)(*this);
    }

    void pprint( std::ostream& o ) const {
      o << (Name)(*this);
    }

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

template <> inline double getValue< double >( const Token& t ) {
    DoubleDatum* id = dynamic_cast< DoubleDatum* >( t.datum() );
    if ( id == NULL )
        throw std::exception();
    return id->get();
}
template <> inline void setValue< double >( const Token& t, double const& value ) {
    DoubleDatum* id = dynamic_cast< DoubleDatum* >( t.datum() );
    if ( id == NULL )
        throw std::exception();
    (*id) = value;
}


template <> inline long getValue< long >( const Token& t ) {
  const IntegerDatum* id = dynamic_cast< const IntegerDatum* >( t.datum() );
  if ( id == NULL )
    throw std::exception();
  return id->get();
}
template <> inline void setValue< long >( const Token& t, long const& value ) {
    IntegerDatum* id = dynamic_cast< IntegerDatum* >( t.datum() );
    if ( id == NULL )
        throw std::exception();
    (*id) = value;
}

template <> inline Token newToken< long >( long const& value ) {
    return Token( new IntegerDatum( value ) );
}


template <> inline Token newToken< double >( double const& value ) {
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

#endif
