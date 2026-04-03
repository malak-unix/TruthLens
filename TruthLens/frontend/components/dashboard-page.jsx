"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
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
  factCheckTips,
  navigationItems,
  topicStats,
} from "../lib/mock-data";

import {
  fetchNews,
  fetchCategories,
  analyzeContent,
  chatWithAssistant,
  registerUser,
  loginUser,
  fetchCurrentUser,
} from "../lib/api";

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

const assistantGuardrails = [
  "Summarize a claim",
  "Explain a score",
  "Rephrase a claim",
  "Suggest verification steps",
];

function formatPercent(score) {
  return `${score}%`;
}

function getApiCountry(region) {
  return region === "morocco" ? "ma" : "world";
}

function getScoreColor(score) {
  if (score >= 80) return "var(--success-strong)";
  if (score >= 50) return "var(--warning-strong)";
  return "var(--danger)";
}

function getBadgeClass(label) {
  if (label === "Reliable") return "status-chip-success";
  if (label === "Needs Context" || label === "Unverified") return "status-chip-warning";
  return "status-chip-danger";
}

function getToneFromLabel(label) {
  if (label === "Reliable") return "reliable";
  if (label === "Needs Context" || label === "Unverified") return "watch";
  return "risk";
}

function getAnalysisTitle(label) {
  if (label === "Reliable") return "Source solide detectee";
  if (label === "Needs Context") return "Contexte supplementaire requis";
  if (label === "Unverified") return "Signal precoce";
  if (label === "Suspicious") return "Contenu suspect";
  if (label === "High Risk") return "Risque eleve";
  if (label === "No Input") return "Pret pour l'analyse";
  return "Analyse terminee";
}

function formatTimeAgo(publishedAt) {
  const published = new Date(publishedAt);
  const now = new Date();
  const diffMs = now - published;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffMinutes > 0) return `${diffMinutes} min ago`;
  return "Just now";
}

function getCategoryImage(category) {
  const images = {
    Economy:
      "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=900&q=80",
    Health:
      "https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?auto=format&fit=crop&w=900&q=80",
    Technology:
      "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80",
    Society:
      "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=900&q=80",
    Sports:
      "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=900&q=80",
    Politics:
      "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=900&q=80",
  };

  return (
    images[category] ||
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80"
  );
}

function mapBackendArticle(article) {
  return {
    id: article.url,
    title: article.title,
    category: article.category,
    source: article.source_name,
    timeAgo: formatTimeAgo(article.published_at),
    summary: article.description,
    score: article.credibility_score,
    badge: article.credibility_label,
    badgeClass: getBadgeClass(article.credibility_label),
    scoreColor: getScoreColor(article.credibility_score),
    image: getCategoryImage(article.category),
    url: article.url,
    region: article.country === "ma" ? "morocco" : "world",
    explanation: article.explanation,
  };
}

function buildEmptyAnalysis() {
  return {
    title: "Pret pour l'analyse",
    score: 0,
    label: "Aucune entree",
    tone: "watch",
    explanation:
      "Collez une URL ou un texte. Cette zone est maintenant connectee au backend FastAPI /analyze.",
    evidence: ["Champ vide", "Attente d'une saisie utilisateur"],
  };
}

function buildEmptyAssistantReply() {
  return {
    answer:
      "Ask the TruthLens assistant to summarize a claim, explain a credibility score, or suggest verification steps.",
    suggested_checks: [
      "Paste a short claim or headline.",
      "Ask what to verify first.",
      "Ask which sources should confirm the story.",
    ],
    grounded_in_scope: true,
    model: "gemini-1.5-flash",
  };
}

