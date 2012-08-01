#include "nest.h"
#include "event.h"
#include "archiving_node.h"
#include "ring_buffer.h"
#include "connection.h"
#include "universal_data_logger.h"
#include "recordables_map.h"
#include <gsl/gsl_odeiv.h>

namespace nest {


extern "C" int CGC_dynamics (double, const double*, double*, void*) ;


class CGC: public Archiving_Node { 
  public: 
  ~CGC();
  CGC(const CGC&);
  CGC();
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
    friend int CGC_dynamics(double, const double*, double*, void*);

    // The next two classes need to be friends to access the State_ class/member
    friend class RecordablesMap<CGC>;
    friend class UniversalDataLogger<CGC>;
  

  struct Parameters_ { 
  double comp2270_Aalpha_f;
  double comp509_V0beta_b;
  double comp509_V0beta_a;
  double comp2657_Kbeta_m;
  double comp1764_vcbase;
  double comp1604_V0alpha_n;
  double comp2845_vchold;
  double comp2845_vcinc;
  double comp1331_Kalpha_n;
  double comp924_Bbeta_c;
  double comp1246_vcbdur;
  double comp150_Abeta_s;
  double comp150_Q10;
  double comp150_Abeta_u;
  double comp2270_V0alpha_s;
  double comp2270_V0alpha_f;
  double comp1911_V0alpha_h;
  double comp509_K_binf;
  double comp2845_vcsteps;
  double comp839_vcinc;
  double comp839_vchold;
  double fix_celsius;
  double comp1246_vcsteps;
  double comp924_Q10;
  double comp1331_Q10;
  double comp924_e;
  double comp1086_Q10;
  double comp1086_gbar;
  double comp150_V0alpha_u;
  double comp150_V0alpha_s;
  double comp1604_Abeta_n;
  double comp1911_Kbeta_h;
  double comp1519_vchold;
  double comp839_vchdur;
  double comp2572_vcbase;
  double comp2572_vcinc;
  double comp924_Abeta_c;
  double comp2657_Kalpha_m;
  double comp1519_vcsteps;
  double comp1911_Kbeta_m;
  double comp1764_vcbdur;
  double comp150_gbar;
  double comp1086_Kbeta_d;
  double comp509_K_ainf;
  double comp2270_Q10;
  double comp424_vcbdur;
  double comp1764_vcsteps;
  double comp509_Aalpha_b;
  double comp509_Aalpha_a;
  double comp1086_Aalpha_d;
  double comp1880_ggaba;
  double comp2572_vcsteps;
  double comp1911_Kalpha_m;
  double comp1911_Kalpha_h;
  double comp2657_V0beta_m;
  double comp509_e;
  double comp1086_V0beta_d;
  double comp2270_Shiftbeta_s;
  double comp1331_V0alpha_n;
  double comp2270_Aalpha_s;
  double comp1604_Aalpha_n;
  double comp2270_gbar;
  double comp150_V0beta_u;
  double comp150_V0beta_s;
  double comp65_cai0;
  double comp2657_Q10;
  double comp924_Balpha_c;
  double comp1331_Aalpha_n;
  double comp1519_vchdur;
  double comp1604_V0beta_n;
  double comp1604_Kalpha_n;
  double comp2185_vchdur;
  double comp2657_Abeta_m;
  double comp2657_B_minf;
  double comp1604_gbar;
  double comp509_Abeta_a;
  double comp509_Abeta_b;
  double comp924_Kbeta_c;
  double comp1086_Kalpha_d;
  double comp1331_V0_ninf;
  double comp1086_V0alpha_d;
  double comp150_e;
  double comp1331_e;
  double comp1519_vcbase;
  double comp150_Kalpha_s;
  double comp150_Kalpha_u;
  double comp1331_V0beta_n;
  double comp1911_e;
  double comp424_vcbase;
  double comp2185_vcinc;
  double comp424_vcsteps;
  double comp509_V0alpha_a;
  double comp509_V0alpha_b;
  double comp2270_Kbeta_s;
  double comp1764_vchold;
  double comp1331_gbar;
  double comp2270_Kbeta_f;
  double comp1764_vcinc;
  double comp424_vcinc;
  double comp1246_vchdur;
  double comp924_Aalpha_c;
  double comp924_Kalpha_c;
  double comp65_cao;
  double comp2572_vcbdur;
  double comp509_V0_binf;
  double comp1911_gbar;
  double comp65_beta;
  double comp509_Kalpha_a;
  double comp2185_vcbase;
  double comp2845_vchdur;
  double comp509_Kalpha_b;
  double comp2572_vchold;
  double comp2657_V0alpha_m;
  double comp839_vcsteps;
  double comp1519_vcbdur;
  double comp1880_egaba;
  double comp2270_Shiftalpha_s;
  double comp2270_Abeta_f;
  double comp1849_gbar;
  double comp2185_vchold;
  double comp2657_V0_minf;
  double comp2572_vchdur;
  double comp2845_vcbdur;
  double comp1911_Q10;
  double comp2657_gbar;
  double comp150_Aalpha_u;
  double comp150_Aalpha_s;
  double comp2657_e;
  double comp150_Kbeta_u;
  double comp1331_Kbeta_n;
  double comp2185_vcsteps;
  double comp509_Kbeta_b;
  double comp509_Kbeta_a;
  double comp1246_vcinc;
  double comp424_vchold;
  double comp509_V0_ainf;
  double comp2270_Kalpha_f;
  double comp509_gbar;
  double comp509_Q10;
  double comp2270_Kalpha_s;
  double comp839_vcbdur;
  double comp1911_Abeta_h;
  double comp1911_Abeta_m;
  double comp150_Kbeta_s;
  double comp1604_e;
  double comp1086_Abeta_d;
  double comp1246_vcbase;
  double comp1331_B_ninf;
  double comp2270_V0beta_s;
  double comp1086_e;
  double comp2270_e;
  double comp1911_V0beta_h;
  double comp2270_V0beta_f;
  double comp1911_V0beta_m;
  double comp424_vchdur;
  double comp1331_Abeta_n;
  double comp924_gbar;
  double comp1246_vchold;
  double comp1604_Q10;
  double comp839_vcbase;
  double comp1911_Aalpha_h;
  double comp1911_V0alpha_m;
  double comp1849_e;
  double comp1911_Aalpha_m;
  double comp65_F;
  double comp1519_vcinc;
  double comp2270_Abeta_s;
  double comp2845_vcbase;
  double comp1604_Kbeta_n;
  double comp1764_vchdur;
  double comp2657_Aalpha_m;
  double comp2185_vcbdur;
  double comp65_d;
  Parameters_();
  void get(DictionaryDatum&) const;
  void set(const DictionaryDatum&);
  };
  

