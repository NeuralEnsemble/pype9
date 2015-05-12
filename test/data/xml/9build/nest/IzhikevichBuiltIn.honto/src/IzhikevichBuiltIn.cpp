/*
 *  IzhikevichBuiltIn.cpp
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include <limits>

#include "IzhikevichBuiltIn.h"
#include "exceptions.h"
#include "network.h"
#include "dict.h"
#include "integerdatum.h"
#include "doubledatum.h"
#include "dictutils.h"
#include "numerics.h"
#include "universal_data_logger_impl.h"



/******************************************************************
 * Recordables map
 ********************************************************************/

nest::RecordablesMap<nineml::IzhikevichBuiltIn> nineml::IzhikevichBuiltIn::recordablesMap_;

namespace nest
{
  // Override the create() method with one call to RecordablesMap::insert_()
  // for each quantity to be recorded.
  template <>
  void RecordablesMap<nineml::IzhikevichBuiltIn>::create()
  {
    // use standard names whereever you can for consistency!
    insert_(names::V_m, &nineml::IzhikevichBuiltIn::get_V_m_);
    insert_(names::U_m, &nineml::IzhikevichBuiltIn::get_U_m_);
  }
}

/******************************************************************
 * Default constructors defining default parameters and state
 ********************************************************************/

nineml::IzhikevichBuiltIn::Parameters_::Parameters_()
  : a_	  (   0.02 ), // a
    b_    (   0.2  ), // b
    c_    ( -65.0  ), // c without unit
    d_    (   8.0  ), // d
    I_e_  (   0.0  ), // pA
    V_th_ (  30.0  ), // mV
    V_min_(-std::numeric_limits<double_t>::max()), // mV
    consistent_integration_(true)
{}

nineml::IzhikevichBuiltIn::State_::State_()
  : v_( -65.0 ), // membrane potential
    u_(   0.0 ), // membrane recovery variable
    I_(   0.0 )  // input current
{}

/******************************************************************
 * Parameter and state extractions and manipulation functions
 ********************************************************************/

void nineml::IzhikevichBuiltIn::Parameters_::get(DictionaryDatum & d) const
{
  def<double>(d, nest::names::I_e, I_e_);
  def<double>(d, nest::names::V_th, V_th_ );  // threshold value
  def<double>(d, nest::names::V_min, V_min_);
  def<double>(d, nest::names::a, a_);
  def<double>(d, nest::names::b, b_);
  def<double>(d, nest::names::c, c_);
  def<double>(d, nest::names::d, d_);
  def<bool>(d, nest::names::consistent_integration, consistent_integration_);
}

void nineml::IzhikevichBuiltIn::Parameters_::set(const DictionaryDatum & d)
{

  updateValue<double>(d, nest::names::V_th, V_th_);
  updateValue<double>(d, nest::names::V_min, V_min_);
  updateValue<double>(d, nest::names::I_e, I_e_);
  updateValue<double>(d, nest::names::a, a_);
  updateValue<double>(d, nest::names::b, b_);
  updateValue<double>(d, nest::names::c, c_);
  updateValue<double>(d, nest::names::d, d_);
  updateValue<bool>(d, nest::names::consistent_integration, consistent_integration_);
}

void nineml::IzhikevichBuiltIn::State_::get(DictionaryDatum & d,  const Parameters_ &) const
{
 def<double>(d, nest::names::U_m, u_); // Membrane potential recovery variable
 def<double>(d, nest::names::V_m, v_); // Membrane potential
}

void nineml::IzhikevichBuiltIn::State_::set(const DictionaryDatum & d,  const Parameters_ &)
{
  updateValue<double>(d, nest::names::U_m, u_);
  updateValue<double>(d, nest::names::V_m, v_);
}

nineml::IzhikevichBuiltIn::Buffers_::Buffers_(nineml::IzhikevichBuiltIn & n)
  : logger_(n)
{}

nineml::IzhikevichBuiltIn::Buffers_::Buffers_(const Buffers_ &, nineml::IzhikevichBuiltIn & n)
  : logger_(n)
{}

/******************************************************************
 * Default and copy constructor for node
 ********************************************************************/

