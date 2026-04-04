"use client";

import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import {
  Activity,
  AlertTriangle,
  Bell,
  Bot,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Languages,
  Moon,
  Search,
  SendHorizontal,
  Sparkles,
  Sun,
  UserRound,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";

import { navigationItems } from "../lib/mock-data";
import {
  getDirection,
  getTranslator,
  translateCategory,
  translateCredibilityLabel,
  translateTrustLevel,
  translateVerificationStatus,
} from "../lib/i18n";

import {
  fetchNews,
  fetchHistoricalNews,
  fetchCategories,
  fetchTrending,
  fetchOverviewStats,
  chatWithAssistant,
  registerUser,
  loginUser,
  fetchCurrentUser,
} from "../lib/api";

const THEME_STORAGE_KEY = "truthlens_theme";
const LANGUAGE_STORAGE_KEY = "truthlens_language";

function getStoredTheme() {
  if (typeof window === "undefined") return "light";

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "dark" || stored === "light") {
    return stored;
  }

  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function getStoredLanguage() {
  if (typeof window === "undefined") return "fr";
  return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === "ar" ? "ar" : "fr";
}

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

function getAnalysisTitle(label, t) {
  if (label === "Reliable") return t("analysis.sourceBaselineStrong");
  if (label === "Needs Context") return t("analysis.moreContextRequired");
  if (label === "Unverified") return t("analysis.earlySignal");
  if (label === "Suspicious") return t("analysis.suspicious");
  if (label === "High Risk") return t("analysis.highRisk");
  if (label === "No Input") return t("analysis.ready");
  return t("analysis.analysisComplete");
}

function formatTimeAgo(publishedAt, t) {
  const published = new Date(publishedAt);
  const now = new Date();
  const diffMs = now - published;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffHours > 0) return `${diffHours} ${t("article.hoursAgo")}`;
  if (diffMinutes > 0) return `${diffMinutes} ${t("article.minutesAgo")}`;
  return t("article.justNow");
}

function formatDateTime(value, language, t) {
  if (!value) return t("statuses.notAvailable");

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(language === "ar" ? "ar-MA" : "fr-MA", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
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
    publishedAt: article.published_at,
    summary: article.description,
    score: article.credibility_score,
    badge: article.credibility_label,
    badgeClass: getBadgeClass(article.credibility_label),
    scoreColor: getScoreColor(article.credibility_score),
    image: article.image_url || getCategoryImage(article.category),
    url: article.url,
    region: article.country === "ma" ? "morocco" : "world",
    explanation: article.explanation,
    fetchedAt: article.fetched_at || "",
    analyzedAt: article.analyzed_at || "",
    batchLabel: article.batch_label,
    sourceType: article.source_type,
    sourceTrustLevel: article.source_trust_level,
    priorityTopic: article.priority_topic || "",
    rankingScore: article.ranking_score || 0,
    sourceScore: article.source_score ?? null,
    articleScore: article.article_score ?? null,
    corroborationScore: article.corroboration_score ?? null,
    verificationStatus: article.verification_status || "",
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
    platform: topic.platform || "news",
    mediaType: topic.media_type || "text",
    thumbnailUrl: topic.thumbnail_url || "",
    sourceUrl: topic.source_url || "",
    viralityScore: topic.virality_score || topic.intensity,
    verificationGapScore: topic.verification_gap_score || 0,
    verificationStatus: topic.verification_status || "unverified",
    confidenceNote: topic.confidence_note || "",
    recencyScore: topic.recency_score || 0,
  };
}

function buildEmptyAnalysis(t) {
  return {
    title: t("analysis.ready"),
    score: 0,
    label: "No Input",
    tone: "watch",
    explanation:
      "Paste a URL or a text claim. This panel is connected to the FastAPI /analyze endpoint.",
    evidence: [t("analysis.noContentProvided"), t("analysis.waitingInput")],
    sourceScore: 0,
    articleScore: 0,
    corroborationScore: 0,
    verificationStatus: "No verification yet",
    sourceProfile: null,
    finalLabel: "No Input",
  };
}

