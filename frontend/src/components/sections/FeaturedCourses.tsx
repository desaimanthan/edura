"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ImageWithFallback } from "@/components/figma/ImageWithFallback"
import { Clock, Star, ChevronRight, BookOpen } from "lucide-react"
import Link from "next/link"
import { featuredCourses } from "@/data/featured-courses"

interface FeaturedCoursesProps {
  onCourseClick?: (courseId: number) => void
}

export function FeaturedCourses({ onCourseClick }: FeaturedCoursesProps) {
  const handleCourseClick = (courseId: number) => {
    if (onCourseClick) {
      onCourseClick(courseId)
    } else {
      // Default behavior: navigate to course detail page
      window.location.href = `/courses/${courseId}`
    }
  }

  return (
    <section className="bg-gray-50 py-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-2 mb-6">
            <BookOpen className="w-4 h-4 text-blue-600" />
            <span className="text-blue-700 font-medium text-sm">Featured Courses</span>
          </div>
          <h2 className="text-3xl lg:text-4xl xl:text-5xl font-black mb-6 text-gray-900">
            Master AI & Data Science
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              with Expert-Led Courses
            </span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
            Learn from industry professionals and academic experts with hands-on projects and real-world applications.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {featuredCourses.map((course) => (
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
              </div>
              
              <CardHeader className="pb-3">
                <CardTitle className="text-xl font-semibold text-gray-900 mb-2">
                  {course.title}
                </CardTitle>
                <CardDescription className="text-gray-600 leading-relaxed">
                  {course.description}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div className="flex items-center text-sm text-gray-500 space-x-4">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{course.duration}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    <span>{course.rating}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between pt-2">
                  <div>
                    <p className="text-sm text-gray-500">by {course.instructor}</p>
                  </div>
                  <Link href="/auth/signup">
                    <Button 
                      size="sm"
                      className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Enroll Now
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <Link href="/courses/catalog">
            <Button 
              size="lg"
              variant="outline"
              className="text-lg px-8 py-3 h-auto border-2 border-gray-300 text-gray-700 hover:bg-gray-900 hover:text-white hover:border-gray-900"
            >
              View All Courses
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  )
}
