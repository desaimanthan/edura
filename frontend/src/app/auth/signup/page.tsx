"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"
import Link from "next/link"
import { useAuth } from "@/components/providers/auth-provider"
import { CheckCircle, Eye, EyeOff, ArrowLeft, Star } from "lucide-react"

export default function SignUp() {
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { register, login, getGoogleAuthUrl } = useAuth()

  const handleEmailSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters")
      return
    }

    setIsLoading(true)

    try {
      const fullName = `${firstName} ${lastName}`.trim()
      await register(fullName, email, password)
      toast.success("Account created successfully!")
      
      // Automatically sign in after successful registration
      try {
        await login(email, password)
        router.push("/dashboard")
      } catch {
        toast.error("Registration successful, but sign-in failed. Please try signing in manually.")
        router.push("/auth/signin")
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Something went wrong"
      toast.error(errorMessage)
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
              Join 10,000+ educators transforming education
            </h1>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              Start creating personalized, AI-powered courses that adapt to every student&apos;s needs.
            </p>
            
            {/* Stats */}
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                <div className="text-2xl font-black text-white">50%</div>
                <div className="text-white/70 text-sm">Faster Creation</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                <div className="text-2xl font-black text-white">95%</div>
                <div className="text-white/70 text-sm">Satisfaction</div>
              </div>
            </div>

            {/* Features */}
            <div className="space-y-3">
              {[
                "AI-powered curriculum generation",
                "Personalized learning paths",
                "Real-time content updates",
                "Smart assessment tools"
              ].map((feature, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-5 h-5 bg-white/20 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-white/90 text-sm">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Badge */}
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 border border-white/30">
            <Star className="w-4 h-4 text-white" />
            <span className="text-white text-sm font-medium">Trusted by top universities</span>
          </div>
        </div>
      </div>

      {/* Right Panel - Signup Form */}
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
              <CardTitle className="text-3xl font-black text-gray-900 mb-2">Create your account</CardTitle>
              <CardDescription className="text-gray-600">
                Start your 14-day free trial. No credit card required.
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6 px-0">
              {/* Google Sign Up */}
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

              {/* Signup Form */}
              <form onSubmit={handleEmailSignUp} className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName" className="text-sm font-medium text-gray-700">First name</Label>
                    <Input
                      id="firstName"
                      placeholder="John"
                      className="h-12 text-base bg-white border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName" className="text-sm font-medium text-gray-700">Last name</Label>
                    <Input
                      id="lastName"
                      placeholder="Doe"
                      className="h-12 text-base bg-white border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">Work email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="john@university.edu"
                    className="h-12 text-base bg-white border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Create a strong password"
                      className="h-12 pr-12 text-base bg-white border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
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
                  <p className="text-xs text-gray-500">Must be at least 8 characters</p>
                </div>

                <div className="flex items-start space-x-2 pt-2">
                  <input type="checkbox" id="terms" className="mt-1 rounded border-gray-300" required />
                  <Label htmlFor="terms" className="text-xs text-gray-600 leading-relaxed">
                    I agree to the <a href="#" className="text-emerald-600 hover:text-emerald-700 underline">Terms of Service</a> and <a href="#" className="text-emerald-600 hover:text-emerald-700 underline">Privacy Policy</a>
                  </Label>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-base font-semibold"
                  disabled={isLoading}
                >
                  {isLoading ? "Creating account..." : "Create account"}
                </Button>
              </form>

              <div className="text-center pt-4">
                <span className="text-gray-600">Already have an account? </span>
                <Link href="/auth/signin" className="text-emerald-600 hover:text-emerald-700 font-semibold">
                  Sign in
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
