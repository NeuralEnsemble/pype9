#include "nest.h"
#include "event.h"
#include "archiving_node.h"
#include "ring_buffer.h"
#include "connection.h"
#include "universal_data_logger.h"
#include "recordables_map.h"
#include <gsl/gsl_odeiv.h>

namespace nest {


extern "C" int AKP06_dynamics (double, const double*, double*, void*) ;


class AKP06: public Archiving_Node { 
  public: 
  ~AKP06();
  AKP06(const AKP06&);
  AKP06();
    using Node::connect_sender;
    using Node::handle;

    port check_connection(Connection&, port);
    
    void handle(SpikeEvent &);
    void handle(CurrentEvent &);
    void handle(DataLoggingRequest &); 
    
    port connect_sender(SpikeEvent &, port);
    port connect_sender(CurrentEvent &, port);
    port connect_sender(DataLoggingRequest &, port);
    
    void get_status(DictionaryDatum &) const;
    void set_status(const DictionaryDatum &);
    
    void init_node_(const Node& proto);
    void init_state_(const Node& proto);
    void init_buffers_();
    void calibrate();
    
    void update(Time const &, const long_t, const long_t);
    // make dynamics function quasi-member
    friend int AKP06_dynamics(double, const double*, double*, void*);

    // The next two classes need to be friends to access the State_ class/member
    friend class RecordablesMap<AKP06>;
    friend class UniversalDataLogger<AKP06>;
  

  struct Parameters_ { 
  double Narsg_gbar;
  double Na_Na_Ooff;
  double comp47_e0;
  double Na_Na_alpha;
  double comp18_ca_depth;
  double Narsg_Na_delta;
  double Narsg_Na_epsilon;
  double Narsg_Na_x6;
  double Narsg_Na_x5;
  double Narsg_Na_x4;
  double comp47_gbar_Kv3;
  double Narsg_Na_x3;
  double Narsg_Na_x2;
  double Narsg_Na_alfac;
  double Narsg_Na_x1;
  double Narsg_Na_beta;
  double Narsg_Na_Oon;
  double celsius;
  double Na_Na_x6;
  double comp172_cao;
  double Na_Na_x5;
  double Na_Na_x4;
  double Narsg_Na_Coff;
  double Na_Na_x3;
  double Na_Na_x2;
  double Na_Na_x1;
  double comp169_e_Leak;
  double Na_Na_beta;
  double Narsg_Na_alpha;
  double Na_Na_epsilon;
  double Na_Na_Coff;
  double Na_Na_btfac;
  double comp141_gbar_Ih;
  double Narsg_Na_Con;
  double comp47_nc;
  double comp19_gbar_Kv1;
  double Narsg_Na_btfac;
  double Narsg_Na_zeta;
  double Na_Na_Oon;
  double comp17_C_m;
  double temp_adj;
  double Narsg_Na_gbar;
  double comp18_F;
  double Na_Na_zeta;
  double Na_e;
  double Na_Na_gamma;
  double comp91_e_Kv4;
  double Na_Na_gbar;
  double Narsg_e;
  double comp47_zn;
  double comp141_e_Ih;
  double comp172_pcabar_CaP;
  double comp193_e_CaBK;
  double comp18_ca0;
  double Vrest;
  double comp47_switch_Kv3;
  double comp47_gunit;
  double Na_Na_Con;
  double comp19_e_Kv1;
  double comp169_gbar_Leak;
  double Narsg_Na_gamma;
  double comp47_e_Kv3;
  double Na_gbar;
  double comp91_gbar_Kv4;
  double Na_Na_delta;
  double Narsg_Na_Ooff;
  double Na_Na_alfac;
  double comp193_CaBK_ztau;
  double comp193_gbar_CaBK;
  double comp18_ca_beta;
  Parameters_();
  void get(DictionaryDatum&) const;
  void set(const DictionaryDatum&);
  };
  

  struct State_ { 
  

