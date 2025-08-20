"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Play, 
  Pause, 
  FileText, 
  Presentation, 
  BookOpen, 
  Video,
  BarChart3,
  RefreshCw
} from 'lucide-react';

interface ContentMaterial {
  _id: string;
  course_id: string;
  module_number: number;
  chapter_number: number;
  material_type: string;
  title: string;
  description?: string;
  content?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'needs_revision';
  r2_key?: string;
  public_url?: string;
  created_at: string;
  updated_at: string;
}

interface CourseStructureChecklist {
  _id: string;
  course_id: string;
  module_title: string;
  module_number: number;
  chapters: Array<{
    chapter_number: number;
    chapter_title: string;
    learning_objectives: string[];
    materials: Array<{
      material_type: string;
      title: string;
      description: string;
      estimated_duration: string;
    }>;
  }>;
  total_materials: number;
  status: 'pending' | 'approved' | 'needs_revision';
  created_at: string;
  updated_at: string;
}

interface ProgressStats {
  total_materials: number;
  completed_materials: number;
  pending_materials: number;
  in_progress_materials: number;
  completion_percentage: number;
}

interface ContentProgressProps {
  courseId: string;
  onStartGeneration?: () => void;
  onPauseGeneration?: () => void;
  refreshInterval?: number; // in milliseconds
}

