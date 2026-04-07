import { useState, useEffect, useRef, type CSSProperties } from 'react';
import { ShoppingCart, Sun, Moon, ChevronLeft, ChevronRight } from 'lucide-react';
import './index.css';

/** API base: Vite dev server proxies /api → FastAPI; set VITE_API_URL for production build */
const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? (import.meta.env.DEV ? '/api' : 'http://127.0.0.1:8000');

// Type definitions
interface Product {
  id: number;
  name: string;
  brand: string;
  category: string;
  price_pkr: number;
  price_usd?: number;
  rating: number;
  specs: string | string[];
  reviews: string | string[];
  search_url_daraz: string;
  search_url_amazon: string;
  image_emoji: string;
  image_url: string;
  image_placeholder_alt?: string;
  key_features?: string[];
  deep_description?: string;
  ddg_abstract?: string;
  description?: string;
  use_cases: string;
  release_year: number;
  sentiment_analysis?: {
    sentiment_label: string;
    review_summary: string;
    confidence_score: number;
    top_praise: string;
    top_complaint: string;
  };
  scores?: {
    price_fit: number;
    feature_match: number;
    review_score: number;
    total_score: number;
    value_rating: string;
  };
  personalization_note?: string;
  justification?: string;
}

function normalizeAdvise(raw: Record<string, unknown>) {
  const products = Array.isArray(raw.products) ? raw.products : [];
  return {
    ...raw,
    products,
    ethics: (raw.ethics as object) || { has_flag: false, flags: [] },
    query_intelligence: (raw.query_intelligence as object) || {},
    alternatives: (raw.alternatives as object) || {},
    final_report: (raw.final_report as object) || {},
    price_intelligence: (raw.price_intelligence as object) || {},
    user_profile: (raw.user_profile as object) || {},
    extracted_preferences: raw.extracted_preferences || {},
    retrieval_strategy: typeof raw.retrieval_strategy === 'string' ? raw.retrieval_strategy : '',
  };
}

function safeSpecs(specs: string | string[] | undefined): string[] {
  if (!specs) return [];
  if (Array.isArray(specs)) return specs.filter(Boolean).map(String);
  try {
    const j = JSON.parse(specs);
    return Array.isArray(j) ? j.map(String) : [];
  } catch {
    return [];
  }
}

function ProductImage({
  product,
  className,
  style,
}: {
  product: Product;
  className?: string;
  style?: CSSProperties;
}) {
  const [src, setSrc] = useState(product.image_url);
  useEffect(() => {
    setSrc(product.image_url);
  }, [product.image_url, product.id]);
  return (
    <img
      src={src}
      alt={product.name}
      className={className}
      style={style}
      loading="lazy"
      onError={() => {
        if (product.image_placeholder_alt && src !== product.image_placeholder_alt) {
          setSrc(product.image_placeholder_alt);
        }
      }}
    />
  );
}

const CATEGORIES = [
  { name: 'Smartphones', emoji: '📱', count: 8 },
  { name: 'Laptops', emoji: '💻', count: 7 },
  { name: 'Heels', emoji: '👠', count: 5 },
  { name: 'Shoes', emoji: '👟', count: 6 },
  { name: 'Earbuds', emoji: '🎧', count: 5 },
  { name: 'Headphones', emoji: '🎵', count: 3 },
  { name: 'Tablets', emoji: '📱', count: 4 },
  { name: 'Smartwatches', emoji: '⌚', count: 4 },
  { name: 'Cameras', emoji: '📷', count: 3 },
  { name: 'Monitors', emoji: '🖥️', count: 3 },
  { name: 'Keyboards', emoji: '⌨️', count: 3 },
  { name: 'Mice', emoji: '🖱️', count: 3 },
  { name: 'Powerbanks', emoji: '🔋', count: 2 },
  { name: 'Speakers', emoji: '🔊', count: 2 },
  { name: 'Gaming Headsets', emoji: '🎮', count: 2 },
  { name: 'Cooling Pads', emoji: '❄️', count: 2 },
  { name: 'Bags', emoji: '👜', count: 5 },
  { name: 'Clothing', emoji: '👔', count: 5 },
  { name: 'Makeup', emoji: '💄', count: 3 },
  { name: 'Skincare', emoji: '✨', count: 3 },
  { name: 'Fragrance', emoji: '🌸', count: 3 },
];

