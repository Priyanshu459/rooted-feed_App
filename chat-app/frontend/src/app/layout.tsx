import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Earthly Chat',
  description: 'A beautiful, real-time chatting site with earthly aesthetics.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
