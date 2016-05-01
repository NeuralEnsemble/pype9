#ifndef TOKEN_H
#define TOKEN_H

#include "doubledatum.h"
#include "integerdatum.h"

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



#endif
