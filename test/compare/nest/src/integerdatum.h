#ifndef INTEGER_DATUM_H
#define INTEGER_DATUM_H

#include "datum.h"

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

#endif
