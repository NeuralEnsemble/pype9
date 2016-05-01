#ifndef DICT_H
#define DICT_H

#include "token.h"

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

#endif
