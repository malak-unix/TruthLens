"use client";

import { useDeferredValue, useEffect, useState } from "react";
import clsx from "clsx";
import {
  Activity,
  Bell,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Search,
  Sparkles,
  UserRound,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";
import {
  activitySeries,
  articleCategories,
  articles,
  factCheckTips,
  navigationItems,
  topicStats,
} from "../lib/mock-data";

const regionLabels = {
  morocco: "Morocco",
  world: "World",
};

const resultStyles = {
  reliable: {
    accent: "var(--success-strong)",
    chipClass: "status-chip status-chip-success",
  },
  watch: {
    accent: "var(--warning-strong)",
    chipClass: "status-chip status-chip-warning",
  },
  risk: {
    accent: "var(--danger)",
    chipClass: "status-chip status-chip-danger",
  },
};

function buildMockAnalysis(input, mode) {
  const query = input.trim().toLowerCase();

  if (!query) {
    return {
      title: "Pret pour l'analyse",
      score: 0,
      label: "Aucune entree",
      tone: "watch",
      explanation:
        "Collez une URL ou un texte. Cette zone est deja preparee pour etre branchee sur l'endpoint FastAPI /analyze.",
      evidence: ["Champ vide", "Attente d'une saisie utilisateur"],
    };
  }

  if (mode === "url") {
    if (/(gov|who\\.int|un\\.org|guardian|lematin|mapnews)/.test(query)) {
      return {
        title: "Source solide detectee",
        score: 88,
        label: "Likely Reliable",
        tone: "reliable",
        explanation:
          "Le lien semble pointer vers un domaine institutionnel ou editorial etabli. La suite cote backend confirmera la corroboration et les metadonnees.",
        evidence: ["Domaine reconnu", "Schema URL propre", "A verifier avec corroboration"],
      };
    }

    if (/(telegram|rumor|blogspot|viral|breaking-news)/.test(query)) {
      return {
        title: "URL a surveiller",
        score: 41,
        label: "Needs Review",
        tone: "risk",
        explanation:
          "Le lien contient des indices frequents de source secondaire ou peu claire. Le moteur backend devra verifier la reputation de la source et les preuves externes.",
        evidence: ["Source peu claire", "Risque de relais viral", "Corroboration necessaire"],
      };
    }

    return {
      title: "Signal precoce",
      score: 67,
      label: "Early Signal",
      tone: "watch",
      explanation:
        "Le lien est exploitable mais il faut encore enrichir la source, le contenu et la corroboration. L'UX est deja en place pour recevoir la reponse du backend.",
      evidence: ["URL valide", "Score intermediaire", "Enrichissement backend a venir"],
    };
  }

  if (/(urgent|partagez|share|secret|miracle|complot|scandale)/.test(query)) {
    return {
      title: "Texte suspect",
      score: 26,
      label: "High Risk",
      tone: "risk",
      explanation:
        "Le texte contient des marqueurs de sensationnalisme et d'incitation au partage. C'est le type de signal que le moteur de credibilite doit penaliser.",
      evidence: ["Vocabulaire alarmiste", "Attribution absente", "Verification prioritaire"],
    };
  }

  return {
    title: "Contenu exploitable",
    score: 73,
    label: "Needs Context",
    tone: "watch",
    explanation:
      "Le texte a une structure informative mais manque encore de contexte et de sources confirmees. La future integration FastAPI ajoutera la corroboration automatique.",
    evidence: ["Texte structure", "Sources non confirmees", "Analyse detaillee a connecter"],
  };
}

function formatPercent(score) {
  return `${score}%`;
}

function ArticleCard({ article, index }) {
  return (
    <article className="article-card" style={{ animationDelay: `${index * 90}ms` }}>
      <div
        className="article-card__media"
        style={{ backgroundImage: `url('${article.image}')` }}
      />

      <div className="article-card__content">
        <div className="article-card__header">
          <div>
            <p className="article-card__eyebrow">{article.category}</p>
            <h3>{article.title}</h3>
          </div>
          <button className="ghost-icon-button" aria-label="Open article preview">
            <ExternalLink size={18} />
          </button>
        </div>

        <div className="article-card__meta">
          <span>{article.source}</span>
          <span className="meta-separator">|</span>
          <span className="meta-time">
            <Clock3 size={14} />
            {article.timeAgo}
          </span>
        </div>

        <p className="article-card__summary">{article.summary}</p>

        <div className="article-card__footer">
          <div className="credibility-block">
            <span>Credibility:</span>
            <strong style={{ color: article.scoreColor }}>
              {formatPercent(article.score)}
            </strong>
          </div>
          <span className={clsx("status-chip", article.badgeClass)}>{article.badge}</span>
        </div>
      </div>
    </article>
  );
}

export function DashboardPage() {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [activeRegion, setActiveRegion] = useState("morocco");
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [factCheckMode, setFactCheckMode] = useState("url");
  const [factInput, setFactInput] = useState("");
  const [chartReady, setChartReady] = useState(false);
  const deferredSearch = useDeferredValue(searchTerm);
  const analysisResult = buildMockAnalysis(factInput, factCheckMode);

  useEffect(() => {
    setChartReady(true);
  }, []);

  const visibleArticles = articles.filter((article) => {
    const matchesRegion = article.region === activeRegion;
    const matchesCategory =
      activeCategory === "All" || article.category === activeCategory;
    const normalizedSearch = deferredSearch.trim().toLowerCase();
    const matchesSearch =
      normalizedSearch.length === 0 ||
      article.title.toLowerCase().includes(normalizedSearch) ||
      article.source.toLowerCase().includes(normalizedSearch) ||
      article.summary.toLowerCase().includes(normalizedSearch);

    return matchesRegion && matchesCategory && matchesSearch;
  });

  const activeTopics = topicStats[activeRegion];
  const activity = activitySeries[activeRegion];
  const resultStyle = resultStyles[analysisResult.tone];

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <div className="brand-mark__logo">T</div>
          <div>
            <h1>TruthLens</h1>
            <p>Monitoring studio</p>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Sidebar navigation">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;

            return (
              <button
                key={item.id}
                type="button"
                className={clsx("sidebar-nav__item", isActive && "is-active")}
                onClick={() => setActiveNav(item.id)}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <p>TruthLens v1.0</p>
          <span>Frontend MVP</span>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <label className="search-field">
            <Search size={22} />
            <input
              type="search"
              placeholder="Search news, sources, topics..."
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
            />
          </label>

          <div className="topbar-actions">
            <button className="ghost-icon-button" aria-label="Notifications">
              <Bell size={20} />
              <span className="topbar-dot" />
            </button>
            <button className="ghost-icon-button" aria-label="Profile">
              <UserRound size={20} />
            </button>
          </div>
        </header>

        <section className="hero-card">
          <div>
            <p className="hero-card__kicker">Real-time credibility analysis</p>
            <h2>Viral News Monitor</h2>
            <p className="hero-card__subtitle">
              Suivi live des actualites Maroc et Monde avec badge de credibilite,
              categories et coin de verification.
            </p>
          </div>

          <div className="hero-card__status">
            <span className="status-chip status-chip-soft">
              <Sparkles size={14} />
              Refresh 06:00 / 12:00 / 18:00
            </span>
            <span className="hero-card__note">
              Base Next.js prete pour le branchement FastAPI
            </span>
          </div>
        </section>

        <div className="content-toolbar">
          <div className="toggle-pill">
            {Object.entries(regionLabels).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={clsx(
                  "toggle-pill__button",
                  activeRegion === key && "is-active",
                )}
                onClick={() => setActiveRegion(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="category-row" role="tablist" aria-label="News categories">
          {articleCategories.map((category) => (
            <button
              key={category}
              type="button"
              className={clsx(
                "category-pill",
                activeCategory === category && "is-active",
              )}
              onClick={() => setActiveCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>

        <div className="results-caption">
          <span>
            {visibleArticles.length} story{visibleArticles.length > 1 ? "ies" : "y"} for{" "}
            {regionLabels[activeRegion]}
          </span>
          <span>
            Focus: {activeCategory === "All" ? "All categories" : activeCategory}
          </span>
        </div>

        <div className="news-list">
          {visibleArticles.length > 0 ? (
            visibleArticles.map((article, index) => (
              <ArticleCard key={article.id} article={article} index={index} />
            ))
          ) : (
            <div className="empty-state">
              <CheckCircle2 size={28} />
              <div>
                <h3>No results for this filter set</h3>
                <p>
                  Essayez une autre recherche ou revenez a la vue All pour
                  poursuivre l'exploration.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

      <aside className="insight-panel">
        <section className="side-card fact-check-card">
          <div className="side-card__header">
            <div className="section-title">
              <Search size={20} />
              <h3>Fact-Check Corner</h3>
            </div>
          </div>

          <div className="fact-check-switch">
            <button
              type="button"
              className={clsx(
                "fact-check-switch__button",
                factCheckMode === "url" && "is-active",
              )}
              onClick={() => setFactCheckMode("url")}
            >
              URL
            </button>
            <button
              type="button"
              className={clsx(
                "fact-check-switch__button",
                factCheckMode === "text" && "is-active",
              )}
              onClick={() => setFactCheckMode("text")}
            >
              Text
            </button>
          </div>

          <textarea
            className="fact-check-input"
            rows={4}
            placeholder={
              factCheckMode === "url"
                ? "Paste article URL..."
                : "Paste headline, article or claim..."
            }
            value={factInput}
            onChange={(event) => setFactInput(event.target.value)}
          />

          <button type="button" className="primary-button">
            Analyze Now
          </button>

          <div
            className="analysis-preview"
            style={{ "--analysis-accent": resultStyle.accent }}
          >
            <div className="analysis-preview__header">
              <div>
                <p className="analysis-preview__eyebrow">{analysisResult.title}</p>
                <strong>{analysisResult.label}</strong>
              </div>
              <span className={resultStyle.chipClass}>
                {analysisResult.score > 0 ? formatPercent(analysisResult.score) : "--"}
              </span>
            </div>

            <p>{analysisResult.explanation}</p>

            <ul className="signal-list">
              {analysisResult.evidence.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="tips-row">
            {factCheckTips.map((tip) => (
              <span key={tip} className="hint-pill">
                {tip}
              </span>
            ))}
          </div>
        </section>

        <section className="side-card">
          <div className="side-card__header">
            <div className="section-title">
              <Activity size={20} />
              <h3>Trending Topics</h3>
            </div>
          </div>

          <div className="topic-list">
            {activeTopics.map((topic) => (
              <div key={topic.label} className="topic-row">
                <span>{topic.label}</span>
                <strong>{topic.value}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="side-card activity-card">
          <div className="side-card__header">
            <div className="section-title">
              <Activity size={20} />
              <h3>Today&apos;s Activity</h3>
            </div>
          </div>

          <div className="activity-chart">
            {chartReady ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activity}>
                  <defs>
                    <linearGradient id="activityGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#ff3030" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#ff3030" stopOpacity={0.04} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#edf1f6" />
                  <XAxis
                    dataKey="time"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: "#738197", fontSize: 12 }}
                  />
                  <Tooltip />
                  <Area
                    dataKey="checks"
                    type="monotone"
                    stroke="#ea1d2c"
                    strokeWidth={2}
                    fill="url(#activityGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="activity-placeholder">
                <span />
                <span />
                <span />
                <span />
                <span />
              </div>
            )}
          </div>

          <div className="activity-summary">
            <div>
              <strong>{activeRegion === "morocco" ? "124" : "173"}</strong>
              <span>checks analysed today</span>
            </div>
            <div>
              <strong>{activeRegion === "morocco" ? "18" : "31"}</strong>
              <span>stories flagged for review</span>
            </div>
          </div>
        </section>
      </aside>
    </main>
  );
}
