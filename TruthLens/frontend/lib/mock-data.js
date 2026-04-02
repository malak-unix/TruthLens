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

export const articleCategories = [
  "All",
  "Politics",
  "Economy",
  "Society",
  "Health",
  "Technology",
  "Sports",
  "International",
];

export const articles = [
  {
    id: "ma-1",
    region: "morocco",
    category: "Economy",
    title: "New Economic Policy Announced: Major Changes to Tax System",
    source: "Le Matin",
    timeAgo: "2 hours ago",
    summary:
      "Verified by official government sources and confirmed by multiple independent journalists covering fiscal reform.",
    score: 85,
    badge: "Reliable",
    badgeClass: "status-chip-success",
    scoreColor: "#1d9c55",
    image:
      "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: "ma-2",
    region: "morocco",
    category: "Health",
    title: "Healthcare Reform Bill Passes Parliament with Unanimous Support",
    source: "Morocco Today",
    timeAgo: "5 hours ago",
    summary:
      "Confirmed by official parliamentary records and cross-verified with multiple local outlets tracking the vote.",
    score: 79,
    badge: "Needs Context",
    badgeClass: "status-chip-warning",
    scoreColor: "#d99119",
    image:
      "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: "ma-3",
    region: "morocco",
    category: "Technology",
    title: "National Digital Identity Upgrade Opens New Access for Public Services",
    source: "MAP",
    timeAgo: "7 hours ago",
    summary:
      "Announcement aligns with the ministry roadmap, but implementation details are still being clarified by regional agencies.",
    score: 74,
    badge: "Likely Reliable",
    badgeClass: "status-chip-success",
    scoreColor: "#1d9c55",
    image:
      "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: "world-1",
    region: "world",
    category: "International",
    title: "Regional Climate Coalition Announces New Cross-Border Water Pact",
    source: "The Guardian",
    timeAgo: "1 hour ago",
    summary:
      "Initial details are strong, but regional agencies are still releasing the full text and implementation timeline.",
    score: 82,
    badge: "Reliable",
    badgeClass: "status-chip-success",
    scoreColor: "#1d9c55",
    image:
      "https://images.unsplash.com/photo-1569163139394-de4e4f43e4e5?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: "world-2",
    region: "world",
    category: "Technology",
    title: "AI Policy Draft Sparks Debate Over Safety, Bias and Open Models",
    source: "Reuters",
    timeAgo: "3 hours ago",
    summary:
      "Broadly corroborated by major outlets, although several clauses remain under negotiation and may still change.",
    score: 77,
    badge: "Needs Context",
    badgeClass: "status-chip-warning",
    scoreColor: "#d99119",
    image:
      "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: "world-3",
    region: "world",
    category: "Society",
    title: "Viral Social Post Claims Sudden Education Rule Change Across Europe",
    source: "Signal Monitor",
    timeAgo: "4 hours ago",
    summary:
      "The claim is circulating quickly but official policy references are incomplete, making this an item to review closely.",
    score: 44,
    badge: "Needs Review",
    badgeClass: "status-chip-danger",
    scoreColor: "#e3262e",
    image:
      "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=900&q=80",
  },
];

export const topicStats = {
  morocco: [
    { label: "Economic Policy", value: 234 },
    { label: "Health Reform", value: 189 },
    { label: "Climate Action", value: 156 },
    { label: "Tech Regulation", value: 142 },
  ],
  world: [
    { label: "AI Safety", value: 264 },
    { label: "Water Security", value: 201 },
    { label: "Election Integrity", value: 188 },
    { label: "Platform Moderation", value: 167 },
  ],
};

export const activitySeries = {
  morocco: [
    { time: "06:00", checks: 18 },
    { time: "09:00", checks: 34 },
    { time: "12:00", checks: 52 },
    { time: "15:00", checks: 45 },
    { time: "18:00", checks: 61 },
    { time: "21:00", checks: 40 },
  ],
  world: [
    { time: "06:00", checks: 24 },
    { time: "09:00", checks: 48 },
    { time: "12:00", checks: 66 },
    { time: "15:00", checks: 72 },
    { time: "18:00", checks: 81 },
    { time: "21:00", checks: 57 },
  ],
};

export const factCheckTips = [
  "URL officiel",
  "Titre viral",
  "Post social",
];
