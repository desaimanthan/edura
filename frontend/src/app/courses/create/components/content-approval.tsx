"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, XCircle, Clock, Edit3, FileText, Presentation, BookOpen, Video } from 'lucide-react';

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

interface ContentApprovalProps {
  courseId: string;
  onApproval?: (materialId: string, approved: boolean, modifications?: string) => void;
  onStructureApproval?: (approved: boolean, modifications?: string) => void;
}

const ContentApproval: React.FC<ContentApprovalProps> = ({
  courseId,
  onApproval,
  onStructureApproval
}) => {
  const [materials, setMaterials] = useState<ContentMaterial[]>([]);
  const [checklists, setChecklists] = useState<CourseStructureChecklist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMaterial, setSelectedMaterial] = useState<string | null>(null);
  const [modifications, setModifications] = useState<string>('');
  const [approvalMode, setApprovalMode] = useState<'structure' | 'content'>('structure');
  const [processingApproval, setProcessingApproval] = useState<string | null>(null);

  // Fetch content progress data
  useEffect(() => {
    const fetchContentProgress = async () => {
      try {
        setLoading(true);
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
        
        // Determine approval mode based on workflow step
        if (data.workflow_step === 'content_structure_approval') {
          setApprovalMode('structure');
        } else if (data.workflow_step === 'content_creation') {
          setApprovalMode('content');
        }
        
      } catch (err) {
        console.error('Error fetching content progress:', err);
        setError(err instanceof Error ? err.message : 'Failed to load content data');
      } finally {
        setLoading(false);
      }
    };

    if (courseId) {
      fetchContentProgress();
    }
  }, [courseId]);

  const handleStructureApproval = async (approved: boolean) => {
    try {
      setProcessingApproval('structure');
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/courses/${courseId}/approve-content-structure`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          approved,
          modifications: approved ? undefined : modifications
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to process structure approval: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (onStructureApproval) {
        onStructureApproval(approved, approved ? undefined : modifications);
      }
      
      // Reset form
      setModifications('');
      
      // Show success message or handle workflow transition
      
    } catch (err) {
      console.error('Error processing structure approval:', err);
      setError(err instanceof Error ? err.message : 'Failed to process approval');
    } finally {
      setProcessingApproval(null);
    }
  };

  const handleContentApproval = async (materialId: string, approved: boolean) => {
    try {
      setProcessingApproval(materialId);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/courses/${courseId}/approve-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          material_id: materialId,
          approved,
          modifications: approved ? undefined : modifications
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to process content approval: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (onApproval) {
        onApproval(materialId, approved, approved ? undefined : modifications);
      }
      
      // Update material status locally
      setMaterials(prev => prev.map(material => 
        material._id === materialId 
          ? { ...material, status: approved ? 'completed' : 'needs_revision' }
          : material
      ));
      
      // Reset form
      setSelectedMaterial(null);
      setModifications('');
      
      
    } catch (err) {
      console.error('Error processing content approval:', err);
      setError(err instanceof Error ? err.message : 'Failed to process approval');
    } finally {
      setProcessingApproval(null);
    }
  };

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
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
      case 'needs_revision':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Needs Revision</Badge>;
      case 'in_progress':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />In Progress</Badge>;
      case 'pending':
      default:
        return <Badge variant="outline"><Clock className="h-3 w-3 mr-1" />Pending Review</Badge>;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Content Approval</CardTitle>
          <CardDescription>Loading content for review...</CardDescription>
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
          <CardTitle>Content Approval</CardTitle>
          <CardDescription>Error loading content</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-red-600 text-center py-4">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Structure Approval Section */}
      {approvalMode === 'structure' && checklists.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Content Structure Approval
            </CardTitle>
            <CardDescription>
              Review and approve the proposed content structure for your course
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {checklists.map((checklist) => (
              <div key={checklist._id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-lg">
                    Module {checklist.module_number}: {checklist.module_title}
                  </h3>
                  {getStatusBadge(checklist.status)}
                </div>
                
                <div className="space-y-3">
                  {checklist.chapters.map((chapter) => (
                    <div key={chapter.chapter_number} className="ml-4 border-l-2 border-gray-200 pl-4">
                      <h4 className="font-medium text-base mb-2">
                        Chapter {chapter.chapter_number}: {chapter.chapter_title}
                      </h4>
                      
                      {chapter.learning_objectives.length > 0 && (
                        <div className="mb-2">
                          <p className="text-sm font-medium text-gray-600 mb-1">Learning Objectives:</p>
                          <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                            {chapter.learning_objectives.map((objective, idx) => (
                              <li key={idx}>{objective}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {chapter.materials.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-gray-600 mb-2">Materials:</p>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {chapter.materials.map((material, idx) => (
                              <div key={idx} className="flex items-start gap-2 p-2 bg-gray-50 rounded text-sm">
                                {getMaterialIcon(material.material_type)}
                                <div className="flex-1">
                                  <p className="font-medium">{material.title}</p>
                                  <p className="text-gray-600 text-xs">{material.description}</p>
                                  <p className="text-gray-500 text-xs">Duration: {material.estimated_duration}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-600 mb-2">
                    Total Materials: <span className="font-medium">{checklist.total_materials}</span>
                  </p>
                </div>
              </div>
            ))}
            
            {/* Structure Approval Actions */}
            <div className="space-y-4 pt-4 border-t">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modifications or Comments (optional)
                </label>
                <Textarea
                  value={modifications}
                  onChange={(e) => setModifications(e.target.value)}
                  placeholder="Enter any modifications or comments about the content structure..."
                  rows={3}
                />
              </div>
              
              <div className="flex gap-3">
                <Button
                  onClick={() => handleStructureApproval(true)}
                  disabled={processingApproval === 'structure'}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  {processingApproval === 'structure' ? 'Processing...' : 'Approve Structure'}
                </Button>
                
                <Button
                  onClick={() => handleStructureApproval(false)}
                  disabled={processingApproval === 'structure' || !modifications.trim()}
                  variant="outline"
                  className="border-red-300 text-red-700 hover:bg-red-50"
                >
                  <Edit3 className="h-4 w-4 mr-2" />
                  Request Modifications
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Individual Content Approval Section */}
      {approvalMode === 'content' && materials.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Individual Content Approval
            </CardTitle>
            <CardDescription>
              Review and approve individual course materials
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {materials.map((material) => (
                <div key={material._id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3">
                      {getMaterialIcon(material.material_type)}
                      <div>
                        <h3 className="font-semibold">
                          Module {material.module_number}, Chapter {material.chapter_number}: {material.title}
                        </h3>
                        {material.description && (
                          <p className="text-gray-600 text-sm mt-1">{material.description}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          Type: {material.material_type} • Updated: {new Date(material.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    {getStatusBadge(material.status)}
                  </div>
                  
                  {material.content && (
                    <div className="mb-4">
                      <details className="group">
                        <summary className="cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-800">
                          View Content Preview
                        </summary>
                        <div className="mt-2 p-3 bg-gray-50 rounded text-sm max-h-40 overflow-y-auto">
                          <pre className="whitespace-pre-wrap font-sans">
                            {material.content.substring(0, 500)}
                            {material.content.length > 500 && '...'}
                          </pre>
                        </div>
                      </details>
                    </div>
                  )}
                  
                  {material.public_url && (
                    <div className="mb-4">
                      <a
                        href={material.public_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 text-sm underline"
                      >
                        &larr; View Full Content
                      </a>
                    </div>
                  )}
                  
                  {material.status === 'pending' && (
                    <div className="space-y-3 pt-3 border-t">
                      {selectedMaterial === material._id && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Modifications or Comments
                          </label>
                          <Textarea
                            value={modifications}
                            onChange={(e) => setModifications(e.target.value)}
                            placeholder="Enter any modifications or comments about this content..."
                            rows={2}
                          />
                        </div>
                      )}
                      
                      <div className="flex gap-2">
                        <Button
                          onClick={() => handleContentApproval(material._id, true)}
                          disabled={processingApproval === material._id}
                          size="sm"
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="h-3 w-3 mr-1" />
                          {processingApproval === material._id ? 'Processing...' : 'Approve'}
                        </Button>
                        
                        {selectedMaterial === material._id ? (
                          <>
                            <Button
                              onClick={() => handleContentApproval(material._id, false)}
                              disabled={processingApproval === material._id || !modifications.trim()}
                              size="sm"
                              variant="outline"
                              className="border-red-300 text-red-700 hover:bg-red-50"
                            >
                              <XCircle className="h-3 w-3 mr-1" />
                              Request Changes
                            </Button>
                            <Button
                              onClick={() => {
                                setSelectedMaterial(null);
                                setModifications('');
                              }}
                              size="sm"
                              variant="ghost"
                            >
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <Button
                            onClick={() => setSelectedMaterial(material._id)}
                            size="sm"
                            variant="outline"
                          >
                            <Edit3 className="h-3 w-3 mr-1" />
                            Request Changes
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
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
            <CardTitle>Content Approval</CardTitle>
            <CardDescription>No content available for review</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No content materials or structure found for this course.</p>
              <p className="text-sm mt-2">Content will appear here once it&apos;s generated.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ContentApproval;