const ContentProgress: React.FC<ContentProgressProps> = ({
  courseId,
  onStartGeneration,
  onPauseGeneration,
  refreshInterval = 5000 // 5 seconds default
}) => {
  const [materials, setMaterials] = useState<ContentMaterial[]>([]);
  const [checklists, setChecklists] = useState<CourseStructureChecklist[]>([]);
  const [progressStats, setProgressStats] = useState<ProgressStats>({
    total_materials: 0,
    completed_materials: 0,
    pending_materials: 0,
    in_progress_materials: 0,
    completion_percentage: 0
  });
  const [workflowStep, setWorkflowStep] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Fetch content progress data
  const fetchContentProgress = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/courses/${courseId}/content-progress`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch content progress: ${response.statusText}`);
      }

      const data = await response.json();
      setMaterials(data.materials || []);
      setChecklists(data.checklists || []);
      setProgressStats(data.progress_stats || {
        total_materials: 0,
        completed_materials: 0,
        pending_materials: 0,
        in_progress_materials: 0,
        completion_percentage: 0
      });
      setWorkflowStep(data.workflow_step || '');
      setLastUpdated(new Date());
      
      // Check if generation is in progress
      setIsGenerating(data.progress_stats?.in_progress_materials > 0);
      
    } catch (err) {
      console.error('Error fetching content progress:', err);
      setError(err instanceof Error ? err.message : 'Failed to load progress data');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    if (courseId) {
      fetchContentProgress();
    }
  }, [courseId]);

  // Auto-refresh when generation is in progress
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isGenerating && refreshInterval > 0) {
      interval = setInterval(() => {
        fetchContentProgress();
      }, refreshInterval);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isGenerating, refreshInterval, courseId]);

  const getMaterialIcon = (materialType: string) => {
    switch (materialType.toLowerCase()) {
      case 'slides':
      case 'presentation':
        return <Presentation className="h-4 w-4" />;
      case 'video':
      case 'lecture':
        return <Video className="h-4 w-4" />;
      case 'reading':
      case 'article':
        return <BookOpen className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'needs_revision':
        return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Needs Revision</Badge>;
      case 'in_progress':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />In Progress</Badge>;
      case 'pending':
      default:
        return <Badge variant="outline"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
    }
  };

  const getWorkflowStepDisplay = (step: string) => {
    switch (step) {
      case 'content_structure_generation':
        return 'Generating Content Structure';
      case 'content_structure_approval':
        return 'Awaiting Structure Approval';
      case 'content_creation':
        return 'Creating Content Materials';
      case 'content_complete':
        return 'Content Creation Complete';
      default:
        return 'Content Creation';
    }
  };

  const handleStartGeneration = async () => {
    try {
      setIsGenerating(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/courses/${courseId}/generate-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to start content generation: ${response.statusText}`);
      }

      if (onStartGeneration) {
        onStartGeneration();
      }
      
      // Refresh progress immediately
      await fetchContentProgress();
      
    } catch (err) {
      console.error('Error starting content generation:', err);
      setError(err instanceof Error ? err.message : 'Failed to start generation');
      setIsGenerating(false);
    }
  };

  const handleRefresh = () => {
    fetchContentProgress();
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Content Generation Progress
          </CardTitle>
          <CardDescription>Loading progress data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Content Generation Progress
          </CardTitle>
          <CardDescription>Error loading progress</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-red-600 text-center py-4">
            {error}
            <Button 
              onClick={handleRefresh} 
              variant="outline" 
              size="sm" 
              className="ml-2"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall Progress Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Content Generation Progress
              </CardTitle>
              <CardDescription>
                {getWorkflowStepDisplay(workflowStep)}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="sm"
                disabled={isGenerating}
              >
                <RefreshCw className={`h-3 w-3 mr-1 ${isGenerating ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              {workflowStep === 'content_creation' && !isGenerating && progressStats.pending_materials > 0 && (
                <Button
                  onClick={handleStartGeneration}
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Play className="h-3 w-3 mr-1" />
                  Start Generation
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{Math.round(progressStats.completion_percentage)}%</span>
            </div>
            <Progress 
              value={progressStats.completion_percentage} 
              className="h-2"
            />
          </div>

          {/* Statistics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{progressStats.total_materials}</div>
              <div className="text-sm text-gray-600">Total Materials</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{progressStats.completed_materials}</div>
              <div className="text-sm text-green-600">Completed</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{progressStats.in_progress_materials}</div>
              <div className="text-sm text-blue-600">In Progress</div>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-700">{progressStats.pending_materials}</div>
              <div className="text-sm text-yellow-600">Pending</div>
            </div>
          </div>

          {/* Last Updated */}
          <div className="text-xs text-gray-500 text-center">
            Last updated: {lastUpdated.toLocaleTimeString()}
            {isGenerating && (
              <span className="ml-2 inline-flex items-center">
                <div className="animate-pulse h-2 w-2 bg-blue-500 rounded-full mr-1"></div>
                Auto-refreshing...
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Content Structure Overview */}
      {checklists.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Content Structure Overview
            </CardTitle>
            <CardDescription>
              Course modules and their content generation status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {checklists.map((checklist) => {
                const moduleProgress = materials.filter(m => m.module_number === checklist.module_number);
                const completedInModule = moduleProgress.filter(m => m.status === 'completed').length;
                const totalInModule = moduleProgress.length;
                const modulePercentage = totalInModule > 0 ? (completedInModule / totalInModule) * 100 : 0;

                return (
                  <div key={checklist._id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold">
                        Module {checklist.module_number}: {checklist.module_title}
                      </h3>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">
                          {completedInModule}/{totalInModule} materials
                        </span>
                        {getStatusBadge(checklist.status)}
                      </div>
                    </div>
                    
                    <div className="space-y-2 mb-3">
                      <div className="flex justify-between text-sm">
                        <span>Module Progress</span>
                        <span>{Math.round(modulePercentage)}%</span>
                      </div>
                      <Progress value={modulePercentage} className="h-1" />
                    </div>

                    <div className="space-y-2">
                      {checklist.chapters.map((chapter) => {
                        const chapterMaterials = materials.filter(
                          m => m.module_number === checklist.module_number && 
                               m.chapter_number === chapter.chapter_number
                        );
                        
                        return (
                          <div key={chapter.chapter_number} className="ml-4 border-l-2 border-gray-200 pl-4">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium text-sm">
                                Chapter {chapter.chapter_number}: {chapter.chapter_title}
                              </h4>
                              <span className="text-xs text-gray-500">
                                {chapterMaterials.filter(m => m.status === 'completed').length}/{chapterMaterials.length}
                              </span>
                            </div>
                            
                            {chapterMaterials.length > 0 && (
                              <div className="mt-2 space-y-1">
                                {chapterMaterials.map((material) => (
                                  <div key={material._id} className="flex items-center gap-2 text-xs">
                                    {getMaterialIcon(material.material_type)}
                                    <span className="flex-1">{material.title}</span>
                                    {getStatusBadge(material.status)}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      {materials.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Recent Activity
            </CardTitle>
            <CardDescription>
              Latest content generation updates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {materials
                .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                .slice(0, 5)
                .map((material) => (
                  <div key={material._id} className="flex items-center gap-3 p-2 border rounded">
                    {getMaterialIcon(material.material_type)}
                    <div className="flex-1">
                      <p className="text-sm font-medium">
                        Module {material.module_number}, Chapter {material.chapter_number}: {material.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        Updated {new Date(material.updated_at).toLocaleString()}
                      </p>
                    </div>
                    {getStatusBadge(material.status)}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {materials.length === 0 && checklists.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Content Generation Progress</CardTitle>
            <CardDescription>No content generation in progress</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No content generation data available.</p>
              <p className="text-sm mt-2">Start content generation to see progress here.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ContentProgress;
