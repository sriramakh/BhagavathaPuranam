import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bhagavatha Puranam Studio",
  description: "Character memory and episode planning studio for Bhagavatham animated storybooks.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