nineml::IzhikevichBuiltIn::IzhikevichBuiltIn()
  : nest::Archiving_Node(),
    P_(),
    S_(),
    B_(*this)
{
  recordablesMap_.create();
}

nineml::IzhikevichBuiltIn::IzhikevichBuiltIn(const nineml::IzhikevichBuiltIn & n)
  : nest::Archiving_Node(n),
    P_(n.P_),
    S_(n.S_),
    B_(n.B_, *this)
{}

nineml::IzhikevichBuiltIn::~IzhikevichBuiltIn() {}

/******************************************************************
 * Node initialization functions
 ********************************************************************/

void nineml::IzhikevichBuiltIn::init_state_(const Node & proto)
{
  const nineml::IzhikevichBuiltIn & pr = downcast<nineml::IzhikevichBuiltIn>(proto);
  S_ = pr.S_;
}

void nineml::IzhikevichBuiltIn::init_buffers_()
{
  B_.spikes_.clear();   // includes resize
  B_.currents_.clear(); // includes resize
  B_.logger_.reset();   // includes resize
  nest::Archiving_Node::clear_history();
}

void nineml::IzhikevichBuiltIn::calibrate()
{
  B_.logger_.init();
}

/******************************************************************
 * Update and spike handling functions
 */

void nineml::IzhikevichBuiltIn::update(nest::Time const & origin,
			      const nest::long_t from, const nest::long_t to)
{
  assert(to >= 0 && (nest::delay) from < nest::Scheduler::get_min_delay());
  assert(from < to);

  const nest::double_t h = nest::Time::get_resolution().get_ms();
  double_t v_old, u_old;

  for ( nest::long_t lag = from ; lag < to ; ++lag )
  {
    // neuron is never refractory
	// use standard forward Euler numerics in this case  
    if (P_.consistent_integration_)
    {
      v_old = S_.v_;
      u_old = S_.u_;
      S_.v_ += h*( 0.04*v_old*v_old + 5.0*v_old + 140.0 - u_old + S_.I_ + P_.I_e_)
               +  B_.spikes_.get_value(lag) ;
      S_.u_ += h*P_.a_*(P_.b_*v_old - u_old);
    }
	// use numerics published in Izhikevich (2003) in this case (not recommended)  
    else
    {
      S_.v_ += h/2.0 * ( 0.04*S_.v_*S_.v_ + 5.0*S_.v_ + 140.0 - S_.u_ + S_.I_ + P_.I_e_)
	       +  B_.spikes_.get_value(lag);
      S_.v_ += h/2.0 * ( 0.04*S_.v_*S_.v_ + 5.0*S_.v_ + 140.0 - S_.u_ + S_.I_ + P_.I_e_)
	       +  B_.spikes_.get_value(lag);
      S_.u_ += h * P_.a_*(P_.b_*S_.v_ - S_.u_);
    }

    // lower bound of membrane potential
    S_.v_ = ( S_.v_<P_.V_min_ ? P_.V_min_ : S_.v_);

    // threshold crossing
    if (S_.v_ >= P_.V_th_)
    {
      S_.v_ = P_.c_;
      S_.u_ = S_.u_ + P_.d_;

      // compute spike time
      set_spiketime(nest::Time::step(origin.get_steps()+lag+1));

      nest::SpikeEvent se;
      network()->send(*this, se, lag);
    }

    // set new input current
    S_.I_ = B_.currents_.get_value(lag);

    // voltage logging
    B_.logger_.record_data(origin.get_steps()+lag);
  }
}

void nineml::IzhikevichBuiltIn::handle(nest::SpikeEvent & e)
{
  assert(e.get_delay() > 0);
  B_.spikes_.add_value(e.get_rel_delivery_steps(network()->get_slice_origin()),
		       e.get_weight() * e.get_multiplicity());
}

void nineml::IzhikevichBuiltIn::handle(nest::CurrentEvent & e)
{
  assert(e.get_delay() > 0);

  const double_t c=e.get_current();
  const double_t w=e.get_weight();
  B_.currents_.add_value(e.get_rel_delivery_steps(network()->get_slice_origin()),
			 w *c);
}

void nineml::IzhikevichBuiltIn::handle(nest::DataLoggingRequest & e)
{
  B_.logger_.handle(e);
}
