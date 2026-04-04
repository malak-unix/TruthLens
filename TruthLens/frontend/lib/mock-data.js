import {
  BarChart3,
  Grid2x2,
  History,
  LayoutDashboard,
  TrendingUp,
} from "lucide-react";

export const navigationItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "trending", label: "Trending", icon: TrendingUp },
  { id: "history", label: "Historical News", icon: History },
  { id: "categories", label: "Categories", icon: Grid2x2 },
  { id: "statistics", label: "Statistics", icon: BarChart3 },
];

export const factCheckTips = [
  "Official URL",
  "Viral headline",
  "Social post",
];

export const assistantStarterPrompts = [
  "Analyze this URL",
  "Check this claim",
  "Why is this suspicious?",
  "Summarize this article",
  "Explain this trend",
  "What should I verify next?",
  "Compare Morocco vs World narratives",
];
