"use client"

import { useState, use } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ImageWithFallback } from "@/components/figma/ImageWithFallback"
import { ArrowLeft, Star, Users, Clock, Bookmark, Share2, Video, FileText, Download, Award, Globe, CheckCircle, ThumbsUp, MessageCircle, Brain } from "lucide-react"
import Link from "next/link"
import { allCourses } from "@/data/featured-courses"
import { FeaturedCourse } from "@/types/course"

interface CourseDetailProps {
  params: Promise<{ courseId: string }>
}

export default function CourseDetail({ params }: CourseDetailProps) {
  const resolvedParams = use(params)
  const courseId = parseInt(resolvedParams.courseId)
  const course = allCourses.find(c => c.id === courseId)

  if (!course) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Course Not Found</h1>
          <p className="text-gray-600 mb-6">The course you're looking for doesn't exist.</p>
          <Link href="/courses/catalog">
            <Button>Browse All Courses</Button>
          </Link>
        </div>
      </div>
    )
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
              <Link href="/courses/catalog" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">Courses</Link>
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

      {/* Course Hero Section */}
      <section className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/courses/catalog">
              <Button 
                variant="ghost" 
                className="text-white/80 hover:text-white hover:bg-white/10 -ml-4"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to courses
              </Button>
            </Link>
          </div>
          
          <div className="grid lg:grid-cols-3 gap-12 items-start">
            {/* Left Content */}
            <div className="lg:col-span-2">
              <div className="flex items-center gap-4 mb-4">
                <Badge 
                  className={`${
                    course.difficulty === 'Beginner' ? 'bg-green-100 text-green-700' :
                    course.difficulty === 'Intermediate' ? 'bg-blue-100 text-blue-700' :
                    'bg-purple-100 text-purple-700'
                  } border-0`}
                >
                  {course.difficulty}
                </Badge>
                <Badge className="bg-white/20 text-white border-0">
                  {course.category}
                </Badge>
              </div>
              
              <h1 className="text-4xl lg:text-5xl font-black mb-6 leading-tight">
                {course.title}
              </h1>
              
              <p className="text-xl text-white/90 mb-8 leading-relaxed">
                {course.fullDescription}
              </p>
              
              <div className="flex items-center gap-8 text-white/80 mb-8">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  <span className="font-semibold">{course.rating}</span>
                  <span>({course.reviews} reviews)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  <span>{course.students.toLocaleString()} students</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  <span>{course.duration}</span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <ImageWithFallback
                  src={course.instructorImage}
                  alt={course.instructor}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <p className="font-semibold text-white">Instructor: {course.instructor}</p>
                  <p className="text-white/70">AI & Machine Learning Expert</p>
                </div>
              </div>

              {/* Course Actions */}
              <div className="flex gap-3 mt-8">
                <Button 
                  size="sm" 
                  className="bg-white/20 backdrop-blur-sm border border-white/30 text-white hover:bg-white/30 hover:text-white font-medium"
                >
                  <Bookmark className="w-4 h-4 mr-2" />
                  Save Course
                </Button>
                <Button 
                  size="sm" 
                  className="bg-white/20 backdrop-blur-sm border border-white/30 text-white hover:bg-white/30 hover:text-white font-medium"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Share
                </Button>
              </div>
            </div>

            {/* Right Sidebar - Course Image */}
            <div className="lg:col-span-1">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                <ImageWithFallback
                  src={course.image}
                  alt={course.title}
                  className="w-full h-48 object-cover rounded-lg mb-6"
                />
                
                <div className="space-y-4 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-white/80">Price</span>
                    <span className="text-2xl font-bold text-white">${course.price}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white/80">Duration</span>
                    <span className="text-white">{course.duration}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white/80">Lessons</span>
                    <span className="text-white">{course.lessons}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white/80">Projects</span>
                    <span className="text-white">{course.projects}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white/80">Certificate</span>
                    <span className="text-white">{course.certificate ? 'Yes' : 'No'}</span>
                  </div>
                </div>
                
                <Link href="/auth/signup">
                  <Button 
                    size="lg"
                    className="w-full bg-white text-emerald-600 hover:bg-gray-100 font-semibold"
                  >
                    Enroll Now - ${course.price}
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Course Content */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-3 gap-12">
            {/* Main Content */}
            <div className="lg:col-span-2">
              <Tabs defaultValue="overview" className="space-y-8">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="curriculum">Curriculum</TabsTrigger>
                  <TabsTrigger value="instructor">Instructor</TabsTrigger>
                  <TabsTrigger value="reviews">Reviews</TabsTrigger>
                </TabsList>
                
                <TabsContent value="overview" className="space-y-8">
                  <Card>
                    <CardHeader>
                      <CardTitle>What you'll learn</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-4">
                        {course.skills.map((skill, index) => (
                          <div key={index} className="flex items-center gap-3">
                            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                            <span className="text-gray-700">{skill}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Prerequisites</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {course.prerequisites.map((prereq, index) => (
                          <div key={index} className="flex items-center gap-3">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full flex-shrink-0" />
                            <span className="text-gray-700">{prereq}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Course Description</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700 leading-relaxed">
                        {course.fullDescription}
                      </p>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="curriculum" className="space-y-6">
                  {course.curriculum.map((module, index) => (
                    <Card key={index}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">
                            Module {index + 1}: {module.title}
                          </CardTitle>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span>{module.lessons} lessons</span>
                            <span>{module.duration}</span>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {Array.from({ length: module.lessons }, (_, i) => (
                            <div key={i} className="flex items-center gap-3 p-3 rounded-lg border border-gray-100">
                              <Video className="w-5 h-5 text-emerald-500" />
                              <span className="flex-1">Lesson {i + 1}: Introduction to concepts</span>
                              <span className="text-sm text-gray-500">
                                {Math.floor(parseInt(module.duration) / module.lessons)} min
                              </span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="instructor" className="space-y-6">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-6">
                        <ImageWithFallback
                          src={course.instructorImage}
                          alt={course.instructor}
                          className="w-24 h-24 rounded-full object-cover"
                        />
                        <div className="flex-1">
                          <h3 className="text-2xl font-semibold mb-2">{course.instructor}</h3>
                          <p className="text-gray-600 mb-4">AI & Machine Learning Expert</p>
                          <p className="text-gray-700 leading-relaxed">
                            {course.instructorBio}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Instructor Stats</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-6 text-center">
                        <div>
                          <div className="text-2xl font-bold text-emerald-600">4.9</div>
                          <div className="text-sm text-gray-500">Average Rating</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-emerald-600">15K+</div>
                          <div className="text-sm text-gray-500">Students Taught</div>
                        </div>
                        <div>
                          <div className="text-2xl font-bold text-emerald-600">8</div>
                          <div className="text-sm text-gray-500">Courses</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="reviews" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Student Reviews</CardTitle>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                          <span className="text-xl font-semibold">{course.rating}</span>
                        </div>
                        <span className="text-gray-500">({course.reviews} reviews)</span>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {/* Sample Reviews */}
                      {[
                        {
                          name: "Sarah Johnson",
                          rating: 5,
                          comment: "Excellent course! The instructor explains complex concepts clearly and the hands-on projects really help solidify the learning.",
                          date: "2 weeks ago"
                        },
                        {
                          name: "Mike Chen",
                          rating: 5,
                          comment: "Best ML course I've taken. Great balance of theory and practical application. Highly recommend!",
                          date: "1 month ago"
                        },
                        {
                          name: "Jessica Brown",
                          rating: 4,
                          comment: "Very comprehensive course. Could use more advanced topics but overall great for beginners to intermediate learners.",
                          date: "1 month ago"
                        }
                      ].map((review, index) => (
                        <div key={index} className="border-b border-gray-100 pb-6 last:border-0">
                          <div className="flex items-start gap-4">
                            <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                              <span className="font-semibold text-emerald-600">
                                {review.name.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <span className="font-semibold">{review.name}</span>
                                <div className="flex">
                                  {[...Array(review.rating)].map((_, i) => (
                                    <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                                  ))}
                                </div>
                                <span className="text-sm text-gray-500">{review.date}</span>
                              </div>
                              <p className="text-gray-700">{review.comment}</p>
                              <div className="flex items-center gap-4 mt-3">
                                <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                                  <ThumbsUp className="w-4 h-4 mr-1" />
                                  Helpful (12)
                                </Button>
                                <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                                  <MessageCircle className="w-4 h-4 mr-1" />
                                  Reply
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="sticky top-32 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Course Features</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Video className="w-5 h-5 text-emerald-500" />
                      <span>{course.lessons} video lessons</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-emerald-500" />
                      <span>{course.projects} hands-on projects</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Download className="w-5 h-5 text-emerald-500" />
                      <span>Downloadable resources</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Award className="w-5 h-5 text-emerald-500" />
                      <span>Certificate of completion</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Globe className="w-5 h-5 text-emerald-500" />
                      <span>Lifetime access</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Related Courses</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {allCourses
                      .filter(c => c.id !== course.id && c.category === course.category)
                      .slice(0, 2)
                      .map(relatedCourse => (
                        <Link key={relatedCourse.id} href={`/courses/${relatedCourse.id}`}>
                          <div className="flex gap-3 p-3 rounded-lg border border-gray-100 hover:border-gray-200 cursor-pointer transition-colors">
                            <ImageWithFallback
                              src={relatedCourse.image}
                              alt={relatedCourse.title}
                              className="w-16 h-12 object-cover rounded"
                            />
                            <div className="flex-1">
                              <h4 className="font-semibold text-sm line-clamp-2">{relatedCourse.title}</h4>
                              <div className="flex items-center gap-2 mt-1">
                                <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                <span className="text-xs text-gray-500">{relatedCourse.rating}</span>
                              </div>
                            </div>
                          </div>
                        </Link>
                      ))}
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
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
              Enroll Now - ${course.price}
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