  enum StateVecElems {
  KV3_MO = 34, COMP193_CABK_ZO = 33, KV1_MO = 32, COMP18_CA = 31, KV4_HO = 30, KV4_MO = 29, CAP_M = 28, IH_M = 27, CABK_H = 26, CABK_M = 25, NARSG_NA_ZC5 = 24, NARSG_NA_ZI5 = 23, NARSG_NA_ZC4 = 22, NARSG_NA_ZI4 = 21, NARSG_NA_ZC3 = 20, NARSG_NA_ZI3 = 19, NARSG_NA_ZC2 = 18, NARSG_NA_ZI2 = 17, NARSG_NA_ZC1 = 16, NARSG_NA_ZI1 = 15, NARSG_NA_ZI6 = 14, NARSG_NA_ZO = 13, NA_NA_ZC5 = 12, NA_NA_ZI5 = 11, NA_NA_ZC4 = 10, NA_NA_ZI4 = 9, NA_NA_ZC3 = 8, NA_NA_ZI3 = 7, NA_NA_ZC2 = 6, NA_NA_ZI2 = 5, NA_NA_ZC1 = 4, NA_NA_ZI1 = 3, NA_NA_ZI6 = 2, NA_NA_ZO = 1, V = 0
  };
  double y_[35];
  int_t     r_;
  State_(const Parameters_& p);
  State_(const State_& s);
  State_& operator=(const State_& s);
  void get(DictionaryDatum&) const;
  void set(const DictionaryDatum&, const Parameters_&);
  };
  

      struct Variables_ {
      int_t    RefractoryCounts_;
      double   U_old_; // for spike-detection
    };
  

  struct Buffers_ { 
  

  Buffers_(AKP06&);
  Buffers_(const Buffers_&, AKP06&);
  UniversalDataLogger<AKP06> logger_;
  

  
  RingBuffer currents_;

  gsl_odeiv_step*    s_;    //!< stepping function
  gsl_odeiv_control* c_;    //!< adaptive stepsize control function
  gsl_odeiv_evolve*  e_;    //!< evolution function
  gsl_odeiv_system   sys_;  //!< struct describing system

  double_t step_;           //!< step size in ms
  double   IntegrationStep_;//!< current integration time step, updated by GSL

  /** 
   * Input current injected by CurrentEvent.
   * This variable is used to transport the current applied into the
   * _dynamics function computing the derivative of the state vector.
   * It must be a part of Buffers_, since it is initialized once before
   * the first simulation, but not modified before later Simulate calls.
   */
  double_t I_stim_;
  };
  template <State_::StateVecElems elem>
  double_t get_y_elem_() const { return S_.y_[elem]; }
  Parameters_ P_;
  State_      S_;
  Variables_  V_;
  Buffers_    B_;
  static RecordablesMap<AKP06> recordablesMap_;
  }; 
    inline
  port AKP06::check_connection(Connection& c, port receptor_type)
  {
    SpikeEvent e;
    e.set_sender(*this);
    c.check_event(e);
    return c.get_target()->connect_sender(e, receptor_type);
  }

  inline
  port AKP06::connect_sender(SpikeEvent&, port receptor_type)
  {
    if (receptor_type != 0)
      throw UnknownReceptorType(receptor_type, get_name());
    return 0;
  }
 
  inline
  port AKP06::connect_sender(CurrentEvent&, port receptor_type)
  {
    if (receptor_type != 0)
      throw UnknownReceptorType(receptor_type, get_name());
    return 0;
  }

  inline
  port AKP06::connect_sender(DataLoggingRequest& dlr, 
				      port receptor_type)
  {
    if (receptor_type != 0)
      throw UnknownReceptorType(receptor_type, get_name());
    return B_.logger_.connect_logging_device(dlr, recordablesMap_);
  }

  inline
    void AKP06::get_status(DictionaryDatum &d) const
  {
    P_.get(d);
    S_.get(d);
    Archiving_Node::get_status(d);

    (*d)[names::recordables] = recordablesMap_.get_list();

    def<double_t>(d, names::t_spike, get_spiketime_ms());
  }

  inline
    void AKP06::set_status(const DictionaryDatum &d)
  {
    Parameters_ ptmp = P_;  // temporary copy in case of errors
    ptmp.set(d);                       // throws if BadProperty
    State_      stmp = S_;  // temporary copy in case of errors
    stmp.set(d, ptmp);                 // throws if BadProperty

    // We now know that (ptmp, stmp) are consistent. We do not 
    // write them back to (P_, S_) before we are also sure that 
    // the properties to be set in the parent class are internally 
    // consistent.
    Archiving_Node::set_status(d);

    // if we get here, temporaries contain consistent set of properties
    P_ = ptmp;
    S_ = stmp;

    calibrate();
  }
}