const AGENTS = [
  { id: 1, name: "Preference Extraction", emoji: "🎯", tag: "NLP & Parsing", desc: "Reads your query and extracts budget, category, priorities and use case with fallback keyword matching" },
  { id: 2, name: "Product Retrieval", emoji: "🔍", tag: "Live APIs", desc: "DummyJSON search & category endpoints, local budget filter with relaxation, DuckDuckGo context, and LLM key features" },
  { id: 3, name: "Review Analysis", emoji: "⭐", tag: "Sentiment Analysis", desc: "Rule-based review signals from ratings and stored review snippets (no per-product LLM)" },
  { id: 4, name: "Comparison Scoring", emoji: "⚖️", tag: "Scoring Engine", desc: "Deterministic 100-point score: budget fit, keyword/spec match, and rating — pure Python" },
  { id: 5, name: "Ethics Detection", emoji: "🛡️", tag: "Ethics & Safety", desc: "Flags budget violations, brand monopoly, low quality and limited options" },
  { id: 6, name: "Price Intelligence", emoji: "📈", tag: "Price Forecasting", desc: "Analyzes market trends by category and season — buy now or wait?" },
  { id: 7, name: "Personalization", emoji: "👤", tag: "Personalization", desc: "Reranks products for your specific use case: student, gamer, traveler, office" },
  { id: 8, name: "Alternatives", emoji: "💡", tag: "Smart Alternatives", desc: "Suggests budget stretches, category alternatives and refurbished options" },
  { id: 9, name: "Query Intelligence", emoji: "🧠", tag: "Query Understanding", desc: "Heuristic ambiguity, confidence, and related searches from category maps (no LLM)" },
  { id: 10, name: "Final Recommendation", emoji: "🏆", tag: "Final Reasoning", desc: "Python justifications for top picks plus one short LLM executive summary when API key is set" },
];

const TEST_QUERIES = {
  "Smartphones": ["I need a good phone under 100k", "Best camera phone for a traveler", "Give me a gaming phone under 150000", "iPhone alternative under 60k"],
  "Laptops": ["Heavy gaming laptop no budget", "Lightest laptop for office work", "Laptop under 120000", "Good cooling laptop for render"],
  "Footwear": ["Comfortable heels for office", "Best running shoes Nike", "Stylo pumps"],
  "Audio": ["Noise cancelling earbuds for traveler", "Best ANC headphones under 20k", "Loud bluetooth speaker for parties"],
  "Gaming": ["Mechanical keyboard red switches", "Lightweight gaming mouse", "Surround sound headset", "144hz monitor for student"],
  "Edge Cases": ["I have no budget show me best things", "gjhgjg", "10 million budget"]
};

const ShoppingBackground = () => {
  const icons = ['🛒', '👜', '👞', '📱', '⌚', '👕', '💄', '💻', '🎮', '📦', '👔', '👠', '👒', '🎧', '📷'];
  const [elements, setElements] = useState<{ id: number; icon: string; left: string; delay: string; duration: string; size: string }[]>([]);
  const scrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      scrollY.current = window.scrollY;
      const bg = document.querySelector('.shopping-bg-container') as HTMLElement;
      if (bg) {
        bg.style.transform = `translateY(${scrollY.current * 0.15}px)`;
      }
    };
    window.addEventListener('scroll', handleScroll);

    const newElements = Array.from({ length: 15 }).map((_, i) => ({
      id: i,
      icon: icons[Math.floor(Math.random() * icons.length)],
      left: `${Math.random() * 100}%`,
      delay: `${-Math.random() * 30}s`, // Start mid-animation for smoothness
      duration: `${20 + Math.random() * 20}s`,
      size: `${1.8 + Math.random() * 2}rem`
    }));
    setElements(newElements);

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="shopping-bg-container bg-parallax">
      {elements.map(el => (
        <div
          key={el.id}
          className="shopping-icon-silhouette"
          style={{
            left: el.left,
            animationDelay: el.delay,
            animationDuration: el.duration,
            fontSize: el.size
          }}
        >
          {el.icon}
        </div>
      ))}
    </div>
  );
};

