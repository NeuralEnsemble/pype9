#ifndef DICTUTILS_H
#define DICTUTILS_H

#include "dict.h"

template<typename FT> void def(DictionaryDatum& d, Name const n, FT const& value) {
    Token t(value); // we hope that we have a constructor for this.
    d->insert_move(n, t);
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
