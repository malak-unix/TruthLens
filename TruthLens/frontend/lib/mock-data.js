import {
  BarChart3,
  Grid2x2,
  LayoutDashboard,
  TrendingUp,
} from "lucide-react";

export const navigationItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "trending", label: "Trending", icon: TrendingUp },
  { id: "categories", label: "Categories", icon: Grid2x2 },
  { id: "statistics", label: "Statistics", icon: BarChart3 },
];

export const factCheckTips = [
  "URL officiel",
  "Titre viral",
  "Post social",
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