const extractBudgetConstraint = (q: string): number | null => {
  const text = q.toLowerCase();
  // Match patterns like "under 100k", "below 50,000", "max 1 lac", "budget 80k"
  const match = text.match(/(?:under|below|max|budget(?: is)?|within|less than)\s*(?:₨|rs\.?|pkr)?\s*([\d,]+(?:\s*[km]|lac|lakh)?)/i);
  if (match) {
    let val = match[1].replace(/,/g, '').trim();
    let num = parseFloat(val);
    if (val.endsWith('k')) num *= 1000;
    if (val.includes('lac') || val.includes('lakh')) num *= 100000;
    if (val.endsWith('m')) num *= 1000000;
    return isNaN(num) ? null : num;
  }
  return null;
};

export default function App() {
  const [query, setQuery] = useState("");
  const [lastQuery, setLastQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [activeAgent, setActiveAgent] = useState(-1);
  const [backendStatus, setBackendStatus] = useState("checking");
  const [toast, setToast] = useState("");

  const [compareMode, setCompareMode] = useState(false);
  const [compareItems, setCompareItems] = useState<number[]>([]);
  const [showModal, setShowModal] = useState(false);

  // Dashboard Metrics
  const [sessionSearches, setSessionSearches] = useState(0);
  const [bestScoreSeen, setBestScoreSeen] = useState(0);

  const [theme, setTheme] = useState('light');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollCategories = (dir: 'left' | 'right') => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir === 'left' ? -300 : 300, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));

  }, []);

  const runSearch = async (queryOverride?: string) => {
    const q = (queryOverride !== undefined ? queryOverride : query).trim();
    if (!q || isSearching) return;

    setQuery(q);
    setLastQuery(q);
    setIsSearching(true);
    setSearchError(null);
    setResults(null);
    document.title = "🔍 Searching... | AuraCart";
    setSessionSearches((s) => s + 1);
    setActiveAgent(1);

    const ac = new AbortController();
    const clientTimeout = window.setTimeout(() => ac.abort(), 90000);
    const anim = window.setInterval(() => {
      setActiveAgent((a) => (a >= 10 || a < 1 ? 1 : a + 1));
    }, 280);

    try {
      const res = await fetch(`${API_BASE}/advise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
        signal: ac.signal,
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const detail = (data as { detail?: string | string[] })?.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((x) => (typeof x === "object" && x && "msg" in x ? (x as { msg: string }).msg : String(x))).join(" ")
              : "Request failed";
        if (res.status === 408) {
          setSearchError("Request timed out. Try a more specific or shorter query.");
        } else {
          setSearchError(msg);
        }
        setResults(normalizeAdvise({ products: [], ethics: { has_flag: false, flags: [] } }));
        return;
      }

      const normalized = normalizeAdvise(data as Record<string, unknown>);

      // Strict Client-Side Filtering
      const keywords = q.toLowerCase().split(/\s+/).filter((k) => k.length > 2);
      const budgetLimit = extractBudgetConstraint(q);

      if (keywords.length > 0 || budgetLimit !== null) {
        normalized.products = normalized.products.filter((p: Product) => {
          const name = p.name.toLowerCase();
          const cat = p.category.toLowerCase();
          const specs = safeSpecs(p.specs).join(" ").toLowerCase();
          const desc = (p.description || "").toLowerCase();

          // 1. Keyword check (if keywords exist)
          const keywordMatch = keywords.length === 0 || keywords.some((k) => 
            name.includes(k) || cat.includes(k) || specs.includes(k) || desc.includes(k)
          );

          // 2. Strict Budget check (if budget mentioned)
          const budgetMatch = budgetLimit === null || p.price_pkr <= budgetLimit;

          return keywordMatch && budgetMatch;
        });

        if (normalized.products.length === 0) {
          if (budgetLimit !== null) {
            setSearchError(`No products found strictly under ₨${budgetLimit.toLocaleString()}. Try increasing your budget.`);
          } else {
            setSearchError("No products matched your specific search criteria.");
          }
        }

        // Boost Ranking: Prioritize products where the query keywords appear in the name
        normalized.products.sort((a: Product, b: Product) => {
          const aScore = keywords.reduce((acc, k) => acc + (a.name.toLowerCase().includes(k) ? 10 : 0) + (a.category.toLowerCase().includes(k) ? 5 : 0), 0);
          const bScore = keywords.reduce((acc, k) => acc + (b.name.toLowerCase().includes(k) ? 10 : 0) + (b.category.toLowerCase().includes(k) ? 5 : 0), 0);
          
          if (bScore !== aScore) return bScore - aScore;
          // Tie-break with original agent-provided total score
          return (b.scores?.total_score || 0) - (a.scores?.total_score || 0);
        });
      }

      setResults(normalized);
      setSelectedProduct(null);
      setSearchError(null);

      const topScore = normalized.products?.[0]?.scores?.total_score || 0;
      if (topScore > bestScoreSeen) setBestScoreSeen(topScore);
    } catch (err: unknown) {
      console.error(err);
      const e = err as { name?: string };
      if (e?.name === "AbortError") {
        setSearchError("Search timed out after 90s. Try again with a simpler query.");
      } else {
        setSearchError("Cannot connect to backend. Start the API: cd backend && python -m uvicorn main:app --port 8000");
      }
      setResults(normalizeAdvise({ products: [], ethics: { has_flag: false, flags: [] } }));
    } finally {
      window.clearTimeout(clientTimeout);
      window.clearInterval(anim);
      setIsSearching(false);
      setActiveAgent(-1);
      document.title = "AuraCart";
    }
  };

  const copyToClipboard = () => {
    const text = `Top Recommendations:\\n1. ${results?.products[0]?.name} - ₨${results?.products[0]?.price_pkr}\\n2. ${results?.products[1]?.name}`;
    navigator.clipboard.writeText(text);
    setToast("Copied!");
    setTimeout(() => setToast(""), 2000);
  };

  return (
    <div className={`app-root ${theme}`}>
      <ShoppingBackground />
      {/* Removed conflicting bg-layer */}

      {toast && <div className="toast">{toast}</div>}

      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-left">
          <span className="logo logo-with-cart" title="AuraCart — Intelligent Shopping Advisor">
            <ShoppingCart className="logo-cart-icon" size={28} strokeWidth={2.2} aria-hidden />
            <span className="logo-text">AuraCart</span>
          </span>
        </div>
        <div className="nav-center">
          <div className="mega-menu">
            <span className="nav-link">Categories ▾</span>
            <div className="mega-panel">
              {CATEGORIES.slice(0, 8).map((c, i) => (
                <div key={i} className="mega-item" onClick={() => runSearch(c.name)}>
                  <span>{c.emoji}</span> <span>{c.name}</span>
                </div>
              ))}
            </div>
          </div>
          <a href="#agents" className="nav-link">Agents</a>
          <a href="#how" className="nav-link">How It Works</a>
        </div>
        <div className="nav-right">
          <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center' }}>
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <span className="badge blue">10 Agents</span>
          <span className="badge green">Groq Powered</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
            <div className={`online-dot ${backendStatus !== 'online' ? 'offline' : ''}`}></div>
            {backendStatus === 'online' ? 'Online' : 'Offline'}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <h1 className="hero-title">Find Anything.<br /><span className="gradient-text">Powered by AI.</span></h1>
        <p className="hero-subtitle">10 specialized AI agents analyze thousands of products to find your perfect match — with ethics checking, price intelligence, and personalized recommendations.</p>

        <div className="search-container">
          <input type="text" className="search-input" placeholder="Search laptops, heels, phones, cameras..." value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && runSearch()} />
          <button className="search-btn" onClick={() => runSearch()}>🔍 Search</button>
        </div>

        <div className="trending-pills">
          <span className="trending-pill" onClick={() => runSearch("Gaming Laptop")}>🔥 Gaming Laptop</span>
          <span className="trending-pill" onClick={() => runSearch("Nike Sneakers")}>👟 Nike Sneakers</span>
          <span className="trending-pill" onClick={() => runSearch("Heels under 5000")}>👠 Heels under 5000</span>
          <span className="trending-pill" onClick={() => runSearch("Noise Cancelling Earbuds")}>🎧 Noise Cancelling</span>
        </div>

        <div className="stats-strip">
          <div className="stat-item"><span className="stat-val">Live</span><span className="stat-label">Catalog</span></div>
          <div className="stat-item"><span className="stat-val">10</span><span className="stat-label">AI Agents</span></div>
          <div className="stat-item"><span className="stat-val">50</span><span className="stat-label">Test Cases</span></div>
          <div className="stat-item"><span className="stat-val">18</span><span className="stat-label">Categories</span></div>
        </div>
      </section>

      {/* Category Browse */}
      <section className="category-browse">
        <button onClick={() => scrollCategories('left')} style={{ color: 'var(--text-primary)', fontSize: '24px' }}><ChevronLeft size={32} /></button>
        <div className="cat-scroll-container" ref={scrollRef}>
          {CATEGORIES.map((c, i) => (
            <div key={i} className="cat-card" onClick={() => runSearch(c.name)}>
              <div className="cat-emoji">{c.emoji}</div>
              <div className="cat-name">{c.name}</div>
              <div className="cat-count">{c.count} products</div>
            </div>
          ))}
        </div>
        <button onClick={() => scrollCategories('right')} style={{ color: 'var(--text-primary)', fontSize: '24px' }}><ChevronRight size={32} /></button>
      </section>

      {/* Meet Your AI Team */}
      <section id="agents" className="agent-team-section">
        <h2 className="section-header syne">Meet Your AI Team</h2>
        <p className="section-sub">10 specialized agents working in perfect harmony to find your ideal product.</p>

        <div className="agent-grid">
          {AGENTS.map((a, i) => (
            <div key={a.id} className={`agent-card ${activeAgent === a.id ? 'active' : ''}`} style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="agent-num-badge">Agent {a.id.toString().padStart(2, '0')}</div>
              <div className="agent-icon">{a.emoji}</div>
              <div className="agent-name syne">{a.name}</div>
              <div className="agent-desc">{a.desc}</div>
              <div className="agent-tag">{a.tag}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Live Pipeline execution view */}
      {isSearching && (
        <div className="pipeline-panel">
          <h3 className="mb-20">Agent Pipeline — Live Status {activeAgent}/10</h3>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${(activeAgent / 10) * 100}%` }}></div>
          </div>
          <div className="pipeline-grid">
            {AGENTS.map(a => {
              let state = "idle";
              if (activeAgent === a.id) state = "active";
              if (a.id < activeAgent) state = "done";

              return (
                <div key={a.id} className={`pipe-agent ${state}`}>
                  <div className="pipe-icon">{state === 'done' ? '✅' : a.emoji}</div>
                  <div className="pipe-details">
                    <span className="pipe-name">{a.name}</span>
                    <span className="pipe-status">
                      {state === 'idle' && 'Waiting...'}
                      {state === 'active' && <span className="thinking-dots">Processing</span>}
                      {state === 'done' && 'Done'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Results Layout */}
      {(results || isSearching) && (
        <div className="results-layout" id="results">

          <div className="main-content">
            {isSearching ? (
              <div>
                <h2 className="syne mb-20" style={{ fontSize: '32px' }}>Your Refined Results</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>Running AI pipeline…</p>
                <div className="skeleton-card" style={{ height: '100px' }} />
                <div className="skeleton-card" />
                <div className="skeleton-card" />
              </div>
            ) : results && (
              <div>
                {selectedProduct && (
                  <section className="product-detail-page" aria-label="Product detail">
                    <button type="button" className="product-detail-back" onClick={() => setSelectedProduct(null)}>
                      <ChevronLeft size={18} aria-hidden />
                      Back to results
                    </button>
                    <div className="product-detail-grid">
                      <div>
                        <ProductImage product={selectedProduct} className="product-detail-hero-img" />
                      </div>
                      <div>
                        <div className="prod-title" style={{ fontSize: '1.5rem', marginBottom: 8 }}>
                          {selectedProduct.name}{' '}
                          <span className="prod-brand">by {selectedProduct.brand}</span>
                        </div>
                        <div className="badge blue" style={{ display: 'inline-block', marginBottom: 12 }}>
                          {selectedProduct.category}
                        </div>
                        <div className="prod-price" style={{ fontSize: '1.75rem', marginBottom: 8 }}>
                          ₨{selectedProduct.price_pkr.toLocaleString()}
                          {selectedProduct.price_usd != null ? (
                            <span style={{ fontSize: '14px', color: 'var(--text-secondary)', marginLeft: 10 }}>
                              (~${Number(selectedProduct.price_usd).toFixed(2)} USD)
                            </span>
                          ) : null}
                        </div>
                        <div style={{ color: 'var(--gold)', marginBottom: 16 }}>
                          {'★'.repeat(Math.min(5, Math.round(selectedProduct.rating)))} ({selectedProduct.rating})
                        </div>
                        <h3 className="syne" style={{ fontSize: '1.1rem', marginBottom: 8 }}>
                          Key features
                        </h3>
                        <ul className="feature-bullets">
                          {(selectedProduct.key_features || safeSpecs(selectedProduct.specs)).map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ul>
                        <h3 className="syne" style={{ fontSize: '1.1rem', margin: '20px 0 8px' }}>
                          Overview
                        </h3>
                        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
                          {selectedProduct.deep_description || selectedProduct.description || 'No extended description.'}
                        </p>
                        <div className="action-buttons" style={{ marginTop: 24 }}>
                          <a
                            href={selectedProduct.search_url_daraz}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-primary"
                            style={{ textDecoration: 'none' }}
                          >
                            View on Daraz
                          </a>
                          <a
                            href={selectedProduct.search_url_amazon}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-outline"
                            style={{ textDecoration: 'none' }}
                          >
                            Amazon search
                          </a>
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                <div className="flex justify-between align-center mb-20">
                  <h2 className="syne" style={{ fontSize: '32px' }}>Your Refined Results</h2>
                  <div>
                    <button className="btn-outline mr-10" style={{ marginRight: '10px' }} onClick={() => setCompareMode(!compareMode)}>
                      {compareMode ? 'Cancel Compare' : 'Compare Mode'}
                    </button>
                    {compareMode && compareItems.length > 0 && <button className="btn-primary" onClick={() => setShowModal(true)}>Compare Selected ({compareItems.length})</button>}
                    <button className="btn-primary" style={{ marginLeft: '10px' }} onClick={copyToClipboard}>📋 Share Results</button>
                  </div>
                </div>

                {searchError && (
                  <div className="info-panel error" style={{ marginBottom: '20px' }}>
                    <strong>Search issue:</strong> {searchError}
                  </div>
                )}

                {!searchError && !isSearching && (!results.products || results.products.length === 0) && (
                  <div className="info-panel warning" style={{ marginBottom: '20px' }}>
                    No products returned. Try a clearer category (e.g. &quot;heels for office&quot;, &quot;gaming laptop&quot;) or check that the API finished without errors.
                  </div>
                )}

                {/* Info panels */}
                {results.query_intelligence?.is_ambiguous && (
                  <div className="info-panel warning">
                    <strong>⚠️ Query Ambigous:</strong> {results.query_intelligence.interpreted_as} <br />
                    Missing Info: {(results.query_intelligence.missing_info || []).join(', ')}
                  </div>
                )}

                {results.ethics?.has_flag && (
                  <div className="info-panel error">
                    <strong>🛡️ Ethics & Bias Flag ({results.ethics.severity}):</strong>
                    <ul>{results.ethics.flags.map((f: any, i: any) => <li key={i}>{f}</li>)}</ul>
                    <p style={{ marginTop: '5px', fontSize: '12px' }}>{results.ethics.note}</p>
                  </div>
                )}

                {results.price_intelligence && (() => {
                  const pi = results.price_intelligence as Record<string, unknown>;
                  const trend = (pi.market_trend as string) || 'Stable';
                  const forecast = (pi.price_forecast as string) || 'Prices are stable.';
                  const seasonal = (pi.seasonal_note as string) || '';
                  const savings = (pi.savings_opportunity as string) || '';
                  return (
                    <div className="info-panel success">
                      <strong>📈 Price Trend ({trend}):</strong> {forecast} <br />
                      {savings ? <span style={{ fontSize: '14px', display: 'block', marginTop: 6 }}>{savings}</span> : null}
                      <span style={{ fontSize: '14px' }}>{seasonal}</span>
                    </div>
                  );
                })()}

                <div className="related-chips mb-20">
                  <span style={{ color: 'var(--text-secondary)', alignSelf: 'center' }}>Related:</span>
                  {results.query_intelligence?.related_searches?.map((r: string, i: number) => (
                    <div key={i} className="chip" onClick={() => runSearch(r)}>{r}</div>
                  ))}
                </div>

                {/* Top Recommendations */}
                {!selectedProduct && (
                  <div className="top-recommendations">
                    {(results.products || []).slice(0, 3).map((p: Product, idx: number) => (
                      <div
                        key={p.id}
                        className={`product-card-large rank-${idx + 1}`}
                        onClick={() => setSelectedProduct(p)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedProduct(p);
                          }
                        }}
                        role="button"
                        tabIndex={0}
                        aria-label={`Open details for ${p.name}`}
                      >
                        <div className={`rank-badge ${idx === 0 ? 'gold' : idx === 1 ? 'blue' : 'green'}`}>#{idx + 1} Match</div>

                        {compareMode && (
                          <input type="checkbox" style={{ position: 'absolute', top: '20px', right: '20px', transform: 'scale(1.5)', zIndex: 2 }}
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => {
                              if (e.target.checked) setCompareItems([...compareItems, p.id]);
                              else setCompareItems(compareItems.filter(id => id !== p.id));
                            }} />
                        )}

                        <div className="prod-image-area" style={{ padding: 0, overflow: 'hidden' }}>
                          <ProductImage product={p} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        </div>

                        <div className="prod-content">
                          <div className="prod-header">
                            <div>
                              <div className="prod-title">{p.name} <span className="prod-brand">by {p.brand}</span></div>
                              <div className="badge blue" style={{ display: 'inline-block' }}>{p.category}</div>
                            </div>
                            <div className="prod-price">₨{p.price_pkr.toLocaleString()}</div>
                          </div>

                          <div className="prod-badges">
                            <span style={{ color: 'var(--gold)' }}>{"★".repeat(Math.round(p.rating))} ({p.rating})</span>
                            <span className={`badge ${p.sentiment_analysis?.sentiment_label === 'Highly Positive' ? 'green' : 'amber'}`}>Feedback: {p.sentiment_analysis?.sentiment_label}</span>
                            <span className="badge gold">{p.scores?.value_rating}</span>
                          </div>

                          <div className="prod-specs">
                            {safeSpecs(p.specs).map((s: string, i: number) => <span key={i} className="prod-spec-item">{s}</span>)}
                          </div>

                          <div style={{ marginTop: '15px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                              <span>Match Score</span>
                              <span>{p.scores?.total_score}/100</span>
                            </div>
                            <div className="score-bar-container">
                              <div className="score-fill" style={{ width: `${p.scores?.total_score}%`, background: idx === 0 ? 'var(--gold)' : idx === 1 ? 'var(--blue)' : 'var(--green)' }}></div>
                            </div>
                          </div>

                          <div className="justification-block">
                            {p.justification || p.personalization_note}
                          </div>

                          <div className="action-buttons">
                            <a href={p.search_url_daraz} target="_blank" className="btn-primary" style={{ textDecoration: 'none' }}>🛒 View on Daraz</a>
                            <a href={p.search_url_amazon} target="_blank" className="btn-outline" style={{ textDecoration: 'none' }}>🔍 Amazon Search</a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {!selectedProduct && (
                  <>
                    <h3 className="syne mt-20 mb-20">All Results</h3>
                    <div className="all-products-grid">
                      {(results.products || []).slice(3).map((p: Product) => (
                        <div
                          key={p.id}
                          className="prod-card-small"
                          onClick={() => setSelectedProduct(p)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              setSelectedProduct(p);
                            }
                          }}
                          role="button"
                          tabIndex={0}
                          aria-label={`Open details for ${p.name}`}
                        >
                          <div className="prod-small-emoji" style={{ padding: 0, overflow: 'hidden' }}>
                            <ProductImage product={p} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          </div>
                          <div className="prod-small-title">{p.name}</div>
                          <div className="prod-small-price">₨{p.price_pkr.toLocaleString()}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>★ {p.rating} • Score: {p.scores?.total_score}</div>
                        </div>
                      ))}
                    </div>
                  </>
                )}

              </div>
            )}
          </div>

          <div className="sidebar">
            <h3 className="sidebar-title">Live Dashboard</h3>

            <div className="sidebar-section">
              <div className="status-row"><div className="status-dot" style={{ background: backendStatus === 'online' ? 'var(--green)' : 'var(--text-secondary)' }}></div> {backendStatus === 'online' ? 'Backend online' : 'Backend offline — start API on port 8000'}</div>
              <div className="status-row"><div className="status-dot" style={{ background: 'var(--blue)' }}></div> DummyJSON live catalog</div>
              <div className="status-row"><div className="status-dot" style={{ background: 'var(--green)' }}></div> 10 Agents Active</div>
              <div className="status-row"><div className="status-dot" style={{ background: 'var(--purple)' }}></div> Llama 3.3 70B (Groq)</div>
            </div>

            <div className="sidebar-section">
              <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Last Query</h4>
              <div style={{ background: 'var(--glass)', padding: '10px', borderRadius: '8px', fontSize: '14px' }}>
                {lastQuery || query || "None"} <br />
                <span style={{ color: 'var(--gold)', fontSize: '12px' }}>{results?.products?.length ?? 0} found</span>
                {results?.retrieval_strategy ? (
                  <div style={{ marginTop: 8, fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                    <strong style={{ color: 'var(--blue)' }}>Retrieval:</strong> {results.retrieval_strategy}
                  </div>
                ) : null}
                {results?.extracted_preferences?.category ? (
                  <div style={{ marginTop: 4, fontSize: '11px', color: 'var(--text-secondary)' }}>
                    <strong style={{ color: 'var(--green)' }}>Category:</strong> {String(results.extracted_preferences.category)}
                  </div>
                ) : null}
              </div>
            </div>

            <div className="sidebar-section">
              <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>Quick Stats</h4>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <div style={{ background: 'var(--glass)', padding: '10px', borderRadius: '8px', flex: 1 }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{sessionSearches}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Searches</div>
                </div>
                <div style={{ background: 'var(--glass)', padding: '10px', borderRadius: '8px', flex: 1 }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{bestScoreSeen}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Best Score</div>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* Compare Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h2>Compare Products</h2>
              <button onClick={() => setShowModal(false)} style={{ fontSize: '24px', color: 'white' }}>×</button>
            </div>
            <table className="decision-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  {compareItems.map(id => {
                    const p = results?.products?.find((x: any) => x.id === id);
                    return <th key={id}>{p.name}</th>;
                  })}
                </tr>
              </thead>
              <tbody>
                <tr><td>Price</td>{compareItems.map(id => <td key={id}>₨{results?.products?.find((x: any) => x.id === id).price_pkr.toLocaleString()}</td>)}</tr>
                <tr><td>Rating</td>{compareItems.map(id => <td key={id}>{results?.products?.find((x: any) => x.id === id).rating}</td>)}</tr>
                <tr><td>AI Score</td>{compareItems.map(id => <td key={id}>{results?.products?.find((x: any) => x.id === id).scores?.total_score}/100</td>)}</tr>
                <tr><td>Sentiment</td>{compareItems.map(id => <td key={id}>{results?.products?.find((x: any) => x.id === id).sentiment_analysis?.sentiment_label}</td>)}</tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Test Queries Panel */}
      <section className="test-queries">
        <h3 className="syne mb-20" style={{ textAlign: 'center' }}>50 Test Queries Evaluator</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center' }}>
          {Object.entries(TEST_QUERIES).map(([cat, arr]) => (
            <div key={cat} style={{ background: 'var(--bg-secondary)', padding: '15px', borderRadius: '12px', minWidth: '250px' }}>
              <h4 style={{ marginBottom: '10px', color: 'var(--blue)' }}>{cat} ({arr.length})</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {arr.map((q, i) => (
                  <button key={i} style={{ textAlign: 'left', background: 'var(--glass)', padding: '8px 12px', borderRadius: '6px', color: 'white', fontSize: '12px' }}
                    onClick={() => { window.scrollTo(0, 0); runSearch(q); }}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <footer>
        <div className="footer-grid">
          <div>
            <h2 className="syne footer-brand" style={{ color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShoppingCart size={32} strokeWidth={2} aria-hidden />
              AuraCart
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '10px', fontSize: '14px' }}>Intelligent Shopping Powered by 10 LangGraph Agents</p>
          </div>
          <div>
            <h4>Project Links</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px', fontSize: '14px', color: 'var(--text-secondary)' }}>
              <a href="https://github.com/Eman-Sarfraz/Aura_Cart" target="_blank" rel="noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none' }}>GitHub Repository</a>
              <a href="https://github.com/Eman-Sarfraz/Aura_Cart/blob/main/report.md" target="_blank" rel="noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none' }}>Project Report</a>
              <a href="https://github.com/Eman-Sarfraz/Aura_Cart/blob/main/architecture_diagram.png" target="_blank" rel="noreferrer" style={{ color: 'var(--blue)', textDecoration: 'none' }}>Architecture Diagram</a>
            </div>
          </div>
          <div>
            <h4>Tech Stack</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px', fontSize: '14px', color: 'var(--text-secondary)' }}>
              <span>React 18 + Vite</span>
              <span>FastAPI Backend</span>
              <span>LangGraph + ChatGroq (Llama3)</span>
              <span>DummyJSON + DuckDuckGo</span>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          built by EMAN SARFRAZ · 10 Agents · live API catalog · 50 Test Cases
        </div>
      </footer>
    </div>
  );
}
