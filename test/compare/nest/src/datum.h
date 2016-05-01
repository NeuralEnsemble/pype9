#ifndef DATUM_H
#define DATUM_H

#include <vector>
#include "name.h"
#include "exceptions.h"

const Name DOUBLE_TYPE("double");
const Name LONG_TYPE("long");
const Name DICTIONARY_TYPE("dictionary");
const Name ARRAY_TYPE("array");
const Name STRING_TYPE("string");
const Name LITERAL_TYPE("literal");

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


#endif
