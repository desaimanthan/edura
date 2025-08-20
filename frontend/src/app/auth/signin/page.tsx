"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"
import Link from "next/link"
import { useAuth } from "@/components/providers/auth-provider"
import { CheckCircle, Brain, Eye, EyeOff, ArrowLeft, Quote } from "lucide-react"

export default function SignIn() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login, getGoogleAuthUrl } = useAuth()

  // Check for error messages from URL params
  const error = searchParams.get('error')
  if (error && !isLoading) {
    if (error === 'oauth_failed') {
      toast.error("Google sign-in failed")
    } else if (error === 'invalid_callback') {
      toast.error("Invalid authentication callback")
    } else if (error === 'callback_failed') {
      toast.error("Authentication callback failed")
    }
  }

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await login(email, password)
      toast.success("Signed in successfully!")
      router.push("/dashboard")
    } catch (error: any) {
      toast.error(error.message || "Invalid credentials")
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setIsLoading(true)
    try {
      // Get the Google auth URL from backend and redirect
      const authUrl = await getGoogleAuthUrl()
      window.location.href = authUrl
    } catch (error) {
      toast.error("Google sign-in failed")
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 text-white flex-col justify-between p-12 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 to-transparent"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl transform translate-x-32 -translate-y-32"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/5 rounded-full blur-3xl transform -translate-x-32 translate-y-32"></div>
        
        <div className="relative z-10">
          {/* Logo */}
          <Link href="/" className="flex items-center mb-16">
            <img src="/Edura_club_w.svg" alt="Edura" className="h-14 w-auto cursor-pointer" />
          </Link>

          {/* Main Content */}
          <div className="max-w-lg">
            <h1 className="text-4xl font-black mb-6 leading-tight">
              Welcome back to the future of teaching
            </h1>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              Continue creating amazing courses with AI that understands pedagogy.
            </p>
            
            {/* Feature Highlights */}
            <div className="space-y-4">
              {[
                "50% faster course creation",
                "Always up-to-date content",
                "Personalized for every student"
              ].map((feature, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-white/90">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Testimonial */}
        <div className="relative z-10">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <Quote className="w-8 h-8 text-white/60 mb-4" />
            <p className="text-white/90 mb-4 leading-relaxed">
              "Edura has completely transformed how I create courses. What used to take weeks now takes days."
            </p>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-teal-400 to-emerald-400 rounded-full flex items-center justify-center">
                <span className="font-semibold text-emerald-900 text-sm">SM</span>
              </div>
              <div>
                <p className="font-semibold text-white">Dr. Sarah Mitchell</p>
                <p className="text-white/60 text-sm">Professor, MIT</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Back Button */}
          <Button 
            variant="ghost" 
            onClick={() => router.push("/")}
            className="mb-8 text-gray-600 hover:text-gray-900 -ml-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to home
          </Button>

          {/* Mobile Logo */}
          <Link href="/" className="lg:hidden flex items-center justify-center mb-8">
            <img src="/Edura_club.svg" alt="Edura" className="h-14 w-auto cursor-pointer" />
          </Link>

          <Card className="border-0 shadow-none bg-transparent">
            <CardHeader className="text-center pb-8 px-0">
              <CardTitle className="text-3xl font-black text-gray-900 mb-2">Sign in</CardTitle>
              <CardDescription className="text-gray-600">
                Enter your credentials to access your account
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6 px-0">
              {/* Google Sign In */}
              <Button 
                variant="outline" 
                className="w-full h-14 border-gray-300 hover:bg-gray-50 text-base"
                onClick={handleGoogleSignIn}
                disabled={isLoading}
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <Separator className="w-full" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-gray-50 px-3 text-gray-500">Or</span>
                </div>
              </div>

              {/* Login Form */}
              <form onSubmit={handleEmailSignIn} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    className="h-14 text-base bg-white border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
                    <Button variant="link" className="text-sm text-emerald-600 hover:text-emerald-700 p-0 h-auto">
                      Forgot password?
                    </Button>
                  </div>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                      className="h-14 pr-12 text-base bg-white border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="remember" className="rounded border-gray-300" />
                  <Label htmlFor="remember" className="text-sm text-gray-600">Remember me for 30 days</Label>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-base font-semibold"
                  disabled={isLoading}
                >
                  {isLoading ? "Signing in..." : "Sign in"}
                </Button>
              </form>

              <div className="text-center pt-4">
                <span className="text-gray-600">Don't have an account? </span>
                <Link href="/auth/signup" className="text-emerald-600 hover:text-emerald-700 font-semibold">
                  Sign up for free
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