function mapAnalysisResult(result) {
  return {
    title: getAnalysisTitle(result.credibility_label),
    score: result.credibility_score,
    label: result.credibility_label,
    tone: getToneFromLabel(result.credibility_label),
    explanation: result.explanation,
    evidence:
      result.risk_signals && result.risk_signals.length > 0
        ? result.risk_signals
        : ["No major risk signal detected"],
  };
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

          <a
            className="ghost-icon-button"
            aria-label="Open article preview"
            href={article.url}
            target="_blank"
            rel="noreferrer"
          >
            <ExternalLink size={18} />
          </a>
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

function SummaryCard({ eyebrow, title, description, value, index }) {
  return (
    <article className="article-card" style={{ animationDelay: `${index * 90}ms` }}>
      <div className="article-card__content">
        <div className="article-card__header">
          <div>
            <p className="article-card__eyebrow">{eyebrow}</p>
            <h3>{title}</h3>
          </div>
        </div>

        <p className="article-card__summary">{description}</p>

        <div className="article-card__footer">
          <div className="credibility-block">
            <span>Value:</span>
            <strong>{value}</strong>
          </div>
        </div>
      </div>
    </article>
  );
}

function AssistantPanel({
  assistantInput,
  setAssistantInput,
  assistantLoading,
  assistantError,
  assistantReply,
  handleAssistantAsk,
  contextArticle,
  className,
}) {
  return (
    <section className={clsx("side-card", "assistant-card", className)}>
      <div className="side-card__header">
        <div className="section-title">
          <Sparkles size={20} />
          <h3>Assistant</h3>
        </div>
      </div>

      <textarea
        className="fact-check-input"
        rows={6}
        placeholder="Ask for a summary, an explanation of the score, or next verification steps..."
        value={assistantInput}
        onChange={(event) => setAssistantInput(event.target.value)}
      />

      <p className="hero-card__note">
        Scope: summaries, score explanations, claim reformulation, and next verification steps.
      </p>

      {contextArticle ? (
        <p className="hero-card__note">
          Context article: {contextArticle.title}
        </p>
      ) : null}

      <button
        type="button"
        className="primary-button"
        onClick={handleAssistantAsk}
        disabled={assistantLoading}
      >
        {assistantLoading ? "Asking..." : "Ask Assistant"}
      </button>

      {assistantError ? (
        <p className="hero-card__note" style={{ color: "var(--danger)" }}>
          {assistantError}
        </p>
      ) : null}

      <div
        className="analysis-preview"
        style={{ "--analysis-accent": "var(--warning-strong)" }}
      >
        <div className="analysis-preview__header">
          <div>
            <p className="analysis-preview__eyebrow">TruthLens Assistant</p>
            <strong>Guided fact-check support</strong>
          </div>
          <span
            className={clsx(
              "status-chip",
              assistantReply.grounded_in_scope
                ? "status-chip-warning"
                : "status-chip-danger",
            )}
          >
            {assistantReply.grounded_in_scope ? "Scoped" : "Out of scope"}
          </span>
        </div>

        <p>{assistantReply.answer}</p>

        <p className="hero-card__note">Model: {assistantReply.model}</p>

        <ul className="signal-list">
          {assistantReply.suggested_checks.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="tips-row">
        {assistantGuardrails.map((item) => (
          <span key={item} className="hint-pill">
            {item}
          </span>
        ))}
      </div>
    </section>
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
  const [assistantInput, setAssistantInput] = useState("");
  const [assistantReply, setAssistantReply] = useState(buildEmptyAssistantReply());
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState("");

  const [articles, setArticles] = useState([]);
  const [articleCategories, setArticleCategories] = useState(["All"]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState("");

  const [analysisResult, setAnalysisResult] = useState(buildEmptyAnalysis());
  const [analyzing, setAnalyzing] = useState(false);

  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfilePanel, setShowProfilePanel] = useState(false);

  const [authMode, setAuthMode] = useState("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  const [authToken, setAuthToken] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  const deferredSearch = useDeferredValue(searchTerm);

  function pushNotification(title, message, type = "info") {
    const item = {
      id: Date.now() + Math.random(),
      title,
      message,
      type,
      read: false,
      createdAt: new Date().toLocaleTimeString(),
    };

    setNotifications((prev) => [item, ...prev].slice(0, 12));
  }

  const unreadCount = notifications.filter((item) => !item.read).length;

  function closeOverlays() {
    setShowNotifications(false);
    setShowProfilePanel(false);
  }

  function openNotifications() {
    setShowNotifications((prev) => !prev);
    setShowProfilePanel(false);
    setNotifications((prev) => prev.map((item) => ({ ...item, read: true })));
  }

  function openProfilePanel() {
    setShowProfilePanel((prev) => !prev);
    setShowNotifications(false);
  }

  function logoutUser() {
    localStorage.removeItem("truthlens_token");
    setAuthToken(null);
    setCurrentUser(null);
    setShowProfilePanel(false);
    pushNotification("Logged out", "Your session has been closed.", "info");
  }

  async function handleRegister() {
    try {
      setAuthLoading(true);
      setAuthError("");

      const data = await registerUser({
        email: authEmail,
        password: authPassword,
        full_name: authFullName || null,
      });

      localStorage.setItem("truthlens_token", data.access_token);
      setAuthToken(data.access_token);
      setCurrentUser(data.user);
      setShowProfilePanel(false);

      pushNotification(
        "Account created",
        `Welcome ${data.user.full_name || data.user.email}`,
        "success"
      );

      setAuthEmail("");
      setAuthPassword("");
      setAuthFullName("");
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogin() {
    try {
      setAuthLoading(true);
      setAuthError("");

      const data = await loginUser({
        email: authEmail,
        password: authPassword,
      });

      localStorage.setItem("truthlens_token", data.access_token);
      setAuthToken(data.access_token);
      setCurrentUser(data.user);
      setShowProfilePanel(false);

      pushNotification(
        "Login successful",
        `Connected as ${data.user.full_name || data.user.email}`,
        "success"
      );

      setAuthEmail("");
      setAuthPassword("");
      setAuthFullName("");
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setAuthLoading(false);
    }
  }

  useEffect(() => {
    setChartReady(true);
    const savedToken = localStorage.getItem("truthlens_token");
    if (savedToken) {
      setAuthToken(savedToken);
    }
  }, []);

  useEffect(() => {
    async function loadCurrentUser() {
      if (!authToken) return;

      try {
        const user = await fetchCurrentUser(authToken);
        setCurrentUser(user);
      } catch (error) {
        console.error("Failed to fetch current user:", error);
        localStorage.removeItem("truthlens_token");
        setAuthToken(null);
        setCurrentUser(null);
      }
    }

    loadCurrentUser();
  }, [authToken]);

  useEffect(() => {
    async function loadCategories() {
      try {
        const data = await fetchCategories();
        setArticleCategories(["All", ...data]);
      } catch (error) {
        console.error("Failed to load categories:", error);
      }
    }

    loadCategories();
  }, []);

  useEffect(() => {
    async function loadNews() {
      try {
        setNewsLoading(true);
        setNewsError("");

        const apiCountry = getApiCountry(activeRegion);
        const data = await fetchNews(
          apiCountry,
          activeCategory === "All" ? "" : activeCategory
        );

        const mapped = data.map(mapBackendArticle);
        setArticles(mapped);

        pushNotification(
          "News updated",
          `${mapped.length} article(s) loaded for ${regionLabels[activeRegion]}.`,
          "info"
        );
      } catch (error) {
        console.error("Failed to load news:", error);
        setNewsError("Impossible de charger les actualites.");
      } finally {
        setNewsLoading(false);
      }
    }

    loadNews();
  }, [activeRegion, activeCategory]);

  async function handleAnalyze() {
    if (!factInput.trim()) {
      setAnalysisResult(buildEmptyAnalysis());
      return;
    }

    try {
      setAnalyzing(true);

      const payload =
        factCheckMode === "url"
          ? { url: factInput.trim() }
          : { text: factInput.trim() };

      const result = await analyzeContent(payload);
      const mapped = mapAnalysisResult(result);
      setAnalysisResult(mapped);

      pushNotification(
        "Analysis completed",
        `${mapped.label} - ${mapped.score}%`,
        mapped.label === "High Risk" || mapped.label === "Suspicious" ? "danger" : "success"
      );
    } catch (error) {
      console.error("Analyze failed:", error);
      setAnalysisResult({
        title: "Erreur d'analyse",
        score: 0,
        label: "Error",
        tone: "risk",
        explanation: "Le backend n'a pas pu analyser cette entree.",
        evidence: ["Erreur backend ou reponse invalide"],
      });

      pushNotification("Analysis failed", "The backend could not process this request.", "danger");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleAssistantAsk() {
    const message = assistantInput.trim();

    if (!message) {
      setAssistantError("");
      setAssistantReply(buildEmptyAssistantReply());
      return;
    }

    const contextArticle = visibleArticles[0];

    try {
      setAssistantLoading(true);
      setAssistantError("");

      const result = await chatWithAssistant({
        message,
        article_title: contextArticle?.title,
        article_summary: contextArticle?.summary,
        article_score: contextArticle?.score,
        article_label: contextArticle?.badge,
      });

      setAssistantReply(result);
      pushNotification("Assistant ready", "The assistant returned a guided response.", "info");
    } catch (error) {
      console.error("Assistant request failed:", error);
      setAssistantError("The assistant could not answer right now.");
      setAssistantReply({
        answer: "The assistant is temporarily unavailable.",
        suggested_checks: [
          "Retry the request in a moment.",
          "Use the Fact-Check Corner while the assistant is unavailable.",
        ],
        grounded_in_scope: true,
        model: "unavailable",
      });
      pushNotification("Assistant unavailable", "The assistant request failed.", "danger");
    } finally {
      setAssistantLoading(false);
    }
  }

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

  const categorySummary = useMemo(() => {
    return articleCategories
      .filter((cat) => cat !== "All")
      .map((cat) => ({
        label: cat,
        value: articles.filter((article) => article.category === cat).length,
      }));
  }, [articleCategories, articles]);

  const activeTopics = topicStats[activeRegion];
  const activity = activitySeries[activeRegion];
  const resultStyle = resultStyles[analysisResult.tone] || resultStyles.watch;

  return (
    <main className="dashboard-shell">
      <aside className="assistant-sidebar">
        <div className="brand-mark">
          <div className="brand-mark__logo">T</div>
          <div>
            <h1>TruthLens</h1>
            <p>Monitoring studio</p>
          </div>
        </div>

        <AssistantPanel
          assistantInput={assistantInput}
          setAssistantInput={setAssistantInput}
          assistantLoading={assistantLoading}
          assistantError={assistantError}
          assistantReply={assistantReply}
          handleAssistantAsk={handleAssistantAsk}
          contextArticle={visibleArticles[0]}
        />

        <div className="sidebar-footer">
          <p>TruthLens v1.0</p>
          <span>{currentUser ? "User connected" : "Gemini-ready assistant"}</span>
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
            <button
              className="ghost-icon-button"
              aria-label="Notifications"
              onClick={openNotifications}
            >
              <Bell size={20} />
              {unreadCount > 0 && <span className="topbar-dot" />}
            </button>

            <button
              className="ghost-icon-button"
              aria-label="Profile"
              onClick={openProfilePanel}
            >
              <UserRound size={20} />
            </button>
          </div>
        </header>

        <nav className="top-nav" aria-label="Top navigation">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;

            return (
              <button
                key={item.id}
                type="button"
                className={clsx("top-nav__item", isActive && "is-active")}
                onClick={() => setActiveNav(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {activeNav === "dashboard" && (
          <>
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
                  Backend live data
                </span>
                <span className="hero-card__note">
                  Backend FastAPI + SQLite + JWT connecte
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
                      activeRegion === key && "is-active"
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
                    activeCategory === category && "is-active"
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
              {newsLoading ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>Loading news...</h3>
                    <p>Le tableau de bord charge les actualites depuis le backend.</p>
                  </div>
                </div>
              ) : newsError ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>Erreur de chargement</h3>
                    <p>{newsError}</p>
                  </div>
                </div>
              ) : visibleArticles.length > 0 ? (
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
          </>
        )}

        {activeNav === "trending" && (
          <>
            <section className="hero-card">
              <div>
                <p className="hero-card__kicker">Trending overview</p>
                <h2>Trending Topics</h2>
                <p className="hero-card__subtitle">
                  Vue rapide des sujets les plus suivis pour {regionLabels[activeRegion]}.
                </p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  Live topic snapshot
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
                      activeRegion === key && "is-active"
                    )}
                    onClick={() => setActiveRegion(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="news-list">
              {activeTopics.map((topic, index) => (
                <SummaryCard
                  key={topic.label}
                  eyebrow="Trending"
                  title={topic.label}
                  description="Ce sujet est actuellement parmi les plus suivis dans la region selectionnee."
                  value={topic.value}
                  index={index}
                />
              ))}
            </div>
          </>
        )}

        {activeNav === "categories" && (
          <>
            <section className="hero-card">
              <div>
                <p className="hero-card__kicker">Category overview</p>
                <h2>Categories</h2>
                <p className="hero-card__subtitle">
                  Repartition des actualites chargees depuis le backend par categorie.
                </p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  Backend category snapshot
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
                      activeRegion === key && "is-active"
                    )}
                    onClick={() => setActiveRegion(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="news-list">
              {categorySummary.map((item, index) => (
                <SummaryCard
                  key={item.label}
                  eyebrow="Category"
                  title={item.label}
                  description="Nombre d'articles actuellement disponibles dans cette categorie."
                  value={item.value}
                  index={index}
                />
              ))}
            </div>
          </>
        )}

        {activeNav === "statistics" && (
          <>
            <section className="hero-card">
              <div>
                <p className="hero-card__kicker">System metrics</p>
                <h2>Statistics</h2>
                <p className="hero-card__subtitle">
                  Activite du systeme, volume de verification et suivi des contenus.
                </p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  SQLite metrics
                </span>
              </div>
            </section>

            <section className="side-card activity-card" style={{ marginTop: "1rem" }}>
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
                        <linearGradient id="activityGradientStats" x1="0" x2="0" y1="0" y2="1">
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
                        fill="url(#activityGradientStats)"
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
                  <strong>{articles.length}</strong>
                  <span>articles currently loaded</span>
                </div>
                <div>
                  <strong>{notifications.length}</strong>
                  <span>notifications created</span>
                </div>
              </div>
            </section>
          </>
        )}
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
                factCheckMode === "url" && "is-active"
              )}
              onClick={() => setFactCheckMode("url")}
            >
              URL
            </button>
            <button
              type="button"
              className={clsx(
                "fact-check-switch__button",
                factCheckMode === "text" && "is-active"
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

          <button
            type="button"
            className="primary-button"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? "Analyzing..." : "Analyze Now"}
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

      {showNotifications && (
        <>
          <div
            onClick={closeOverlays}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(15, 23, 42, 0.18)",
              zIndex: 9998,
            }}
          />

          <div
            style={{
              position: "fixed",
              top: "88px",
              right: "32px",
              width: "340px",
              background: "#fff",
              border: "1px solid #eceef3",
              borderRadius: "20px",
              boxShadow: "0 20px 50px rgba(15, 23, 42, 0.18)",
              padding: "16px",
              zIndex: 9999,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
              }}
            >
              <strong>Notifications</strong>
              <button
                onClick={() => setNotifications([])}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "#64748b",
                  fontWeight: 600,
                }}
              >
                Clear
              </button>
            </div>

            {notifications.length === 0 ? (
              <p style={{ color: "#738197", fontSize: "14px", margin: 0 }}>
                No notifications yet.
              </p>
            ) : (
              <div style={{ display: "grid", gap: "10px", maxHeight: "320px", overflowY: "auto" }}>
                {notifications.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: "12px",
                      borderRadius: "14px",
                      background: "#f8fafc",
                      border: "1px solid #edf1f6",
                    }}
                  >
                    <strong style={{ display: "block", marginBottom: "4px" }}>{item.title}</strong>
                    <p style={{ margin: 0, color: "#516079", fontSize: "14px" }}>{item.message}</p>
                    <span style={{ fontSize: "12px", color: "#94a3b8" }}>{item.createdAt}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {showProfilePanel && (
        <>
          <div
            onClick={closeOverlays}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(15, 23, 42, 0.28)",
              zIndex: 9998,
            }}
          />

          <div
            style={{
              position: "fixed",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              width: "min(92vw, 440px)",
              background: "#fff",
              border: "1px solid #eceef3",
              borderRadius: "24px",
              boxShadow: "0 28px 60px rgba(15, 23, 42, 0.18)",
              padding: "20px",
              zIndex: 9999,
            }}
          >
            {currentUser ? (
              <div style={{ display: "grid", gap: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong>Connected user</strong>
                  <button
                    onClick={closeOverlays}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "18px",
                      color: "#64748b",
                    }}
                  >
                    ×
                  </button>
                </div>

                <div style={{ color: "#516079", display: "grid", gap: "6px" }}>
                  <div><strong>Email:</strong> {currentUser.email}</div>
                  <div><strong>Name:</strong> {currentUser.full_name || "Not provided"}</div>
                </div>

                <button
                  className="primary-button"
                  type="button"
                  onClick={logoutUser}
                >
                  Logout
                </button>
              </div>
            ) : (
              <div style={{ display: "grid", gap: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      type="button"
                      className={clsx("fact-check-switch__button", authMode === "login" && "is-active")}
                      onClick={() => {
                        setAuthMode("login");
                        setAuthError("");
                      }}
                    >
                      Login
                    </button>
                    <button
                      type="button"
                      className={clsx("fact-check-switch__button", authMode === "register" && "is-active")}
                      onClick={() => {
                        setAuthMode("register");
                        setAuthError("");
                      }}
                    >
                      Sign up
                    </button>
                  </div>

                  <button
                    onClick={closeOverlays}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "18px",
                      color: "#64748b",
                    }}
                  >
                    ×
                  </button>
                </div>

                {authMode === "register" && (
                  <input
                    type="text"
                    placeholder="Full name"
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    className="fact-check-input"
                    style={{ minHeight: "52px" }}
                  />
                )}

                <input
                  type="email"
                  placeholder="Email"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  className="fact-check-input"
                  style={{ minHeight: "52px" }}
                />

                <input
                  type="password"
                  placeholder="Password"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  className="fact-check-input"
                  style={{ minHeight: "52px" }}
                />

                {authError && (
                  <p style={{ color: "var(--danger)", margin: 0, fontSize: "14px" }}>
                    {authError}
                  </p>
                )}

                <button
                  className="primary-button"
                  type="button"
                  onClick={authMode === "login" ? handleLogin : handleRegister}
                  disabled={authLoading}
                >
                  {authLoading
                    ? "Please wait..."
                    : authMode === "login"
                    ? "Login"
                    : "Create account"}
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </main>
  );
}
