import "./globals.css";

export const metadata = {
  title: "TruthLens",
  description: "Tableau de bord TruthLens pour la surveillance et la verification de l'actualite.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
