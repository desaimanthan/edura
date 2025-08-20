"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ImageWithFallback } from "@/components/figma/ImageWithFallback"
import Link from "next/link"
import { CheckCircle, Clock, Users, BookOpen, Zap, TrendingUp, ArrowRight, Star, Sparkles, Brain, Target, Rocket, Award, Globe, Play } from "lucide-react"
import { useAuth } from "@/components/providers/auth-provider"

export default function Home() {
  const { user, loading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (loading) return // Still loading
    if (isAuthenticated) router.push("/dashboard") // Already authenticated
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null // Will redirect to dashboard
  }

  return (
    <div className="min-h-screen overflow-x-hidden">
      {/* Navigation */}
      <nav className="relative z-50 bg-white border-b border-gray-100">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="flex items-center">
              <img src="/Edura_club.svg" alt="Edura" className="h-12 w-auto cursor-pointer" />
            </Link>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Features</a>
              <a href="#benefits" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Benefits</a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Pricing</a>
              <Link href="/auth/signin">
                <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">Sign In</Button>
              </Link>
              <Link href="/auth/signup">
                <Button size="sm" className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-white py-16 lg:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="lg:pr-8">
              <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-4 py-2 mb-6">
                <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                <span className="text-emerald-700 font-medium text-sm">Reduce Course Creation Time by 50%</span>
              </div>
              
              <h1 className="text-4xl lg:text-5xl xl:text-6xl font-black mb-6 leading-tight text-gray-900">
                AI Copilot for
                <br />
                <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                  Modern Instructors
                </span>
              </h1>
              
              <p className="text-lg lg:text-xl text-gray-600 mb-8 leading-relaxed">
                Scale your expertise with AI that creates personalized curricula, keeps content fresh, and adapts to every student&apos;s learning style.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Link href="/auth/signup">
                  <Button size="lg" className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-lg px-8 py-3 h-auto">
                    Start Free Trial
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
                <Button variant="outline" size="lg" className="text-lg px-8 py-3 h-auto border-gray-300 text-gray-700 hover:bg-gray-50">
                  <Play className="w-5 h-5 mr-2" />
                  Watch Demo
                </Button>
              </div>
              
              <div className="flex items-center gap-6 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  <span>No credit card required</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  <span>14-day free trial</span>
                </div>
              </div>
            </div>

            {/* Right Visual */}
            <div className="relative lg:pl-8">
              <div className="relative">
                {/* Main Image */}
                <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-gray-100">
                  <ImageWithFallback
                    src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&h=600&fit=crop"
                    alt="AI-powered education platform dashboard"
                    className="w-full h-auto"
                  />
                </div>
                
                {/* Floating Stats Cards */}
                <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-lg border border-gray-100 p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">50% Faster</p>
                      <p className="text-sm text-gray-500">Course Creation</p>
                    </div>
                  </div>
                </div>
                
                <div className="absolute -top-6 -right-6 bg-white rounded-xl shadow-lg border border-gray-100 p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center">
                      <Users className="w-5 h-5 text-teal-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">10,000+</p>
                      <p className="text-sm text-gray-500">Students</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - Light Background */}
      <section id="features" className="bg-gray-50 py-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 bg-teal-50 border border-teal-200 rounded-full px-4 py-2 mb-6">
              <Rocket className="w-4 h-4 text-teal-600" />
              <span className="text-teal-700 font-medium text-sm">Core Features</span>
            </div>
            <h2 className="text-3xl lg:text-4xl xl:text-5xl font-black mb-6 text-gray-900">
              Everything you need to
              <br />
              <span className="bg-gradient-to-r from-teal-600 to-emerald-600 bg-clip-text text-transparent">
                scale your teaching
              </span>
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              From curriculum generation to personalized feedback, our AI copilot handles the heavy lifting.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: BookOpen,
                title: "Curriculum Generation",
                description: "Generate complete lesson plans, slides, and exercises from simple prompts.",
                gradient: "from-emerald-500 to-teal-500"
              },
              {
                icon: Users,
                title: "Personalized Learning",
                description: "Tailor content to each student's background, interests, and learning style.",
                gradient: "from-teal-500 to-green-500"
              },
              {
                icon: Clock,
                title: "Content Freshness",
                description: "Stay current with automated updates from curated industry sources.",
                gradient: "from-green-500 to-emerald-500"
              },
              {
                icon: Target,
                title: "Human-in-the-Loop",
                description: "Maintain full editorial control with side-by-side diff reviews.",
                gradient: "from-emerald-600 to-teal-600"
              },
              {
                icon: Award,
                title: "Smart Assessment",
                description: "Auto-generate rubrics and provide personalized feedback.",
                gradient: "from-teal-600 to-green-600"
              },
              {
                icon: Zap,
                title: "Real-time Collaboration",
                description: "Work seamlessly with AI while maintaining your unique voice.",
                gradient: "from-green-600 to-emerald-600"
              }
            ].map((feature, index) => (
              <Card key={index} className="group bg-white border border-gray-200 hover:border-gray-300 transition-all duration-300 hover:shadow-lg">
                <CardHeader className="p-[21px]">
                  <div className={`w-12 h-12 bg-gradient-to-r ${feature.gradient} rounded-xl flex items-center justify-center mb-4`}>
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <CardTitle className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</CardTitle>
                  <CardDescription className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section - Dark Background */}
      <section className="bg-slate-900 text-white py-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { number: "50%", label: "Time Reduction", icon: Clock },
              { number: "10k+", label: "Students Reached", icon: Users },
              { number: "500+", label: "Educators", icon: Globe },
              { number: "95%", label: "Satisfaction Rate", icon: Star }
            ].map((stat, index) => (
              <div key={index} className="text-center group">
                <div className="w-16 h-16 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                  <stat.icon className="w-8 h-8 text-white" />
                </div>
                <div className="text-3xl lg:text-4xl font-black text-white mb-2">{stat.number}</div>
                <div className="text-white/70 font-medium">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section - Light Background */}
      <section id="benefits" className="bg-white py-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-4 py-2 mb-6">
                <Award className="w-4 h-4 text-emerald-600" />
                <span className="text-emerald-700 font-medium text-sm">Proven Results</span>
              </div>
              
              <h2 className="text-3xl lg:text-4xl xl:text-5xl font-black mb-6 text-gray-900">
                Transform your
                <br />
                <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                  teaching efficiency
                </span>
              </h2>
              
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Join hundreds of educators who have revolutionized their course creation process.
              </p>

              <div className="space-y-6">
                {[
                  {
                    title: "50% Faster Course Creation",
                    description: "Generate complete modules in hours, not weeks, while maintaining high standards.",
                    color: "emerald"
                  },
                  {
                    title: "Always Current Content",
                    description: "Automatically update your curriculum as new developments emerge.",
                    color: "teal"
                  },
                  {
                    title: "Personalized at Scale",
                    description: "Deliver tailored learning experiences to every student effortlessly.",
                    color: "green"
                  }
                ].map((benefit, index) => (
                  <div key={index} className="flex items-start gap-4">
                    <div className={`w-8 h-8 bg-gradient-to-r ${
                      benefit.color === 'emerald' ? 'from-emerald-500 to-teal-500' :
                      benefit.color === 'teal' ? 'from-teal-500 to-green-500' :
                      'from-green-500 to-emerald-500'
                    } rounded-lg flex items-center justify-center flex-shrink-0 mt-1`}>
                      <CheckCircle className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">{benefit.title}</h3>
                      <p className="text-gray-600">{benefit.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="relative rounded-2xl overflow-hidden shadow-xl bg-gray-100">
                <ImageWithFallback
                  src="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&h=600&fit=crop"
                  alt="Diverse group of students learning"
                  className="w-full h-auto"
                />
              </div>
              
              <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-lg border border-gray-100 p-4">
                <div className="text-center">
                  <div className="text-2xl font-black text-gray-900 mb-1">85%</div>
                  <div className="text-sm text-gray-500">Time Savings</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials - Dark Background */}
      <section className="bg-slate-900 text-white py-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-2 mb-6">
              <Star className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-300 font-medium text-sm">Testimonials</span>
            </div>
            <h2 className="text-3xl lg:text-4xl xl:text-5xl font-black mb-4">
              <span className="bg-gradient-to-r from-white to-emerald-200 bg-clip-text text-transparent">
                Loved by educators
              </span>
              <br />
              <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                worldwide
              </span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: "Dr. Sarah Mitchell",
                role: "Professor, MIT",
                content: "This AI copilot has completely transformed how I create courses. What used to take weeks now takes days.",
                initials: "SM",
                gradient: "from-teal-500 to-green-500"
              },
              {
                name: "Prof. James Rodriguez",
                role: "Stanford University",
                content: "The personalization features are incredible. My students are more engaged than ever before.",
                initials: "JR",
                gradient: "from-emerald-500 to-teal-500"
              },
              {
                name: "Dr. Lisa Chen",
                role: "Carnegie Mellon",
                content: "Finally, an AI tool that understands pedagogy. It's like having an expert teaching assistant.",
                initials: "LC",
                gradient: "from-green-500 to-emerald-500"
              }
            ].map((testimonial, index) => (
              <Card key={index} className="bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all duration-300">
                <CardContent className="pt-6">
                  <div className="flex mb-4">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-emerald-400 text-emerald-400" />
                    ))}
                  </div>
                  <p className="text-white/80 mb-6 leading-relaxed">
                    &ldquo;{testimonial.content}&rdquo;
                  </p>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 bg-gradient-to-r ${testimonial.gradient} rounded-full flex items-center justify-center`}>
                      <span className="font-semibold text-white text-sm">{testimonial.initials}</span>
                    </div>
                    <div>
                      <p className="font-semibold text-white">{testimonial.name}</p>
                      <p className="text-white/60 text-sm">{testimonial.role}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section - Colored Background */}
      <section className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl lg:text-4xl xl:text-5xl font-black mb-6">
              Ready to revolutionize
              <br />
              your teaching?
            </h2>
            <p className="text-lg text-white/90 mb-8 max-w-2xl mx-auto">
              Join thousands of educators who are already using AI to create better courses faster.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup">
                <Button size="lg" className="bg-white text-emerald-600 hover:bg-gray-100 text-lg px-8 py-3 h-auto">
                  Start Free Trial
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="border-white bg-white/10 text-white hover:bg-white/20 backdrop-blur-sm text-lg px-8 py-3 h-auto">
                Schedule Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer - Dark Background */}
      <footer className="bg-slate-900 border-t border-white/10 py-16 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12">
            <div>
              <div className="flex items-center mb-6">
                <img src="/Edura_club.svg" alt="Edura" className="h-12 w-auto" />
              </div>
              <p className="text-white/60 leading-relaxed">
                Empowering educators with AI to create the most personalized learning experiences.
              </p>
            </div>
            
            {[
              {
                title: "Product",
                links: ["Features", "Pricing", "Documentation", "API"]
              },
              {
                title: "Company", 
                links: ["About", "Blog", "Careers", "Contact"]
              },
              {
                title: "Support",
                links: ["Help Center", "Community", "Privacy Policy", "Terms of Service"]
              }
            ].map((section, index) => (
              <div key={index}>
                <h4 className="font-semibold text-white mb-4">{section.title}</h4>
                <ul className="space-y-2">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <a href="#" className="text-white/60 hover:text-white transition-colors text-sm">{link}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          
          <div className="border-t border-white/10 mt-12 pt-8 text-center text-white/60 text-sm">
            <p>&copy; 2025 Edura. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
