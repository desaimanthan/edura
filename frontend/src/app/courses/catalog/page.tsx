"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ImageWithFallback } from "@/components/figma/ImageWithFallback"
import { Search, Filter, ChevronRight, Calendar, Star, Users, Clock, BookOpen, Brain } from "lucide-react"
import Link from "next/link"
import { allCourses, categories } from "@/data/featured-courses"
import { FeaturedCourse } from "@/types/course"

export default function CourseCatalog() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("All")

  const filteredCourses = allCourses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         course.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         course.instructor.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === "All" || course.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const handleCourseClick = (courseId: number) => {
    // Navigate to course detail page
    window.location.href = `/courses/${courseId}`
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="relative z-50 bg-white border-b border-gray-100 sticky top-0">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="flex items-center">
              <img src="/Edura_club.svg" alt="Edura" className="h-12 w-auto cursor-pointer" />
            </Link>
            <div className="hidden md:flex items-center space-x-8">
              <Link href="/" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Home</Link>
              <Link href="/courses/catalog" className="text-emerald-600 font-medium">Courses</Link>
              <a href="/#features" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Features</a>
              <a href="/#pricing" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Pricing</a>
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

      {/* Course Catalog Header */}
      <section className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <h1 className="text-4xl lg:text-5xl font-black mb-6 leading-tight">
              Explore Our AI & Data Science Courses
            </h1>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              Master cutting-edge AI technologies with expert-led courses designed for modern learners.
            </p>
            
            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  placeholder="Search courses, instructors, topics..."
                  className="pl-10 h-12 text-base bg-white text-gray-900 border-0"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="relative">
                <select 
                  className="h-12 px-4 pr-10 bg-white text-gray-900 border-0 rounded-md font-medium appearance-none cursor-pointer"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
                <Filter className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Course Grid */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-black text-gray-900 mb-2">
                {filteredCourses.length} Course{filteredCourses.length !== 1 ? 's' : ''} Found
              </h2>
              <p className="text-gray-600">
                {selectedCategory !== "All" ? `Showing ${selectedCategory} courses` : "All available courses"}
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-8">
            {filteredCourses.map((course) => (
              <Card 
                key={course.id} 
                className="group overflow-hidden bg-white border border-gray-200 hover:border-gray-300 hover:shadow-xl transition-all duration-300 cursor-pointer"
                onClick={() => handleCourseClick(course.id)}
              >
                <div className="relative overflow-hidden">
                  <ImageWithFallback
                    src={course.image}
                    alt={course.title}
                    className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute top-4 left-4">
                    <Badge 
                      className={`${
                        course.difficulty === 'Beginner' ? 'bg-green-100 text-green-700' :
                        course.difficulty === 'Intermediate' ? 'bg-blue-100 text-blue-700' :
                        'bg-purple-100 text-purple-700'
                      } border-0`}
                    >
                      {course.difficulty}
                    </Badge>
                  </div>
                  <div className="absolute top-4 right-4">
                    <Badge className="bg-white/90 text-gray-700 border-0">
                      {course.category}
                    </Badge>
                  </div>
                </div>
                
                <CardHeader className="pb-3">
                  <CardTitle className="text-xl font-semibold text-gray-900 mb-2 line-clamp-2">
                    {course.title}
                  </CardTitle>
                  <CardDescription className="text-gray-600 leading-relaxed line-clamp-3">
                    {course.description}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="flex items-center text-sm text-gray-500 space-x-4">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>{course.duration}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>{course.students.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      <span>{course.rating}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between pt-2">
                    <div>
                      <p className="text-sm text-gray-500">Instructor</p>
                      <p className="font-semibold text-gray-900">{course.instructor}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">${course.price}</p>
                      <Link href="/auth/signup">
                        <Button 
                          className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 mt-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Enroll Now
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredCourses.length === 0 && (
            <div className="text-center py-16">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No courses found</h3>
              <p className="text-gray-600 mb-6">Try adjusting your search or filters to find more courses.</p>
              <Button 
                variant="outline"
                onClick={() => {
                  setSearchQuery("")
                  setSelectedCategory("All")
                }}
              >
                Clear Filters
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-slate-900 text-white py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-6">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl lg:text-4xl font-black mb-4">
            Ready to Start Learning?
          </h2>
          <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
            Join thousands of students already advancing their AI and data science skills.
          </p>
          <Link href="/auth/signup">
            <Button 
              size="lg" 
              className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-lg px-8 py-3 h-auto"
            >
              Create Free Account
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-white/10 py-16 text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12">
            <div>
              <div className="flex items-center mb-6">
                <img src="/Edura_club_w.svg" alt="Edura" className="h-12 w-auto" />
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
