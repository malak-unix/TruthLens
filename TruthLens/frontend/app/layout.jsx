import "./globals.css";

export const metadata = {
  title: "TruthLens",
  description: "TruthLens dashboard for monitoring news, trends, and explainable credibility analysis.",
};

export default function RootLayout({ children }) {
  const preferenceScript = `
    (function () {
      try {
        var storedTheme = localStorage.getItem("truthlens_theme");
        var storedLanguage = localStorage.getItem("truthlens_language");
        var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        var theme = storedTheme === "dark" || storedTheme === "light" ? storedTheme : (prefersDark ? "dark" : "light");
        var language = storedLanguage === "ar" ? "ar" : "fr";
        var direction = language === "ar" ? "rtl" : "ltr";
        document.documentElement.setAttribute("data-theme", theme);
        document.documentElement.setAttribute("lang", language);
        document.documentElement.setAttribute("dir", direction);
      } catch (error) {}
    })();
  `;

  return (
    <html lang="fr" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <script dangerouslySetInnerHTML={{ __html: preferenceScript }} />
        {children}
      </body>
    </html>
  );
}
