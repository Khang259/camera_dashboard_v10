import type React from "react"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Header } from "@/components/header"
import { AppBackground } from "@/components/app-background"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "ISS",
  description: "Monitor your cameras in real-time",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className}`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          <AppBackground>
            <div className="flex min-h-screen flex-col">
              <Header />
              <main className="flex-1 overflow-auto p-4 container mx-auto">{children}</main>
            </div>
          </AppBackground>
        </ThemeProvider>
      </body>
    </html>
  )
}
