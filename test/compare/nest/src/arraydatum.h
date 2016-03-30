#ifndef ARRAYDATUM_H
#define ARRAYDATUM_H

#include "tokenarray.h"

class ArrayDatum : public Datum, public TokenArray {

  public:

    ArrayDatum()
      : Datum(&ARRAY_TYPE) {
    }

    Datum* clone() const {
        return new ArrayDatum();
    }

    void print( std::ostream& o ) const {
      o << "<array datums are not implemented>";
    }

    void pprint( std::ostream& o ) const {
      o << "<array datums are not implemented>";
    }

};


#endif
