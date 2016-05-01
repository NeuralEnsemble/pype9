#include "dict.h"

const Token Dictionary::VoidToken;

Token::Token( int value )
{
  p = new IntegerDatum( value );
}

Token::Token( unsigned int value )
{
  p = new IntegerDatum( value );
}

Token::Token( long value )
{
  p = new IntegerDatum( value );
}

Token::Token( unsigned long value )
{
  p = new IntegerDatum( value );
}

Token::Token( double value )
{
  p = new DoubleDatum( value );
}


Token::operator long() const
{
  return getValue< long >( *this );
}

Token::operator size_t() const
{
  return getValue< long >( *this );
}

Token::operator double() const
{
  return getValue< double >( *this );
}


Token& Dictionary::insert_move( const Name& n, Token& t )
{
  Token& result = TokenMap::operator[]( n );
  result.move( t );
  return result;
}

Token& Dictionary::insert( const Name& n, const Token& t )
{
  return TokenMap::operator[]( n ) = t;
}

Token& Dictionary::operator[]( const Name& n )
{
  return TokenMap::operator[]( n );
}

const Token& Dictionary::lookup( const Name& n ) const {
  TokenMap::const_iterator where = find( n );
  if ( where != end() )
    return ( *where ).second;
  else
    return Dictionary::VoidToken;
}

std::ostream& operator<<( std::ostream& o, const Token& c )
{
  if ( !c )
    o << "<Null token>";
  else
    c->print( o );
  return o;
}