  struct State_ { 
  

  enum StateVecElems {
  COMP65_CA = 14, KIR_MO = 13, NA_MO = 12, NA_HO = 11, CAHVA_HO = 10, CAHVA_MO = 9, NAR_MO = 8, NAR_HO = 7, KV_MO = 6, KM_M = 5, PNA_M = 4, KCA_M = 3, KA_M = 2, KA_H = 1, V = 0
  };
  double y_[15];
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
  

  Buffers_(CGC&);
  Buffers_(const Buffers_&, CGC&);
  UniversalDataLogger<CGC> logger_;
  

  
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
  static RecordablesMap<CGC> recordablesMap_;
  }; 
    inline
  port CGC::check_connection(Connection& c, port receptor_type)
  {
    SpikeEvent e;
    e.set_sender(*this);
    c.check_event(e);
    return c.get_target()->connect_sender(e, receptor_type);
  }

  inline
  port CGC::connect_sender(SpikeEvent&, port receptor_type)
  {
    if (receptor_type != 0)
      throw UnknownReceptorType(receptor_type, get_name());
    return 0;
  }
 
  inline
  port CGC::connect_sender(CurrentEvent&, port receptor_type)
  {
    if (receptor_type != 0)
      throw UnknownReceptorType(receptor_type, get_name());
    return 0;
  }

  inline
  port CGC::connect_sender(DataLoggingRequest& dlr, 
				      port receptor_type)
  {
    if (receptor_type != 0)
      throw UnknownReceptorType(receptor_type, get_name());
    return B_.logger_.connect_logging_device(dlr, recordablesMap_);
  }

  inline
    void CGC::get_status(DictionaryDatum &d) const
  {
    P_.get(d);
    S_.get(d);
    Archiving_Node::get_status(d);

    (*d)[names::recordables] = recordablesMap_.get_list();

    def<double_t>(d, names::t_spike, get_spiketime_ms());
  }

  inline
    void CGC::set_status(const DictionaryDatum &d)
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




