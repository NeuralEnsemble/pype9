#ifndef DOUBLE_DATUM_H
#define DOUBLE_DATUM_H

#include "datum.h"

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

#endif
