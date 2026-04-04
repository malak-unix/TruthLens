"use client";

import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import {
  Activity,
  Bell,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Link2,
  MessageSquareText,
  Search,
  SendHorizontal,
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

import { assistantStarterPrompts, navigationItems } from "../lib/mock-data";

import {
  fetchNews,
  fetchCategories,
  fetchTrending,
  fetchOverviewStats,
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

function getApiRegion(region) {
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
    International:
      "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=900&q=80",
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
    batchLabel: article.batch_label,
    sourceType: article.source_type,
    sourceTrustLevel: article.source_trust_level,
    priorityTopic: article.priority_topic || "",
    rankingScore: article.ranking_score || 0,
  };
}

function mapTrendingTopic(topic) {
  return {
    id: `${topic.region}-${topic.normalized_topic || topic.topic}`,
    label: topic.title || topic.topic,
    normalizedTopic: topic.normalized_topic || topic.topic,
    value: topic.intensity,
    articleCount: topic.related_articles_count || topic.article_count,
    freshness: topic.freshness_label || topic.freshness,
    credibilityWarning: topic.credibility_warning,
    region: topic.region === "ma" ? "morocco" : "world",
    sourceSignals: topic.source_signals || [],
    platformSignals: topic.platform_signals || [],
    viralityScore: topic.virality_score || topic.intensity,
    verificationGapScore: topic.verification_gap_score || 0,
    confidenceNote: topic.confidence_note || "",
    recencyScore: topic.recency_score || 0,
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
    sourceScore: 0,
    articleScore: 0,
    corroborationScore: 0,
    verificationStatus: "No verification yet",
    sourceProfile: null,
    finalLabel: "Aucune entree",
  };
}

function buildConversationMessage(role, content, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random()}`,
    role,
    content,
    suggestedChecks: extra.suggestedChecks || [],
    quickActions: extra.quickActions || [],
    model: extra.model || "",
    intent: extra.intent || "",
    contextNote: extra.contextNote || "",
    analysisSnapshot: extra.analysisSnapshot || null,
    groundedInScope: extra.groundedInScope ?? true,
  };
}

function buildAssistantWelcome(region, selectedArticle, selectedTrend) {
  if (selectedTrend) {
    return `TruthLens Assistant is ready. I can explain why "${selectedTrend.label}" is trending, what signals are driving it, and whether it is spreading faster than verification.`;
  }

  if (selectedArticle) {
    return `TruthLens Assistant is ready. I can summarize "${selectedArticle.title}", explain its credibility score, compare narratives, or tell you what to verify next.`;
  }

  return `TruthLens Assistant is ready for ${regionLabels[region]}. Paste a URL, drop a text claim, or ask about a trend to start a verification conversation.`;
}

function mapAnalysisResult(result) {
  return {
    title: getAnalysisTitle(result.credibility_label),
    score: result.credibility_score,
    label: result.credibility_label,
    finalLabel: result.final_label || result.credibility_label,
    tone: getToneFromLabel(result.credibility_label),
    explanation: result.explanation,
    evidence:
      result.risk_signals && result.risk_signals.length > 0
        ? result.risk_signals
        : ["No major risk signal detected"],
    verificationTips: result.verification_tips || [],
    inputType: result.input_type || "text",
    sourceScore: result.source_score || 0,
    articleScore: result.article_score || 0,
    corroborationScore: result.corroboration_score || 0,
    verificationStatus: result.verification_status || "Awaiting corroboration",
    sourceProfile: result.source_profile || null,
  };
}

function buildActivityFromStats(stats, trendingCount) {
  const total = stats?.total_articles || 0;
  const suspicious = stats?.suspicious_count || 0;
  const reliable = stats?.reliable_count || 0;
  const world = stats?.world_articles || 0;
  const morocco = stats?.morocco_articles || 0;

  return [
    { time: "06:00", checks: Math.max(4, Math.round(total * 0.2)) },
    { time: "09:00", checks: Math.max(6, Math.round(total * 0.35)) },
    { time: "12:00", checks: Math.max(8, Math.round((total + trendingCount) * 0.45)) },
    { time: "15:00", checks: Math.max(6, Math.round((world + morocco) * 0.6)) },
    { time: "18:00", checks: Math.max(5, Math.round((suspicious + reliable + trendingCount) * 0.9)) },
    { time: "21:00", checks: Math.max(4, Math.round((total + suspicious) * 0.4)) },
  ];
}

function ArticleCard({ article, index, onSelect, isSelected }) {
  return (
    <article
      className={clsx("article-card", isSelected && "article-card--selected")}
      style={{ animationDelay: `${index * 90}ms` }}
      onClick={() => onSelect?.(article)}
    >
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
            onClick={(event) => event.stopPropagation()}
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

        {article.priorityTopic ? (
          <div className="tips-row" style={{ marginTop: "-2px" }}>
            <span className="hint-pill">Trend: {article.priorityTopic}</span>
            {article.sourceTrustLevel ? (
              <span className="hint-pill">Trust: {article.sourceTrustLevel}</span>
            ) : null}
          </div>
        ) : null}

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

function SummaryCard({ eyebrow, title, description, value, index, danger = false }) {
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
          {danger ? (
            <span className="status-chip status-chip-danger">Watch</span>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function TrendCard({ trend, index, onSelect, isSelected }) {
  return (
    <article
      className={clsx("side-card", "trend-card", isSelected && "trend-card--selected")}
      style={{ animationDelay: `${index * 80}ms` }}
      onClick={() => onSelect?.(trend)}
    >
      <div className="side-card__header">
        <div>
          <p className="analysis-preview__eyebrow">Trend Intelligence</p>
          <h3>{trend.label}</h3>
        </div>
        <span className={clsx("status-chip", trend.credibilityWarning ? "status-chip-danger" : "status-chip-soft")}>
          {trend.credibilityWarning ? "Early Warning" : trend.freshness}
        </span>
      </div>

      <div className="trend-card__stats">
        <div>
          <span>Virality</span>
          <strong>{Math.round(trend.viralityScore)}</strong>
        </div>
        <div>
          <span>Articles</span>
          <strong>{trend.articleCount}</strong>
        </div>
        <div>
          <span>Gap</span>
          <strong>{Math.round(trend.verificationGapScore)}</strong>
        </div>
      </div>

      <p className="article-card__summary">{trend.confidenceNote}</p>

      <div className="tips-row">
        {trend.platformSignals.map((item) => (
          <span key={`platform-${trend.id}-${item}`} className="hint-pill">
            {item}
          </span>
        ))}
        {trend.sourceSignals.map((item) => (
          <span key={`source-${trend.id}-${item}`} className="hint-pill">
            {item}
          </span>
        ))}
      </div>
    </article>
  );
}

function AssistantPanel({
  region,
  selectedArticle,
  selectedTrend,
  assistantMessages,
  assistantDraft,
  setAssistantDraft,
  assistantLoading,
  assistantError,
  onSend,
  onQuickAction,
  threadRef,
}) {
  const hasMessages = assistantMessages.length > 0;
  const quickActions = assistantMessages.at(-1)?.quickActions?.length
    ? assistantMessages.at(-1).quickActions
    : assistantStarterPrompts;

  return (
    <section className="assistant-shell">
      <div className="assistant-shell__header">
        <div className="section-title">
          <Sparkles size={20} />
          <h3>TruthLens Assistant</h3>
        </div>
        <span className="status-chip status-chip-soft">Copilot</span>
      </div>

      <div className="assistant-shell__context">
        <span className="hint-pill">{regionLabels[region]}</span>
        {selectedArticle ? <span className="hint-pill">Article selected</span> : null}
        {selectedTrend ? <span className="hint-pill">Trend selected</span> : null}
      </div>

      <div className="assistant-thread" ref={threadRef}>
        {!hasMessages ? (
          <div className="assistant-empty">
            <div className="assistant-empty__icon">
              <MessageSquareText size={22} />
            </div>
            <h3>Verification starts here</h3>
            <p>{buildAssistantWelcome(region, selectedArticle, selectedTrend)}</p>

            <div className="tips-row" style={{ marginTop: "0" }}>
              {assistantGuardrails.map((item) => (
                <span key={item} className="hint-pill">
                  {item}
                </span>
              ))}
            </div>

            <div className="assistant-quick-actions assistant-quick-actions--welcome">
              {assistantStarterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="assistant-chip"
                  onClick={() => onQuickAction(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="assistant-thread__messages">
            {assistantMessages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  "assistant-message",
                  message.role === "user" ? "assistant-message--user" : "assistant-message--assistant"
                )}
              >
                <div className="assistant-message__meta">
                  <span>{message.role === "user" ? "You" : "TruthLens Assistant"}</span>
                  {message.model ? <span>{message.model}</span> : null}
                </div>

                <div className="assistant-message__bubble">
                  <p>{message.content}</p>

                  {message.contextNote ? (
                    <p className="hero-card__note">{message.contextNote}</p>
                  ) : null}

                  {message.analysisSnapshot ? (
                    <div className="assistant-analysis-card">
                      <div className="analysis-preview__header">
                        <div>
                          <p className="analysis-preview__eyebrow">Verification snapshot</p>
                          <strong>{message.analysisSnapshot.final_label}</strong>
                        </div>
                        <span className="status-chip status-chip-warning">
                          {message.analysisSnapshot.final_score}%
                        </span>
                      </div>

                      <div className="analysis-metrics">
                        <div className="analysis-metrics__item">
                          <span>Source</span>
                          <strong>{message.analysisSnapshot.source_score}</strong>
                        </div>
                        <div className="analysis-metrics__item">
                          <span>Article</span>
                          <strong>{message.analysisSnapshot.article_score}</strong>
                        </div>
                        <div className="analysis-metrics__item">
                          <span>Corroboration</span>
                          <strong>{message.analysisSnapshot.corroboration_score}</strong>
                        </div>
                      </div>

                      <p className="analysis-subnote">
                        {message.analysisSnapshot.verification_status}
                      </p>

                      {message.analysisSnapshot.source_profile ? (
                        <div className="tips-row">
                          <span className="hint-pill">
                            {message.analysisSnapshot.source_profile.source_name}
                          </span>
                          <span className="hint-pill">
                            {message.analysisSnapshot.source_profile.source_type}
                          </span>
                          <span className="hint-pill">
                            {message.analysisSnapshot.source_profile.risk_tier}
                          </span>
                        </div>
                      ) : null}

                      <p>{message.analysisSnapshot.explanation}</p>
                    </div>
                  ) : null}

                  {message.suggestedChecks?.length ? (
                    <ul className="signal-list">
                      {message.suggestedChecks.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </div>
            ))}

            {assistantLoading ? (
              <div className="assistant-message assistant-message--assistant">
                <div className="assistant-message__meta">
                  <span>TruthLens Assistant</span>
                </div>
                <div className="assistant-message__bubble assistant-message__bubble--loading">
                  <p>Thinking through the verification context...</p>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      <div className="assistant-composer">
        <div className="assistant-quick-actions">
          {quickActions.slice(0, 4).map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="assistant-chip"
              onClick={() => onQuickAction(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>

        {assistantError ? (
          <p className="hero-card__note" style={{ color: "var(--danger)", margin: "6px 0 0" }}>
            {assistantError}
          </p>
        ) : null}

        <div className="assistant-composer__box">
          <textarea
            className="assistant-composer__input"
            rows={4}
            placeholder="Ask a question, paste a URL, drop a claim, or ask why something is trending..."
            value={assistantDraft}
            onChange={(event) => setAssistantDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSend();
              }
            }}
          />

          <button
            type="button"
            className="assistant-send"
            onClick={onSend}
            disabled={assistantLoading}
            aria-label="Send message"
          >
            <SendHorizontal size={18} />
          </button>
        </div>
      </div>
    </section>
  );
}

function ContextPanel({ selectedArticle, selectedTrend, analysisResult, onQuickAction }) {
  return (
    <section className="side-card context-card">
      <div className="side-card__header">
        <div className="section-title">
          <Link2 size={20} />
          <h3>Current Context</h3>
        </div>
      </div>

      {selectedTrend ? (
        <div className="context-block">
          <p className="analysis-preview__eyebrow">Trend focus</p>
          <strong>{selectedTrend.label}</strong>
          <p className="article-card__summary">{selectedTrend.confidenceNote}</p>

          <div className="tips-row">
            <span className="hint-pill">{selectedTrend.region}</span>
            <span className="hint-pill">{selectedTrend.freshness}</span>
            <span className="hint-pill">Gap {Math.round(selectedTrend.verificationGapScore)}</span>
          </div>

          <div className="tips-row">
            {selectedTrend.platformSignals.map((item) => (
              <span key={`context-platform-${item}`} className="hint-pill">
                {item}
              </span>
            ))}
            {selectedTrend.sourceSignals.map((item) => (
              <span key={`context-source-${item}`} className="hint-pill">
                {item}
              </span>
            ))}
          </div>

          <div className="context-actions">
            <button type="button" className="ghost-action" onClick={() => onQuickAction("Explain this trend")}>
              Explain this trend
            </button>
            <button type="button" className="ghost-action" onClick={() => onQuickAction("Compare Morocco vs World narratives")}>
              Compare narratives
            </button>
          </div>
        </div>
      ) : selectedArticle ? (
        <div className="context-block">
          <p className="analysis-preview__eyebrow">Article focus</p>
          <strong>{selectedArticle.title}</strong>
          <p className="article-card__summary">{selectedArticle.summary}</p>

          <div className="tips-row">
            <span className="hint-pill">{selectedArticle.source}</span>
            <span className="hint-pill">{selectedArticle.badge}</span>
            <span className="hint-pill">{selectedArticle.score}%</span>
          </div>

          <div className="context-actions">
            <button type="button" className="ghost-action" onClick={() => onQuickAction("Summarize this article")}>
              Summarize
            </button>
            <button type="button" className="ghost-action" onClick={() => onQuickAction("Why is this suspicious?")}>
              Explain score
            </button>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <CheckCircle2 size={28} />
          <div>
            <h3>No context selected</h3>
            <p>Select an article or a trend to give the assistant stronger context.</p>
          </div>
        </div>
      )}

      <div className="analysis-preview" style={{ "--analysis-accent": resultStyles[analysisResult.tone]?.accent || "var(--warning-strong)" }}>
        <div className="analysis-preview__header">
          <div>
            <p className="analysis-preview__eyebrow">Latest verification snapshot</p>
            <strong>{analysisResult.finalLabel}</strong>
          </div>
          <span className={(resultStyles[analysisResult.tone] || resultStyles.watch).chipClass}>
            {analysisResult.score > 0 ? formatPercent(analysisResult.score) : "--"}
          </span>
        </div>

        <div className="analysis-metrics">
          <div className="analysis-metrics__item">
            <span>Source</span>
            <strong>{analysisResult.sourceScore || "--"}</strong>
          </div>
          <div className="analysis-metrics__item">
            <span>Article</span>
            <strong>{analysisResult.articleScore || "--"}</strong>
          </div>
          <div className="analysis-metrics__item">
            <span>Corroboration</span>
            <strong>{analysisResult.corroborationScore || "--"}</strong>
          </div>
        </div>

        <p className="analysis-subnote">{analysisResult.verificationStatus}</p>

        {analysisResult.sourceProfile ? (
          <div className="tips-row">
            <span className="hint-pill">{analysisResult.sourceProfile.source_name}</span>
            <span className="hint-pill">{analysisResult.sourceProfile.source_type}</span>
            <span className="hint-pill">{analysisResult.sourceProfile.risk_tier}</span>
            <span className="hint-pill">
              base {analysisResult.sourceProfile.base_reliability_score}
            </span>
          </div>
        ) : null}

        <p>{analysisResult.explanation}</p>

        {analysisResult.evidence?.length ? (
          <ul className="signal-list">
            {analysisResult.evidence.slice(0, 4).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}

        {analysisResult.verificationTips?.length ? (
          <div className="tips-row">
            {analysisResult.verificationTips.slice(0, 3).map((item) => (
              <span key={item} className="hint-pill">
                {item}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export function DashboardPage() {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [activeRegion, setActiveRegion] = useState("morocco");
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [chartReady, setChartReady] = useState(false);
  const [assistantDraft, setAssistantDraft] = useState("");
  const [assistantMessages, setAssistantMessages] = useState([]);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState("");
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [selectedTrend, setSelectedTrend] = useState(null);
  const assistantThreadRef = useRef(null);

  const [articles, setArticles] = useState([]);
  const [articleCategories, setArticleCategories] = useState(["All"]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState("");

  const [trendingTopics, setTrendingTopics] = useState([]);
  const [trendingLoading, setTrendingLoading] = useState(false);

  const [overviewStats, setOverviewStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const [analysisResult, setAnalysisResult] = useState(buildEmptyAnalysis());

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

  useEffect(() => {
    async function loadTrending() {
      try {
        setTrendingLoading(true);
        const data = await fetchTrending(getApiRegion(activeRegion));
        setTrendingTopics(data.map(mapTrendingTopic));
      } catch (error) {
        console.error("Failed to load trending:", error);
        setTrendingTopics([]);
      } finally {
        setTrendingLoading(false);
      }
    }

    loadTrending();
  }, [activeRegion]);

  useEffect(() => {
    async function loadStats() {
      try {
        setStatsLoading(true);
        const data = await fetchOverviewStats();
        setOverviewStats(data);
      } catch (error) {
        console.error("Failed to load stats:", error);
        setOverviewStats(null);
      } finally {
        setStatsLoading(false);
      }
    }

    loadStats();
  }, [articles.length]);

  async function sendAssistantMessage(forcedMessage = "") {
    const message = (forcedMessage || assistantDraft).trim();
    if (!message) {
      return;
    }

    const history = assistantMessages.slice(-6).map((item) => ({
      role: item.role,
      content: item.content,
    }));

    const userMessage = buildConversationMessage("user", message);

    setAssistantMessages((prev) => [...prev, userMessage]);
    setAssistantDraft("");

    try {
      setAssistantLoading(true);
      setAssistantError("");

      const result = await chatWithAssistant({
        message,
        history,
        article_title: selectedArticle?.title,
        article_summary: selectedArticle?.summary,
        article_score: selectedArticle?.score,
        article_label: selectedArticle?.badge,
        article_url: selectedArticle?.url,
        article_source: selectedArticle?.source,
        article_region: selectedArticle?.region,
        risk_signals: analysisResult?.evidence || [],
        selected_trend_title: selectedTrend?.label,
        selected_trend_region: selectedTrend?.region,
        selected_trend_freshness: selectedTrend?.freshness,
        selected_trend_confidence_note: selectedTrend?.confidenceNote,
        selected_trend_source_signals: selectedTrend?.sourceSignals || [],
        selected_trend_platform_signals: selectedTrend?.platformSignals || [],
        selected_trend_related_articles_count: selectedTrend?.articleCount,
        selected_trend_verification_gap_score: selectedTrend?.verificationGapScore,
        region_focus: regionLabels[activeRegion],
        active_view: activeNav,
        morocco_trends: trendingTopics
          .filter((topic) => topic.region === "morocco")
          .slice(0, 6)
          .map((topic) => topic.label),
        world_trends: trendingTopics
          .filter((topic) => topic.region === "world")
          .slice(0, 6)
          .map((topic) => topic.label),
      });

      const assistantMessage = buildConversationMessage("assistant", result.answer, {
        suggestedChecks: result.suggested_checks,
        quickActions: result.quick_actions,
        model: result.model,
        intent: result.intent,
        contextNote: result.context_note,
        analysisSnapshot: result.analysis_snapshot,
        groundedInScope: result.grounded_in_scope,
      });

      setAssistantMessages((prev) => [...prev, assistantMessage]);

      if (result.analysis_snapshot) {
        setAnalysisResult(
          mapAnalysisResult({
            credibility_score: result.analysis_snapshot.credibility_score,
            credibility_label: result.analysis_snapshot.credibility_label,
            source_score: result.analysis_snapshot.source_score,
            article_score: result.analysis_snapshot.article_score,
            corroboration_score: result.analysis_snapshot.corroboration_score,
            final_score: result.analysis_snapshot.final_score,
            final_label: result.analysis_snapshot.final_label,
            verification_status: result.analysis_snapshot.verification_status,
            explanation: result.analysis_snapshot.explanation,
            risk_signals: result.analysis_snapshot.risk_signals,
            verification_tips: result.analysis_snapshot.verification_tips,
            input_type: result.analysis_snapshot.input_type,
            source_profile: result.analysis_snapshot.source_profile,
          })
        );
      }

      pushNotification("Assistant ready", "TruthLens Assistant returned a guided response.", "info");
    } catch (error) {
      console.error("Assistant request failed:", error);
      setAssistantError("The assistant could not answer right now.");

      setAssistantMessages((prev) => [
        ...prev,
        buildConversationMessage(
          "assistant",
          "TruthLens Assistant is temporarily unavailable. Retry in a moment or select an article or trend for stronger context.",
          {
            suggestedChecks: [
              "Retry the request in a moment.",
              "Select an article and ask why it is suspicious.",
              "Open Trending and ask for a trend explanation.",
            ],
            model: "unavailable",
            intent: "error",
            contextNote: "Assistant request failed.",
          }
        ),
      ]);

      pushNotification("Assistant unavailable", "The assistant request failed.", "danger");
    } finally {
      setAssistantLoading(false);
    }
  }

  function handleQuickAction(prompt) {
    if (prompt === "Analyze this URL") {
      if (selectedArticle?.url) {
        sendAssistantMessage(`Analyze this URL: ${selectedArticle.url}`);
      } else {
        setAssistantDraft("Analyze this URL: ");
      }
      return;
    }

    if (prompt === "Check this claim") {
      if (selectedArticle?.title) {
        sendAssistantMessage(`Check this claim: ${selectedArticle.title}`);
      } else {
        setAssistantDraft("Check this claim: ");
      }
      return;
    }

    if (prompt === "Summarize this article" && selectedArticle?.title) {
      sendAssistantMessage("Summarize this article.");
      return;
    }

    if (prompt === "Why is this suspicious?" && selectedArticle?.title) {
      sendAssistantMessage("Why is this suspicious?");
      return;
    }

    if (prompt === "Explain this trend" && selectedTrend?.label) {
      sendAssistantMessage("Explain this trend.");
      return;
    }

    if (prompt === "What should I verify next?" && selectedTrend?.label) {
      sendAssistantMessage("What should I verify next?");
      return;
    }

    if (prompt === "Compare Morocco vs World narratives") {
      sendAssistantMessage("Compare Morocco vs World narratives.");
      return;
    }

    setAssistantDraft(prompt);
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

  const visibleTrending = trendingTopics.filter((topic) => topic.region === activeRegion);

  useEffect(() => {
    if (visibleArticles.length === 0) {
      setSelectedArticle(null);
      return;
    }

    if (!selectedArticle || !visibleArticles.some((article) => article.id === selectedArticle.id)) {
      setSelectedArticle(visibleArticles[0]);
    }
  }, [visibleArticles, selectedArticle]);

  useEffect(() => {
    if (visibleTrending.length === 0) {
      setSelectedTrend(null);
      return;
    }

    if (!selectedTrend || !visibleTrending.some((trend) => trend.id === selectedTrend.id)) {
      setSelectedTrend(visibleTrending[0]);
    }
  }, [visibleTrending, selectedTrend]);

  useEffect(() => {
    if (assistantThreadRef.current) {
      assistantThreadRef.current.scrollTop = assistantThreadRef.current.scrollHeight;
    }
  }, [assistantMessages, assistantLoading]);

  const categorySummary = useMemo(() => {
    return articleCategories
      .filter((cat) => cat !== "All")
      .map((cat) => ({
        label: cat,
        value: articles.filter(
          (article) => article.category === cat && article.region === activeRegion
        ).length,
      }))
      .filter((item) => item.value > 0);
  }, [articleCategories, articles, activeRegion]);

  const activity = useMemo(
    () => buildActivityFromStats(overviewStats, visibleTrending.length),
    [overviewStats, visibleTrending.length]
  );

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
          region={activeRegion}
          selectedArticle={selectedArticle}
          selectedTrend={selectedTrend}
          assistantMessages={assistantMessages}
          assistantDraft={assistantDraft}
          setAssistantDraft={setAssistantDraft}
          assistantLoading={assistantLoading}
          assistantError={assistantError}
          onSend={() => sendAssistantMessage()}
          onQuickAction={handleQuickAction}
          threadRef={assistantThreadRef}
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
                  Suivi live des actualites Maroc et Monde avec badges de credibilite,
                  trend intelligence hybride et assistant de verification integre.
                </p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  Backend live data
                </span>
                <span className="hero-card__note">
                  {overviewStats?.last_refresh_batch
                    ? `Last refresh: ${overviewStats.last_refresh_batch}`
                    : "Backend FastAPI + SQLite + JWT connecte"}
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
                  <ArticleCard
                    key={article.id}
                    article={article}
                    index={index}
                    onSelect={(item) => {
                      setSelectedArticle(item);
                      setSelectedTrend(null);
                    }}
                    isSelected={selectedArticle?.id === article.id}
                  />
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
              {trendingLoading ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>Loading trends...</h3>
                    <p>Les tendances sont en cours de chargement depuis le backend.</p>
                  </div>
                </div>
              ) : visibleTrending.length > 0 ? (
                visibleTrending.map((topic, index) => (
                  <TrendCard
                    key={topic.id}
                    index={index}
                    trend={topic}
                    onSelect={(item) => {
                      setSelectedTrend(item);
                      setSelectedArticle(null);
                    }}
                    isSelected={selectedTrend?.id === topic.id}
                  />
                ))
              ) : (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>No trending topics</h3>
                    <p>Aucune tendance n'est disponible pour cette region pour le moment.</p>
                  </div>
                </div>
              )}
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
              {categorySummary.length > 0 ? (
                categorySummary.map((item, index) => (
                  <SummaryCard
                    key={item.label}
                    eyebrow="Category"
                    title={item.label}
                    description="Nombre d'articles actuellement disponibles dans cette categorie."
                    value={item.value}
                    index={index}
                  />
                ))
              ) : (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>No category data</h3>
                    <p>Aucune categorie exploitable pour la region selectionnee.</p>
                  </div>
                </div>
              )}
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
                  <strong>{statsLoading ? "..." : overviewStats?.total_articles ?? 0}</strong>
                  <span>articles currently loaded</span>
                </div>
                <div>
                  <strong>{statsLoading ? "..." : overviewStats?.suspicious_count ?? 0}</strong>
                  <span>stories flagged for review</span>
                </div>
              </div>

              <div className="activity-summary" style={{ marginTop: "14px" }}>
                <div>
                  <strong>{statsLoading ? "..." : overviewStats?.morocco_articles ?? 0}</strong>
                  <span>Morocco articles</span>
                </div>
                <div>
                  <strong>{statsLoading ? "..." : overviewStats?.world_articles ?? 0}</strong>
                  <span>World articles</span>
                </div>
              </div>
            </section>
          </>
        )}
      </section>

      <aside className="insight-panel">
        <ContextPanel
          selectedArticle={selectedArticle}
          selectedTrend={selectedTrend}
          analysisResult={analysisResult}
          onQuickAction={handleQuickAction}
        />

        <section className="side-card">
          <div className="side-card__header">
            <div className="section-title">
              <Activity size={20} />
              <h3>Trend Intelligence</h3>
            </div>
          </div>

          <div className="topic-list">
            {visibleTrending.length > 0 ? (
              visibleTrending.slice(0, 6).map((topic) => (
                <button
                  key={topic.id}
                  type="button"
                  className={clsx("topic-row", selectedTrend?.id === topic.id && "topic-row--selected")}
                  onClick={() => {
                    setSelectedTrend(topic);
                    setSelectedArticle(null);
                  }}
                >
                  <div className="topic-row__content">
                    <span>{topic.label}</span>
                    <small>
                      {topic.articleCount} related article(s) - {topic.freshness}
                    </small>
                  </div>
                  <strong>{Math.round(topic.viralityScore)}</strong>
                </button>
              ))
            ) : (
              <div className="topic-row">
                <div className="topic-row__content">
                  <span>No live trends</span>
                  <small>TruthLens has no strong trend cluster for this region yet.</small>
                </div>
                <strong>--</strong>
              </div>
            )}
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
              <strong>{overviewStats?.total_articles ?? articles.length}</strong>
              <span>checks analysed today</span>
            </div>
            <div>
              <strong>{overviewStats?.suspicious_count ?? 0}</strong>
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
