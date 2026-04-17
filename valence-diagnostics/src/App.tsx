import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Shield, Activity, Lock, Database, X, User, ArrowRight, Upload, FileText, CheckCircle2, BarChart3, Globe2 } from 'lucide-react';
import { cn } from './lib/utils';

export default function App() {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [uploadState, setUploadState] = useState<'idle' | 'analyzing' | 'results'>('idle');
  const [fileName, setFileName] = useState('');

  const handleMockUpload = () => {
    setFileName('bovine_sample_A74.mp4');
    setUploadState('analyzing');
    setTimeout(() => {
      setUploadState('results');
    }, 4000);
  };

  return (
    <div className="min-h-screen bg-background text-text-primary selection:bg-accent selection:text-white font-sans">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b-2 border-black bg-white">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-black flex items-center justify-center">
              <div className="w-2 h-2 bg-white" />
            </div>
            <span className="font-bold text-lg tracking-tight uppercase">Valence Diagnostics</span>
          </div>
          <div className="flex items-center gap-8">
            {!isLoggedIn && (
              <>
                <a href="#solutions" className="hidden md:block text-xs font-bold uppercase tracking-widest hover:text-accent transition-colors">Solutions</a>
                <a href="#technology" className="hidden md:block text-xs font-bold uppercase tracking-widest hover:text-accent transition-colors">Methodology</a>
              </>
            )}
            {isLoggedIn ? (
              <button 
                onClick={() => {
                  setIsLoggedIn(false);
                  setUploadState('idle');
                }}
                className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest hover:text-accent transition-colors"
              >
                <User className="w-4 h-4" />
                Sign Out
              </button>
            ) : (
              <button 
                onClick={() => setIsAuthModalOpen(true)}
                className="px-5 py-2 text-xs font-bold uppercase tracking-widest bg-black text-white hover:bg-accent transition-colors"
              >
                Client Login
              </button>
            )}
          </div>
        </div>
      </nav>

      {isLoggedIn ? (
        <main className="pt-24 pb-24 max-w-5xl mx-auto px-6 min-h-screen flex flex-col">
          <div className="mb-12 border-b-2 border-black pb-6">
            <h2 className="text-4xl font-bold tracking-tighter text-black mb-2 uppercase">Diagnostic Engine</h2>
            <p className="text-text-secondary font-mono text-sm uppercase tracking-widest">Secure valuation and analysis portal.</p>
          </div>

          {uploadState === 'idle' && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border-2 border-dashed border-black hover:border-accent hover:bg-surface transition-colors bg-white p-16 flex flex-col items-center justify-center text-center cursor-pointer flex-1 min-h-[400px]"
              onClick={handleMockUpload}
            >
              <div className="w-16 h-16 border-2 border-black flex items-center justify-center mb-6 bg-surface">
                <Upload className="w-6 h-6 text-black" />
              </div>
              <h3 className="text-2xl font-bold mb-2 uppercase tracking-tight">Upload Microscope Feed</h3>
              <p className="text-sm text-text-secondary mb-8 max-w-md">
                Drag and drop high-resolution video files (.mp4, .avi) or click to browse. Maximum file size 500MB.
              </p>
              <button className="px-8 py-4 bg-black text-white text-xs font-bold uppercase tracking-widest hover:bg-accent transition-colors">
                Select File
              </button>
            </motion.div>
          )}

          {uploadState === 'analyzing' && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="border-2 border-black bg-white p-16 flex flex-col items-center justify-center text-center flex-1 min-h-[400px] shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]"
            >
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-16 h-16 border-4 border-surface border-t-black rounded-full mb-8"
              />
              <h3 className="text-3xl font-bold mb-2 uppercase tracking-tight">Valuating Sample...</h3>
              <p className="text-sm text-text-secondary font-bold uppercase tracking-widest mb-4">
                Running Proprietary Computer Vision Models
              </p>
              <div className="bg-black text-white px-4 py-2 font-mono text-xs mb-12">
                TARGET: {fileName}
              </div>
              <div className="w-full max-w-md h-2 bg-surface border-2 border-black overflow-hidden relative">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 4, ease: "easeInOut" }}
                  className="absolute top-0 left-0 h-full bg-accent"
                />
              </div>
            </motion.div>
          )}

          {uploadState === 'results' && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="space-y-8"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b-2 border-black pb-6 gap-4">
                <div>
                  <h3 className="text-3xl font-bold mb-1 uppercase tracking-tight">Valuation Report</h3>
                  <p className="text-sm text-text-secondary font-mono uppercase tracking-widest">FILE: {fileName}</p>
                </div>
                <button 
                  onClick={() => setUploadState('idle')}
                  className="px-6 py-3 border-2 border-black text-xs font-bold uppercase tracking-widest hover:bg-black hover:text-white transition-colors bg-white"
                >
                  New Analysis
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-0 border-2 border-black bg-black">
                <div className="bg-white p-6 border-r-2 border-b-2 lg:border-b-0 border-black">
                  <div className="text-xs font-bold text-text-secondary uppercase tracking-widest mb-4">Motility Score</div>
                  <div className="font-mono text-4xl font-bold text-black">94.2%</div>
                  <div className="text-xs font-bold text-accent mt-2 flex items-center gap-1">
                    <Activity className="w-3 h-3" /> +2.1% VS BENCHMARK
                  </div>
                </div>
                <div className="bg-white p-6 border-r-2 border-b-2 lg:border-b-0 border-black">
                  <div className="text-xs font-bold text-text-secondary uppercase tracking-widest mb-4">Morphology</div>
                  <div className="font-mono text-4xl font-bold text-black">98.7%</div>
                  <div className="text-xs font-bold text-accent mt-2 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> OPTIMAL STRUCTURE
                  </div>
                </div>
                <div className="bg-white p-6 border-r-2 border-b-2 sm:border-b-0 border-black">
                  <div className="text-xs font-bold text-text-secondary uppercase tracking-widest mb-4">Concentration</div>
                  <div className="font-mono text-4xl font-bold text-black">1.2B</div>
                  <div className="text-xs font-bold text-text-secondary mt-2 uppercase">CELLS / ML</div>
                </div>
                <div className="bg-accent p-6 relative overflow-hidden text-white">
                  <div className="absolute top-0 right-0 p-3">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                  </div>
                  <div className="text-xs font-bold uppercase tracking-widest mb-4 opacity-90">Market Valuation</div>
                  <div className="font-sans text-4xl font-bold mb-1 tracking-tighter">TIER 1</div>
                  <div className="text-xs font-mono font-bold opacity-80">EST. $150-$200 / STRAW</div>
                </div>
              </div>

              <div className="border-2 border-black bg-white p-8 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
                <h4 className="text-sm font-bold text-black uppercase tracking-widest mb-4 border-b-2 border-black pb-4">AI Diagnostic Summary</h4>
                <p className="text-text-secondary leading-relaxed mb-8 max-w-4xl font-medium">
                  The analyzed sample exhibits exceptional progressive motility and structural integrity. 
                  Head and tail morphology are within the 99th percentile of the institutional database. 
                  This sample is classified as <strong className="text-black font-bold">ELITE GRADE</strong> and is highly recommended for premium commercial distribution.
                </p>
                <button className="flex items-center justify-center gap-2 px-8 py-4 bg-black text-white text-xs font-bold uppercase tracking-widest hover:bg-accent transition-colors w-full sm:w-auto">
                  <FileText className="w-4 h-4" />
                  Export Official Report (PDF)
                </button>
              </div>
            </motion.div>
          )}
        </main>
      ) : (
        <main className="pt-16">
          {/* Hero Section */}
          <section className="border-b-2 border-black bg-surface relative">
            <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, black 1px, transparent 0)', backgroundSize: '24px 24px' }} />
            <div className="max-w-7xl mx-auto px-6 pt-24 pb-32 relative z-10">
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="max-w-4xl"
              >
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-black text-white text-[10px] font-bold uppercase tracking-widest mb-8">
                  <Shield className="w-3 h-3" />
                  Institutional-Grade Diagnostics
                </div>
                <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-8 leading-[1.05]">
                  ENTERPRISE AI FOR <br />
                  <span className="text-accent">BOVINE GENETICS.</span>
                </h1>
                <p className="text-xl text-text-secondary font-medium max-w-2xl mb-12 leading-relaxed">
                  Valence Diagnostics provides proprietary computer vision infrastructure for the agricultural sector. Real-time, institutional-grade valuation of genetic material for commercial breeders and veterinary labs.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <button 
                    onClick={() => setIsAuthModalOpen(true)}
                    className="group flex items-center justify-center gap-2 px-8 py-4 bg-black text-white hover:bg-accent transition-colors text-xs font-bold uppercase tracking-widest"
                  >
                    Request Enterprise Demo
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>
                  <button className="px-8 py-4 bg-white border-2 border-black hover:bg-surface transition-colors text-xs font-bold uppercase tracking-widest text-black">
                    Read the Whitepaper
                  </button>
                </div>
              </motion.div>
            </div>
          </section>

          {/* Trust Banner */}
          <section className="border-b-2 border-black bg-white py-6">
            <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-8">
              <p className="text-xs font-bold text-text-muted uppercase tracking-widest">Trusted by industry leaders</p>
              <div className="flex flex-wrap items-center gap-8 md:gap-16 opacity-50 grayscale">
                <div className="font-bold text-xl tracking-tight">CONTINENTAL AGTECH</div>
                <div className="font-bold text-xl tracking-tighter">VANGUARD LABS</div>
                <div className="font-bold text-xl tracking-wide">MERIDIAN RESEARCH</div>
                <div className="font-bold text-xl tracking-widest uppercase">APEX VISION</div>
              </div>
            </div>
          </section>

          {/* Solutions Section */}
          <section id="solutions" className="py-24 bg-white border-b-2 border-black">
            <div className="max-w-7xl mx-auto px-6">
              <div className="mb-16 max-w-2xl">
                <h2 className="text-4xl font-bold tracking-tighter mb-6 uppercase">Unparalleled Market Dominance</h2>
                <p className="text-lg text-text-secondary leading-relaxed">
                  Our infrastructure is designed for high-scale operations, delivering absolute data security and seamless scalability. We replace manual microscopy with deterministic AI validation.
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-2 border-black bg-black">
                {[
                  { icon: Activity, title: "Real-Time Analysis", desc: "Sub-millisecond processing of microscope video feeds. Instantaneous motility and morphology scoring." },
                  { icon: Database, title: "Scalable Infrastructure", desc: "Cloud-native architecture built to handle millions of diagnostic records with zero latency." },
                  { icon: Lock, title: "Absolute Security", desc: "SOC2 compliant end-to-end encryption for sensitive genetic data and proprietary valuations." },
                ].map((feature, i) => (
                  <div key={i} className="flex flex-col bg-white p-8 border-r-2 border-b-2 md:border-b-0 border-black last:border-r-0">
                    <div className="w-12 h-12 border-2 border-black flex items-center justify-center mb-6">
                      <feature.icon className="w-6 h-6 text-black" />
                    </div>
                    <h3 className="text-xl font-bold mb-3 uppercase tracking-tight">{feature.title}</h3>
                    <p className="text-text-secondary leading-relaxed text-sm">{feature.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Technology Showcase / Methodology */}
          <section id="technology" className="py-24 bg-surface border-b-2 border-black">
            <div className="max-w-7xl mx-auto px-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-black text-white text-[10px] font-bold uppercase tracking-widest mb-6">
                    <BarChart3 className="w-3 h-3" />
                    Proprietary Models
                  </div>
                  <h2 className="text-4xl font-bold tracking-tighter mb-6 uppercase">Deterministic Valuation at Scale</h2>
                  <p className="text-lg text-text-secondary leading-relaxed mb-8">
                    Valence Diagnostics leverages custom-trained convolutional neural networks to analyze cellular structure and movement patterns. By standardizing the valuation process, we eliminate human error and provide a transparent, auditable trail for every sample.
                  </p>
                  <ul className="space-y-4">
                    {[
                      "99.9% Confidence Interval on Morphology",
                      "Automated Tier Classification",
                      "Instant PDF Report Generation",
                      "API Integration for LIMS"
                    ].map((item, i) => (
                      <li key={i} className="flex items-center gap-3 text-black font-bold text-sm uppercase tracking-tight">
                        <CheckCircle2 className="w-5 h-5 text-accent" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Methodology Flowchart */}
                <div className="border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
                  <div className="bg-black text-white px-6 py-3 font-mono text-xs font-bold uppercase tracking-widest flex justify-between items-center">
                    <span>Methodology</span>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      <span>System Active</span>
                    </div>
                  </div>
                  <div className="flex flex-col">
                    {/* Step 1 */}
                    <div className="p-8 border-b-2 border-black flex gap-6 items-start hover:bg-surface transition-colors">
                      <div className="font-mono text-3xl font-bold text-accent">01</div>
                      <div>
                        <h4 className="font-bold uppercase tracking-widest text-sm mb-2">How to Upload</h4>
                        <p className="text-sm text-text-secondary leading-relaxed">Secure ingestion of high-resolution microscope video feeds via encrypted portal. Supports standard formats (.mp4, .avi).</p>
                      </div>
                    </div>
                    {/* Step 2 */}
                    <div className="p-8 border-b-2 border-black flex gap-6 items-start hover:bg-surface transition-colors">
                      <div className="font-mono text-3xl font-bold text-accent">02</div>
                      <div>
                        <h4 className="font-bold uppercase tracking-widest text-sm mb-2">Sign Up for Result</h4>
                        <p className="text-sm text-text-secondary leading-relaxed">Client authentication initiates the deterministic AI processing pipeline. Zero-latency cloud execution.</p>
                      </div>
                    </div>
                    {/* Step 3 */}
                    <div className="p-8 flex gap-6 items-start hover:bg-surface transition-colors">
                      <div className="font-mono text-3xl font-bold text-accent">03</div>
                      <div>
                        <h4 className="font-bold uppercase tracking-widest text-sm mb-2">Quantitative Analytics</h4>
                        <p className="text-sm text-text-secondary leading-relaxed">Delivery of institutional-grade valuation, motility, and morphology metrics. Exportable to LIMS.</p>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="bg-white py-12 border-t-2 border-black">
            <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 bg-black flex items-center justify-center">
                  <div className="w-2 h-2 bg-white" />
                </div>
                <span className="font-bold text-lg tracking-tight uppercase">Valence Diagnostics</span>
              </div>
              <div className="flex gap-6 text-xs font-bold uppercase tracking-widest text-text-secondary">
                <a href="#" className="hover:text-black transition-colors">Privacy Policy</a>
                <a href="#" className="hover:text-black transition-colors">Terms of Service</a>
                <a href="#" className="hover:text-black transition-colors">Contact</a>
              </div>
              <div className="text-xs font-bold text-text-muted uppercase tracking-widest">
                &copy; {new Date().getFullYear()} Valence Diagnostics. All rights reserved.
              </div>
            </div>
          </footer>
        </main>
      )}

      {/* Auth Modal */}
      <AnimatePresence>
        {isAuthModalOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/40 backdrop-blur-sm"
          >
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="bg-white border-2 border-black w-full max-w-md p-8 relative shadow-[12px_12px_0px_0px_rgba(0,0,0,1)]"
            >
              <button 
                onClick={() => setIsAuthModalOpen(false)}
                className="absolute top-6 right-6 text-text-secondary hover:text-black transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="mb-8">
                <div className="w-12 h-12 bg-black flex items-center justify-center mb-6">
                  <Globe2 className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-black mb-2 tracking-tighter uppercase">Client Portal</h2>
                <p className="text-sm text-text-secondary font-bold uppercase tracking-widest">Secure access for institutional partners.</p>
              </div>

              <form className="space-y-6" onSubmit={(e) => {
                e.preventDefault();
                setIsLoggedIn(true);
                setIsAuthModalOpen(false);
              }}>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-black mb-2">Institutional Email</label>
                  <input 
                    type="email" 
                    required
                    className="w-full bg-surface border-2 border-black px-4 py-3 text-sm font-bold focus:outline-none focus:bg-white transition-all"
                    placeholder="dr.smith@institute.edu"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-black mb-2">Access Token</label>
                  <input 
                    type="password" 
                    required
                    className="w-full bg-surface border-2 border-black px-4 py-3 text-sm font-bold focus:outline-none focus:bg-white transition-all"
                    placeholder="••••••••••••"
                  />
                </div>
                <button 
                  type="submit"
                  className="w-full bg-black text-white hover:bg-accent transition-colors py-4 text-xs font-bold uppercase tracking-widest mt-2"
                >
                  Authenticate
                </button>
              </form>
              
              <div className="mt-8 pt-6 border-t-2 border-black text-center">
                <p className="text-xs font-bold text-text-secondary uppercase tracking-widest">
                  Requesting access? <a href="#" className="text-black hover:text-accent underline">Apply for Beta</a>
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