function buildConversationMessage(role, content, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random()}`,
    role,
    content,
    timestamp:
      extra.timestamp ||
      new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    suggestedChecks: extra.suggestedChecks || [],
    quickActions: extra.quickActions || [],
    model: extra.model || "",
    intent: extra.intent || "",
    contextNote: extra.contextNote || "",
    analysisSnapshot: extra.analysisSnapshot || null,
    groundedInScope: extra.groundedInScope ?? true,
  };
}

function buildAssistantWelcome(t, region, selectedArticle, selectedTrend) {
  if (selectedTrend) {
    return t("assistant.welcomeTrend");
  }

  if (selectedArticle) {
    return t("assistant.welcomeArticle");
  }

  return t("assistant.welcomeDefault");
}

function mapAnalysisResult(result, t) {
  return {
    title: getAnalysisTitle(result.credibility_label, t),
    score: result.credibility_score,
    label: result.credibility_label,
    finalLabel: result.final_label || result.credibility_label,
    tone: getToneFromLabel(result.credibility_label),
    explanation: result.explanation,
    evidence:
      result.risk_signals && result.risk_signals.length > 0
        ? result.risk_signals
        : [t("analysis.noRiskSignal")],
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

function normalizeText(value = "") {
  return value
    .toLowerCase()
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/[^\p{L}\p{N}\s-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractKeywords(value = "") {
  return normalizeText(value)
    .split(" ")
    .filter((token) => token.length >= 4)
    .slice(0, 8);
}

function includesKeywordSet(text, keywords) {
  if (!text || keywords.length === 0) return false;
  const normalized = normalizeText(text);
  return keywords.some((keyword) => normalized.includes(keyword));
}

function findRelatedArticles({ selectedArticle, selectedTrend, articles, historicalArticles }) {
  const seed =
    selectedArticle?.title ||
    selectedArticle?.priorityTopic ||
    selectedTrend?.normalizedTopic ||
    selectedTrend?.label ||
    "";

  const keywords = extractKeywords(seed);
  const pool = [...articles, ...historicalArticles];
  const seen = new Set();

  return pool.filter((item) => {
    if (seen.has(item.id)) return false;
    const matches =
      (selectedArticle && item.id === selectedArticle.id) ||
      includesKeywordSet(item.title, keywords) ||
      includesKeywordSet(item.summary, keywords) ||
      includesKeywordSet(item.priorityTopic, keywords);

    if (matches) {
      seen.add(item.id);
    }

    return matches;
  });
}

function buildConfidenceCardData({ selectedArticle, analysisResult, t, language }) {
  const fallbackScore = analysisResult?.score || 0;
  const fallbackLabel = analysisResult?.finalLabel || analysisResult?.label || "Unverified";
  const label = selectedArticle?.badge || fallbackLabel;
  const score = selectedArticle?.score ?? fallbackScore;
  const sourceScore = selectedArticle?.sourceScore ?? analysisResult?.sourceScore ?? 0;
  const articleScore = selectedArticle?.articleScore ?? analysisResult?.articleScore ?? 0;
  const corroborationScore =
    selectedArticle?.corroborationScore ?? analysisResult?.corroborationScore ?? 0;
  const verificationStatus =
    selectedArticle?.verificationStatus || analysisResult?.verificationStatus || "No verification yet";

  let level = translateCredibilityLabel(label, language);
  if (score >= 85) level = translateCredibilityLabel("Reliable", language);
  else if (score >= 65) level = translateCredibilityLabel("Needs Context", language);
  else if (score >= 45) level = translateCredibilityLabel("Unverified", language);
  else level = translateCredibilityLabel("Suspicious", language);

  const topSignals = [
    `${t("article.source")}: ${sourceScore || "--"}/100`,
    `${t("article.articleQuality")}: ${articleScore || "--"}/100`,
    `${t("article.corroboration")}: ${corroborationScore || "--"}/100`,
  ];

  if (selectedArticle?.sourceTrustLevel) {
    topSignals.push(
      `${t("article.trust")}: ${translateTrustLevel(selectedArticle.sourceTrustLevel, language)}`
    );
  }

  let nextAction = t("assistant.quickVerify");
  if (verificationStatus.toLowerCase().includes("awaiting") || verificationStatus.toLowerCase().includes("non")) {
    nextAction = t("assistant.quickCompare");
  } else if (score < 50) {
    nextAction = t("assistant.quickRisk");
  } else if (selectedArticle?.url) {
    nextAction = t("assistant.quickExplain");
  }

  return {
    score,
    level,
    verificationStatus: translateVerificationStatus(verificationStatus, language),
    topSignals: topSignals.slice(0, 4),
    nextAction,
  };
}

function buildNarrativeComparisonData({
  selectedArticle,
  selectedTrend,
  relatedArticles,
  t,
  language,
}) {
  const reliableCoverage = relatedArticles
    .filter(
      (item) =>
        item.badge === "Reliable" ||
        item.badge === "Needs Context" ||
        item.sourceTrustLevel === "high" ||
        item.sourceTrustLevel === "medium"
    )
    .slice(0, 2);

  const uncertainCoverage = relatedArticles
    .filter(
      (item) =>
        item.badge === "Unverified" ||
        item.badge === "Suspicious" ||
        item.badge === "High Risk" ||
        (item.verificationStatus || "").toLowerCase().includes("awaiting")
    )
    .slice(0, 2);

  const newest = [...relatedArticles]
    .sort((left, right) => new Date(right.publishedAt) - new Date(left.publishedAt))[0];
  const oldest = [...relatedArticles]
    .sort((left, right) => new Date(left.publishedAt) - new Date(right.publishedAt))[0];

  return {
    sharedNarrative:
      selectedArticle?.title ||
      selectedTrend?.label ||
      t("dashboard.noResultsMessage"),
    reliableReporting:
      reliableCoverage.length > 0
        ? reliableCoverage.map((item) => `${item.source}: ${item.title}`)
        : [t("analysis.moreContextRequired")],
    stillUnverified:
      uncertainCoverage.length > 0
        ? uncertainCoverage.map(
            (item) =>
              `${item.source}: ${translateVerificationStatus(item.verificationStatus || "unverified", language)}`
          )
        : [translateVerificationStatus("supported by stronger sources", language)],
    changedOverTime:
      oldest && newest && oldest.id !== newest.id
        ? `${formatDateTime(oldest.publishedAt, language, t)} -> ${formatDateTime(newest.publishedAt, language, t)}`
        : t("dashboard.verifiedFirst"),
  };
}

function buildTimelineData({ selectedArticle, relatedArticles, language, t }) {
  const coverage = selectedArticle ? [selectedArticle, ...relatedArticles] : relatedArticles;
  const sorted = [...coverage]
    .filter((item) => item.publishedAt)
    .sort((left, right) => new Date(left.publishedAt) - new Date(right.publishedAt));

  const first = sorted[0];
  const midpoint = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length / 2))];
  const verified =
    coverage.find((item) => item.analyzedAt || item.verificationStatus) || selectedArticle || first;

  return [
    {
      label: t("dashboard.firstAppearance"),
      time: first ? formatDateTime(first.publishedAt, language, t) : t("statuses.notAvailable"),
      detail: first?.source || t("statuses.notAvailable"),
    },
    {
      label: t("dashboard.acceleration"),
      time: midpoint ? formatDateTime(midpoint.fetchedAt || midpoint.publishedAt, language, t) : t("statuses.notAvailable"),
      detail: midpoint ? `${coverage.length} ${t("trending.articles").toLowerCase()}` : t("statuses.notAvailable"),
    },
    {
      label: t("dashboard.verificationMoment"),
      time: verified ? formatDateTime(verified.analyzedAt || verified.fetchedAt || verified.publishedAt, language, t) : t("statuses.notAvailable"),
      detail: verified?.verificationStatus
        ? translateVerificationStatus(verified.verificationStatus, language)
        : t("statuses.notAvailable"),
    },
  ];
}

function getTrendSampleHeadlines(trend, articles, historicalArticles) {
  const related = findRelatedArticles({
    selectedArticle: null,
    selectedTrend: trend,
    articles,
    historicalArticles,
  });

  return [...new Set(related.map((item) => item.title))].slice(0, 2);
}

function isCrisisSignal(selectedArticle, selectedTrend) {
  const seed = normalizeText(
    [
      selectedArticle?.title,
      selectedArticle?.summary,
      selectedArticle?.priorityTopic,
      selectedTrend?.label,
      selectedTrend?.normalizedTopic,
    ]
      .filter(Boolean)
      .join(" ")
  );

  const crisisKeywords = [
    "war",
    "conflict",
    "strike",
    "ceasefire",
    "invasion",
    "crisis",
    "guerre",
    "conflit",
    "greve",
    "cessez-le-feu",
    "crise",
    "seisme",
    "espace aerien",
    "alerte sanitaire",
    "earthquake",
    "airspace",
    "internet",
    "health alert",
    "outage",
    "military",
    "escalation",
  ];

  return (
    Boolean(selectedArticle?.isConflict) ||
    Boolean(selectedTrend?.credibilityWarning) ||
    crisisKeywords.some((keyword) => seed.includes(keyword))
  );
}

function WhyNowCard({ t, checksToday }) {
  return (
    <section className="insight-card insight-card--accent">
      <p className="insight-card__eyebrow">{t("dashboard.whyNowKicker")}</p>
      <h3>{t("dashboard.whyNowLead")}</h3>
      <p>{t("dashboard.whyNowCalm")}</p>
      <div className="insight-card__stat">
        <strong>{checksToday}</strong>
        <span>{t("dashboard.claimsCheckedToday")}</span>
      </div>
    </section>
  );
}

function ConfidenceCard({ t, data }) {
  return (
    <section className="insight-card">
      <div className="insight-card__header">
        <div>
          <p className="insight-card__eyebrow">{t("dashboard.confidenceCard")}</p>
          <h3>{formatPercent(data.score)}</h3>
        </div>
        <span className="status-chip status-chip-soft">{data.level}</span>
      </div>

      <div className="insight-card__list">
        <div>
          <strong>{t("dashboard.confidenceLevel")}</strong>
          <span>{data.verificationStatus}</span>
        </div>
        <div>
          <strong>{t("dashboard.topSignals")}</strong>
          <ul>
            {data.topSignals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>{t("dashboard.nextBestAction")}</strong>
          <span>{data.nextAction}</span>
        </div>
      </div>
    </section>
  );
}

function NarrativeCard({ t, comparison }) {
  return (
    <section className="insight-card">
      <p className="insight-card__eyebrow">{t("dashboard.compareNarrative")}</p>
      <div className="insight-block">
        <strong>{t("dashboard.sharedNarrative")}</strong>
        <p>{comparison.sharedNarrative}</p>
      </div>
      <div className="insight-block">
        <strong>{t("dashboard.reliableReporting")}</strong>
        <ul>
          {comparison.reliableReporting.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div className="insight-block">
        <strong>{t("dashboard.stillUnverified")}</strong>
        <ul>
          {comparison.stillUnverified.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div className="insight-block">
        <strong>{t("dashboard.changedOverTime")}</strong>
        <p>{comparison.changedOverTime}</p>
      </div>
    </section>
  );
}

function TimelineCard({ t, timeline }) {
  return (
    <section className="insight-card">
      <p className="insight-card__eyebrow">{t("dashboard.claimTimeline")}</p>
      <div className="timeline-list">
        {timeline.map((item) => (
          <div key={item.label} className="timeline-step">
            <div className="timeline-step__dot" />
            <div>
              <strong>{item.label}</strong>
              <p>{item.time}</p>
              <span>{item.detail}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CrisisBanner({ t }) {
  return (
    <section className="crisis-banner">
      <div className="crisis-banner__icon">
        <AlertTriangle size={20} />
      </div>
      <div>
        <p className="insight-card__eyebrow">{t("dashboard.crisisMode")}</p>
        <h3>{t("dashboard.crisisSubtitle")}</h3>
        <div className="tips-row">
          <span className="hint-pill">{t("dashboard.verifiedFirst")}</span>
          <span className="hint-pill">{t("dashboard.unconfirmed")}</span>
        </div>
      </div>
    </section>
  );
}

function ArticleCard({ article, index, onSelect, isSelected, t, language }) {
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
            <p className="article-card__eyebrow">{translateCategory(article.category, language)}</p>
            <h3>{article.title}</h3>
          </div>

          <a
            className="ghost-icon-button"
            aria-label={t("actions.openArticle")}
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
            {formatTimeAgo(article.publishedAt, t)}
          </span>
        </div>

        <p className="article-card__summary">{article.summary}</p>

        {article.priorityTopic ? (
          <div className="tips-row" style={{ marginTop: "-2px" }}>
            <span className="hint-pill">
              {t("article.trend")}: {article.priorityTopic}
            </span>
            {article.sourceTrustLevel ? (
              <span className="hint-pill">
                {t("article.trust")}: {translateTrustLevel(article.sourceTrustLevel, language)}
              </span>
            ) : null}
          </div>
        ) : null}

        <div className="article-card__footer">
          <div className="credibility-block">
            <span>{t("article.credibility")}:</span>
            <strong style={{ color: article.scoreColor }}>
              {formatPercent(article.score)}
            </strong>
          </div>
          <span className={clsx("status-chip", article.badgeClass)}>
            {translateCredibilityLabel(article.badge, language)}
          </span>
        </div>
      </div>
    </article>
  );
}

function SummaryCard({ eyebrow, title, description, value, index, danger = false, t }) {
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
            <span>{t("categories.value")}:</span>
            <strong>{value}</strong>
          </div>
          {danger ? (
            <span className="status-chip status-chip-danger">{t("categories.watch")}</span>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function TrendCard({ trend, index, onSelect, isSelected, t, language }) {
  return (
    <article
      className={clsx("side-card", "trend-card", isSelected && "trend-card--selected")}
      style={{ animationDelay: `${index * 80}ms` }}
      onClick={() => onSelect?.(trend)}
    >
      {trend.thumbnailUrl ? (
        <div
          className="trend-card__thumb"
          style={{ backgroundImage: `url('${trend.thumbnailUrl}')` }}
        />
      ) : null}

      <div className="side-card__header">
        <div>
          <p className="analysis-preview__eyebrow">{t("trending.intelligence")}</p>
          <h3>{trend.label}</h3>
        </div>
        <span className={clsx("status-chip", trend.credibilityWarning ? "status-chip-danger" : "status-chip-soft")}>
          {trend.credibilityWarning ? t("trending.earlyWarning") : t(`statuses.${trend.freshness}`)}
        </span>
      </div>

      <div className="trend-card__stats">
        <div>
          <span>{t("trending.virality")}</span>
          <strong>{Math.round(trend.viralityScore)}</strong>
        </div>
        <div>
          <span>{t("trending.articles")}</span>
          <strong>{trend.articleCount}</strong>
        </div>
        <div>
          <span>{t("trending.gap")}</span>
          <strong>{Math.round(trend.verificationGapScore)}</strong>
        </div>
      </div>

      <p className="article-card__summary">{trend.confidenceNote}</p>

      <div className="insight-block insight-block--compact">
        <strong>{t("trending.whyItTrends")}</strong>
        <p>{trend.whyItTrends}</p>
      </div>

      {trend.sampleHeadlines?.length ? (
        <div className="insight-block insight-block--compact">
          <strong>{t("trending.sampleHeadlines")}</strong>
          <ul>
            {trend.sampleHeadlines.map((headline) => (
              <li key={headline}>{headline}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="analysis-subnote">{translateVerificationStatus(trend.verificationStatus, language)}</p>

      <div className="tips-row">
        <span className="hint-pill">
          {t("trending.riskLevel")}: {trend.credibilityWarning ? t("trending.earlyWarning") : translateVerificationStatus(trend.verificationStatus, language)}
        </span>
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
  t,
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
  language,
}) {
  const hasMessages = assistantMessages.length > 0;

  return (
    <section className="assistant-shell">
      <div className="assistant-shell__header">
        <div className="assistant-shell__identity">
          <div className="assistant-shell__agent-mark">
            <Bot size={22} />
          </div>
          <div>
            <h3>{t("assistant.title")}</h3>
            <p>{t("assistant.online")}</p>
          </div>
        </div>
      </div>

      <div className="assistant-thread" ref={threadRef}>
        <div className="assistant-thread__messages">
          <div className="copilot-actions">
            <button type="button" className="copilot-action" onClick={() => onQuickAction(t("assistant.quickExplain"))}>
              {t("assistant.quickExplain")}
            </button>
            <button type="button" className="copilot-action" onClick={() => onQuickAction(t("assistant.quickVerify"))}>
              {t("assistant.quickVerify")}
            </button>
            <button type="button" className="copilot-action" onClick={() => onQuickAction(t("assistant.quickCompare"))}>
              {t("assistant.quickCompare")}
            </button>
            <button type="button" className="copilot-action" onClick={() => onQuickAction(t("assistant.quickRisk"))}>
              {t("assistant.quickRisk")}
            </button>
          </div>

          {!hasMessages ? (
            <div className="assistant-message assistant-message--assistant">
              <div className="assistant-message__avatar">
                <Bot size={14} />
              </div>
              <div className="assistant-message__content">
                <div className="assistant-message__bubble">
                  <p>{buildAssistantWelcome(t, region, selectedArticle, selectedTrend)}</p>
                </div>
                <span className="assistant-message__time">
                  {new Date().toLocaleTimeString(language === "ar" ? "ar-MA" : "fr-MA", { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          ) : null}

          {hasMessages ? assistantMessages.map((message) => (
            <div
              key={message.id}
              className={clsx(
                "assistant-message",
                message.role === "user" ? "assistant-message--user" : "assistant-message--assistant"
              )}
            >
              {message.role !== "user" ? (
                <div className="assistant-message__avatar">
                  <Bot size={14} />
                </div>
              ) : null}

              <div className="assistant-message__content">
                <div className="assistant-message__bubble">
                  <p>{message.content}</p>
                </div>

                <span className="assistant-message__time">{message.timestamp}</span>
              </div>
            </div>
          )) : null}

          {assistantLoading ? (
            <div className="assistant-message assistant-message--assistant">
              <div className="assistant-message__avatar">
                <Bot size={14} />
              </div>
              <div className="assistant-message__content">
                <div className="assistant-message__bubble assistant-message__bubble--loading">
                  <p>{t("assistant.loading")}</p>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="assistant-composer">
        {assistantError ? (
          <p className="hero-card__note" style={{ color: "var(--danger)", margin: "6px 0 0" }}>
            {assistantError}
          </p>
        ) : null}

        <div className="assistant-composer__box">
          <textarea
            className="assistant-composer__input"
            rows={1}
            placeholder={t("assistant.placeholder")}
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
            aria-label={t("actions.send")}
          >
            <SendHorizontal size={18} />
          </button>
        </div>
      </div>
    </section>
  );
}

function HistoricalArticleCard({ article, index, onSelect, isSelected, t, language }) {
  return (
    <article
      className={clsx("article-card", "historical-card", isSelected && "article-card--selected")}
      style={{ animationDelay: `${index * 80}ms` }}
      onClick={() => onSelect?.(article)}
    >
      <div
        className="article-card__media"
        style={{ backgroundImage: `url('${article.image}')` }}
      />

      <div className="article-card__content">
        <div className="article-card__header">
          <div>
            <p className="article-card__eyebrow">{t("history.storedAnalysis")}</p>
            <h3>{article.title}</h3>
          </div>

          <a
            className="ghost-icon-button"
            aria-label={t("actions.openArticle")}
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
          <span>{translateCategory(article.category, language)}</span>
          <span className="meta-separator">|</span>
          <span>{article.region === "morocco" ? t("regions.morocco") : t("regions.world")}</span>
        </div>

        <p className="article-card__summary">{article.summary}</p>

        <div className="analysis-preview historical-card__analysis">
          <div className="analysis-preview__header">
            <div>
              <p className="analysis-preview__eyebrow">{t("history.savedCredibility")}</p>
              <strong>{translateCredibilityLabel(article.badge, language)}</strong>
            </div>
            <span className={clsx("status-chip", article.badgeClass)}>{formatPercent(article.score)}</span>
          </div>

          <div className="analysis-metrics">
            <div className="analysis-metrics__item">
              <span>{t("article.source")}</span>
              <strong>{article.sourceScore ?? "--"}</strong>
            </div>
            <div className="analysis-metrics__item">
              <span>{t("article.articleQuality")}</span>
              <strong>{article.articleScore ?? "--"}</strong>
            </div>
            <div className="analysis-metrics__item">
              <span>{t("article.corroboration")}</span>
              <strong>{article.corroborationScore ?? "--"}</strong>
            </div>
          </div>

          <p>{article.explanation}</p>
          <p className="analysis-subnote">
            {article.verificationStatus
              ? translateVerificationStatus(article.verificationStatus, language)
              : t("history.verificationUnavailable")}
          </p>
        </div>

        <div className="historical-card__timeline">
          <span>{t("history.published")}: {formatDateTime(article.publishedAt, language, t)}</span>
          <span>{t("history.stored")}: {formatDateTime(article.fetchedAt, language, t)}</span>
          <span>{t("history.analyzed")}: {formatDateTime(article.analyzedAt, language, t)}</span>
        </div>
      </div>
    </article>
  );
}

export function DashboardPage() {
  const [theme, setTheme] = useState(getStoredTheme);
  const [language, setLanguage] = useState(getStoredLanguage);
  const [mobileAssistantOpen, setMobileAssistantOpen] = useState(false);
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
  const [historicalArticles, setHistoricalArticles] = useState([]);
  const [articleCategories, setArticleCategories] = useState(["All"]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState("");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  const [trendingTopics, setTrendingTopics] = useState([]);
  const [trendingLoading, setTrendingLoading] = useState(false);

  const [overviewStats, setOverviewStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const [analysisResult, setAnalysisResult] = useState(buildEmptyAnalysis(getTranslator(getStoredLanguage())));

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
  const t = useMemo(() => getTranslator(language), [language]);
  const direction = useMemo(() => getDirection(language), [language]);
  const regionLabels = useMemo(
    () => ({
      morocco: t("regions.morocco"),
      world: t("regions.world"),
    }),
    [t]
  );

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
    pushNotification(t("auth.logoutTitle"), t("auth.logoutMessage"), "info");
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
        t("auth.registerSuccessTitle"),
        t("auth.registerSuccessMessage", { user: data.user.full_name || data.user.email }),
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
        t("auth.loginSuccessTitle"),
        t("auth.loginSuccessMessage", { user: data.user.full_name || data.user.email }),
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
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("lang", language);
    root.setAttribute("dir", direction);
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [language, direction]);

  useEffect(() => {
    const mediaQuery = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mediaQuery || window.localStorage.getItem(THEME_STORAGE_KEY)) {
      return undefined;
    }

    const updateTheme = (event) => setTheme(event.matches ? "dark" : "light");
    mediaQuery.addEventListener?.("change", updateTheme);
    return () => mediaQuery.removeEventListener?.("change", updateTheme);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const handleResize = () => {
      if (window.innerWidth > 940) {
        setMobileAssistantOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (assistantMessages.length === 0) {
      setAssistantMessages([
        buildConversationMessage(
          "assistant",
          t("assistant.welcomeDefault")
        ),
      ]);
    }
  }, [assistantMessages.length, t]);

  useEffect(() => {
    setAnalysisResult(buildEmptyAnalysis(t));
  }, [t]);

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
          t("dashboard.newsUpdatedTitle"),
          t("dashboard.newsUpdatedMessage", {
            count: mapped.length,
            region: regionLabels[activeRegion],
          }),
          "info"
        );
      } catch (error) {
        console.error("Failed to load news:", error);
        setNewsError(language === "ar" ? "تعذر تحميل موجز الاخبار." : "Impossible de charger le flux d'actualites.");
      } finally {
        setNewsLoading(false);
      }
    }

    loadNews();
  }, [activeRegion, activeCategory, language, t, regionLabels]);

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
    async function loadHistoricalNews() {
      try {
        setHistoryLoading(true);
        setHistoryError("");

        const data = await fetchHistoricalNews({
          country: getApiCountry(activeRegion),
          category: activeCategory === "All" ? "" : activeCategory,
          search: deferredSearch,
          limit: 80,
        });

        setHistoricalArticles(data.map(mapBackendArticle));
      } catch (error) {
        console.error("Failed to load historical news:", error);
        setHistoricalArticles([]);
        setHistoryError(language === "ar" ? "تعذر تحميل الاخبار التاريخية." : "Impossible de charger les actualites historiques.");
      } finally {
        setHistoryLoading(false);
      }
    }

    loadHistoricalNews();
  }, [activeRegion, activeCategory, deferredSearch, language]);

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
        ui_language: language,
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
          }, t)
        );
      }

      pushNotification(t("assistant.readyNotificationTitle"), t("assistant.readyNotificationMessage"), "info");
    } catch (error) {
      console.error("Assistant request failed:", error);
      setAssistantError(t("assistant.unavailable"));

      setAssistantMessages((prev) => [
        ...prev,
        buildConversationMessage(
          "assistant",
          t("assistant.unavailableReply"),
          {
            model: "unavailable",
            intent: "error",
          }
        ),
      ]);

      pushNotification(t("assistant.failedNotificationTitle"), t("assistant.failedNotificationMessage"), "danger");
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
    () =>
      buildActivityFromStats(
        overviewStats,
        trendingTopics.filter((topic) => topic.region === activeRegion).length
      ),
    [overviewStats, trendingTopics, activeRegion]
  );

  const relatedArticles = useMemo(
    () =>
      findRelatedArticles({
        selectedArticle,
        selectedTrend,
        articles: articles.filter(
          (article) =>
            article.region === activeRegion &&
            (activeCategory === "All" || article.category === activeCategory)
        ),
        historicalArticles,
      }),
    [selectedArticle, selectedTrend, articles, historicalArticles, activeRegion, activeCategory]
  );

  const confidenceCard = useMemo(
    () =>
      buildConfidenceCardData({
        selectedArticle,
        analysisResult,
        t,
        language,
      }),
    [selectedArticle, analysisResult, t, language]
  );

  const narrativeComparison = useMemo(
    () =>
      buildNarrativeComparisonData({
        selectedArticle,
        selectedTrend,
        relatedArticles,
        t,
        language,
      }),
    [selectedArticle, selectedTrend, relatedArticles, t, language]
  );

  const timelineData = useMemo(
    () => buildTimelineData({ selectedArticle, relatedArticles, language, t }),
    [selectedArticle, relatedArticles, language, t]
  );

  const crisisModeActive = useMemo(
    () => isCrisisSignal(selectedArticle, selectedTrend),
    [selectedArticle, selectedTrend]
  );

  const enrichedTrending = useMemo(
    () =>
      trendingTopics
        .filter((trend) => trend.region === activeRegion)
        .map((trend) => ({
        ...trend,
        whyItTrends: t("trending.trendReason"),
        sampleHeadlines: getTrendSampleHeadlines(trend, articles, historicalArticles),
      })),
    [trendingTopics, activeRegion, t, articles, historicalArticles]
  );

  const displayFocus = activeCategory === "All" ? t("dashboard.allCategories") : translateCategory(activeCategory, language);

  return (
    <main className="dashboard-shell" data-rtl={direction === "rtl"}>
      {mobileAssistantOpen ? (
        <button
          type="button"
          className="assistant-mobile-backdrop"
          aria-label={t("actions.closeAssistant")}
          onClick={() => setMobileAssistantOpen(false)}
        />
      ) : null}

      <aside className={clsx("assistant-sidebar", mobileAssistantOpen && "assistant-sidebar--mobile-open")}>
        <div className="brand-mark">
          <div className="brand-mark__logo">
            <img src="/truthlens-logo.png" alt="TruthLens logo" className="brand-mark__logo-image" />
          </div>
          <div>
            <h1>TruthLens</h1>
            <p>{t("app.monitoringStudio")}</p>
          </div>
        </div>

        <AssistantPanel
          t={t}
          region={activeRegion}
          selectedArticle={selectedArticle}
          selectedTrend={selectedTrend}
          assistantMessages={assistantMessages}
          assistantDraft={assistantDraft}
          setAssistantDraft={setAssistantDraft}
          assistantLoading={assistantLoading}
          assistantError={assistantError}
          onSend={() => sendAssistantMessage()}
          onQuickAction={(prompt) => sendAssistantMessage(prompt)}
          threadRef={assistantThreadRef}
          language={language}
        />

        <div className="sidebar-footer">
          <p>{t("app.version")}</p>
          <span>{currentUser ? t("app.signedIn") : t("app.assistantReady")}</span>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <label className="search-field">
            <Search size={22} />
            <input
              type="search"
              placeholder={t("topbar.searchPlaceholder")}
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
            />
          </label>

          <div className="topbar-actions">
            <button
              className="ghost-icon-button"
              aria-label={t("actions.changeTheme")}
              onClick={() => setTheme((prev) => (prev === "dark" ? "light" : "dark"))}
              title={`${t("actions.changeTheme")}: ${theme === "dark" ? t("theme.dark") : t("theme.light")}`}
            >
              {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            <div className="language-switch" role="group" aria-label={t("language.switcher")}>
              <button
                type="button"
                className={clsx("language-switch__button", language === "fr" && "is-active")}
                onClick={() => setLanguage("fr")}
              >
                <Languages size={16} />
                <span>{t("language.fr")}</span>
              </button>
              <button
                type="button"
                className={clsx("language-switch__button", language === "ar" && "is-active")}
                onClick={() => setLanguage("ar")}
              >
                <span>{t("language.ar")}</span>
              </button>
            </div>

            <button
              className="ghost-icon-button"
              aria-label={t("topbar.notifications")}
              onClick={openNotifications}
            >
              <Bell size={20} />
              {unreadCount > 0 && <span className="topbar-dot" />}
            </button>

            <button
              className="ghost-icon-button"
              aria-label={t("topbar.profile")}
              onClick={openProfilePanel}
            >
              <UserRound size={20} />
            </button>
          </div>
        </header>

        <button
          type="button"
          className="assistant-mobile-toggle"
          onClick={() => setMobileAssistantOpen(true)}
        >
          <Bot size={18} />
          <span>{t("assistant.title")}</span>
        </button>

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
                <span>{t(`nav.${item.id}`)}</span>
              </button>
            );
          })}
        </nav>

        {activeNav === "dashboard" && (
          <>
            <section className="hero-card">
              <div>
                <p className="hero-card__kicker">{t("dashboard.kicker")}</p>
                <h2>{t("dashboard.title")}</h2>
                <p className="hero-card__subtitle">{t("dashboard.subtitle")}</p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  {t("dashboard.liveData")}
                </span>
                <span className="hero-card__note">
                  {overviewStats?.last_refresh_batch
                    ? t("dashboard.lastRefresh", { batch: overviewStats.last_refresh_batch })
                    : t("dashboard.backendConnected")}
                </span>
              </div>
            </section>

            <div className="insight-grid insight-grid--top">
              <WhyNowCard t={t} checksToday={overviewStats?.checks_today ?? 0} />
              <ConfidenceCard t={t} data={confidenceCard} />
            </div>

            {crisisModeActive ? <CrisisBanner t={t} /> : null}

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
                  {translateCategory(category, language)}
                </button>
              ))}
            </div>

            <div className="results-caption">
              <span>{t("dashboard.resultsCount", { count: visibleArticles.length, region: regionLabels[activeRegion] })}</span>
              <span>{t("dashboard.focus", { value: displayFocus })}</span>
            </div>

            <div className="insight-grid insight-grid--secondary">
              <NarrativeCard t={t} comparison={narrativeComparison} />
              <TimelineCard t={t} timeline={timelineData} />
            </div>

            <div className="news-list">
              {newsLoading ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>{t("dashboard.loadingTitle")}</h3>
                    <p>{t("dashboard.loadingMessage")}</p>
                  </div>
                </div>
              ) : newsError ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>{t("dashboard.errorTitle")}</h3>
                    <p>{newsError}</p>
                  </div>
                </div>
              ) : visibleArticles.length > 0 ? (
                visibleArticles.map((article, index) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    index={index}
                    t={t}
                    language={language}
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
                    <h3>{t("dashboard.noResultsTitle")}</h3>
                    <p>{t("dashboard.noResultsMessage")}</p>
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
                <p className="hero-card__kicker">{t("trending.kicker")}</p>
                <h2>{t("trending.title")}</h2>
                <p className="hero-card__subtitle">
                  {t("trending.subtitle", { region: regionLabels[activeRegion] })}
                </p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  {t("trending.liveSnapshot")}
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
                    <h3>{t("trending.loadingTitle")}</h3>
                    <p>{t("trending.loadingMessage")}</p>
                  </div>
                </div>
              ) : enrichedTrending.length > 0 ? (
                enrichedTrending.map((topic, index) => (
                  <TrendCard
                    key={topic.id}
                    index={index}
                    trend={topic}
                    t={t}
                    language={language}
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
                    <h3>{t("trending.emptyTitle")}</h3>
                    <p>{t("trending.emptyMessage")}</p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {activeNav === "history" && (
          <>
            <section className="hero-card">
              <div>
                <p className="hero-card__kicker">{t("history.kicker")}</p>
                <h2>{t("history.title")}</h2>
                <p className="hero-card__subtitle">{t("history.subtitle")}</p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  {t("history.storedFeed")}
                </span>
                <span className="hero-card__note">
                  {t("history.archivedCount", { count: historicalArticles.length, region: regionLabels[activeRegion] })}
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

              <div className="category-row" role="tablist" aria-label="Historical categories">
                {articleCategories.map((category) => (
                  <button
                    key={`history-${category}`}
                    type="button"
                    className={clsx(
                      "category-pill",
                      activeCategory === category && "is-active"
                    )}
                  onClick={() => setActiveCategory(category)}
                >
                  {translateCategory(category, language)}
                </button>
              ))}
            </div>
          </div>

          <div className="content-toolbar" style={{ marginTop: "0" }}>
              <span>{t("history.searchScope", { value: deferredSearch ? `"${deferredSearch}"` : t("history.allStoredCoverage") })}</span>
              <span>{t("dashboard.focus", { value: displayFocus })}</span>
            </div>

            <div className="news-list">
              {historyLoading ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>{t("history.loadingTitle")}</h3>
                    <p>{t("history.loadingMessage")}</p>
                  </div>
                </div>
              ) : historyError ? (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>{t("history.errorTitle")}</h3>
                    <p>{historyError}</p>
                  </div>
                </div>
              ) : historicalArticles.length > 0 ? (
                historicalArticles.map((article, index) => (
                  <HistoricalArticleCard
                    key={`history-${article.id}`}
                    article={article}
                    index={index}
                    t={t}
                    language={language}
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
                    <h3>{t("history.emptyTitle")}</h3>
                    <p>{t("history.emptyMessage")}</p>
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
                <p className="hero-card__kicker">{t("categories.kicker")}</p>
                <h2>{t("categories.title")}</h2>
                <p className="hero-card__subtitle">{t("categories.subtitle")}</p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  {t("categories.snapshot")}
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
                    eyebrow={t("categories.category")}
                    title={translateCategory(item.label, language)}
                    description={t("categories.description")}
                    value={item.value}
                    index={index}
                    t={t}
                  />
                ))
              ) : (
                <div className="empty-state">
                  <CheckCircle2 size={28} />
                  <div>
                    <h3>{t("categories.noDataTitle")}</h3>
                    <p>{t("categories.noDataMessage")}</p>
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
                <p className="hero-card__kicker">{t("statistics.kicker")}</p>
                <h2>{t("statistics.title")}</h2>
                <p className="hero-card__subtitle">{t("statistics.subtitle")}</p>
              </div>

              <div className="hero-card__status">
                <span className="status-chip status-chip-soft">
                  <Sparkles size={14} />
                  {t("statistics.sqliteMetrics")}
                </span>
              </div>
            </section>

            <section className="side-card activity-card" style={{ marginTop: "1rem" }}>
              <div className="side-card__header">
                <div className="section-title">
                  <Activity size={20} />
                  <h3>{t("statistics.todayActivity")}</h3>
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
                  <span>{t("statistics.articlesLoaded")}</span>
                </div>
                <div>
                  <strong>{statsLoading ? "..." : overviewStats?.suspicious_count ?? 0}</strong>
                  <span>{t("statistics.storiesFlagged")}</span>
                </div>
              </div>

              <div className="activity-summary" style={{ marginTop: "14px" }}>
                <div>
                  <strong>{statsLoading ? "..." : overviewStats?.morocco_articles ?? 0}</strong>
                  <span>{t("statistics.moroccoArticles")}</span>
                </div>
                <div>
                  <strong>{statsLoading ? "..." : overviewStats?.world_articles ?? 0}</strong>
                  <span>{t("statistics.worldArticles")}</span>
                </div>
              </div>
            </section>
          </>
        )}
      </section>

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
              right: direction === "rtl" ? "auto" : "32px",
              left: direction === "rtl" ? "32px" : "auto",
              width: "340px",
              background: "var(--panel-strong)",
              border: "1px solid var(--border)",
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
              <strong>{t("notifications.title")}</strong>
              <button
                onClick={() => setNotifications([])}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--muted)",
                  fontWeight: 600,
                }}
              >
                {t("actions.clear")}
              </button>
            </div>

            {notifications.length === 0 ? (
              <p style={{ color: "var(--muted)", fontSize: "14px", margin: 0 }}>
                {t("notifications.empty")}
              </p>
            ) : (
              <div style={{ display: "grid", gap: "10px", maxHeight: "320px", overflowY: "auto" }}>
                {notifications.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: "12px",
                      borderRadius: "14px",
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <strong style={{ display: "block", marginBottom: "4px" }}>{item.title}</strong>
                    <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "14px" }}>{item.message}</p>
                    <span style={{ fontSize: "12px", color: "var(--muted)" }}>{item.createdAt}</span>
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
              background: "var(--panel-strong)",
              border: "1px solid var(--border)",
              borderRadius: "24px",
              boxShadow: "0 28px 60px rgba(15, 23, 42, 0.18)",
              padding: "20px",
              zIndex: 9999,
            }}
          >
            {currentUser ? (
              <div style={{ display: "grid", gap: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong>{t("auth.connectedUser")}</strong>
                  <button
                    onClick={closeOverlays}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "18px",
                      color: "var(--muted)",
                    }}
                  >
                    <X size={16} />
                  </button>
                </div>

                <div style={{ color: "var(--text-soft)", display: "grid", gap: "6px" }}>
                  <div><strong>{t("auth.email")}:</strong> {currentUser.email}</div>
                  <div><strong>{t("auth.name")}:</strong> {currentUser.full_name || t("auth.notProvided")}</div>
                </div>

                <button
                  className="primary-button"
                  type="button"
                  onClick={logoutUser}
                >
                  {t("actions.logout")}
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
                      {t("actions.login")}
                    </button>
                    <button
                      type="button"
                      className={clsx("fact-check-switch__button", authMode === "register" && "is-active")}
                      onClick={() => {
                        setAuthMode("register");
                        setAuthError("");
                      }}
                    >
                      {t("actions.signup")}
                    </button>
                  </div>

                  <button
                    onClick={closeOverlays}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "18px",
                      color: "var(--muted)",
                    }}
                  >
                    <X size={16} />
                  </button>
                </div>

                {authMode === "register" && (
                  <input
                    type="text"
                    placeholder={t("auth.fullNamePlaceholder")}
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    className="fact-check-input"
                    style={{ minHeight: "52px" }}
                  />
                )}

                <input
                  type="email"
                  placeholder={t("auth.emailPlaceholder")}
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  className="fact-check-input"
                  style={{ minHeight: "52px" }}
                />

                <input
                  type="password"
                  placeholder={t("auth.passwordPlaceholder")}
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
                    ? t("auth.pleaseWait")
                    : authMode === "login"
                    ? t("actions.login")
                    : t("actions.signup")}
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </main>
  );
}
