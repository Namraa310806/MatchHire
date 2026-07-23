import { useState } from 'react';
import { useResumes, useActiveResume, useUploadResume, useActivateResume, useParseResume, useDeleteResume, useResumeVersionHistory, useRollbackVersion } from '@/features/resume/hooks/useResume';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileUpload } from '@/components/ui/file-upload';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spinner } from '@/components/ui/spinner';
import { FileText, CheckCircle, Trash2, History, Eye, Download } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function ResumePage() {
  const { data: resumes, isLoading: resumesLoading } = useResumes();
  const { data: activeResume, isLoading: activeLoading } = useActiveResume();
  const uploadResume = useUploadResume();
  const activateResume = useActivateResume();
  const parseResume = useParseResume();
  const deleteResume = useDeleteResume();
  const rollbackVersion = useRollbackVersion();

  const [showVersionHistory, setShowVersionHistory] = useState<string | null>(null);
  const [showParsedData, setShowParsedData] = useState<string | null>(null);

  const handleFileUpload = (files: File[]) => {
    if (files && files.length > 0) {
      uploadResume.mutate(files[0]);
    }
  };

  const handleActivate = (id: string) => {
    activateResume.mutate(id);
  };

  const handleParse = (id: string) => {
    parseResume.mutate(id, {
      onSuccess: () => {
        setShowParsedData(id);
      },
    });
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this resume?')) {
      deleteResume.mutate(id);
    }
  };

  const handleRollback = (resumeId: string, versionId: string) => {
    rollbackVersion.mutate({ id: resumeId, versionId: versionId });
  };

  if (resumesLoading || activeLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Resume Management</h1>
        <p className="text-muted-foreground mt-2">Upload and manage your resumes</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload New Resume</CardTitle>
        </CardHeader>
        <CardContent>
          {uploadResume.isPending ? (
            <div className="flex items-center justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <FileUpload
              onFileSelect={handleFileUpload}
              accept=".pdf,.doc,.docx"
              multiple={false}
            />
          )}
        </CardContent>
      </Card>

      {activeResume && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-primary" />
              Active Resume
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResumeCard
              resume={activeResume}
              isActive
              onActivate={() => {}}
              onParse={() => handleParse(activeResume.id)}
              onDelete={() => handleDelete(activeResume.id)}
              onViewVersions={() => setShowVersionHistory(activeResume.id)}
              onViewParsed={() => setShowParsedData(activeResume.id)}
              isParsing={parseResume.isPending}
            />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>All Resumes</CardTitle>
        </CardHeader>
        <CardContent>
          {resumes && resumes.length > 0 ? (
            <div className="space-y-4">
              {resumes
                .filter(r => r.id !== activeResume?.id)
                .map((resume) => (
                  <ResumeCard
                    key={resume.id}
                    resume={resume}
                    isActive={false}
                    onActivate={() => handleActivate(resume.id)}
                    onParse={() => handleParse(resume.id)}
                    onDelete={() => handleDelete(resume.id)}
                    onViewVersions={() => setShowVersionHistory(resume.id)}
                    onViewParsed={() => setShowParsedData(resume.id)}
                    isParsing={parseResume.isPending}
                  />
                ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No resumes uploaded yet</p>
          )}
        </CardContent>
      </Card>

      {/* Version History Dialog */}
      <Dialog open={!!showVersionHistory} onOpenChange={() => setShowVersionHistory(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Version History</DialogTitle>
          </DialogHeader>
          <VersionHistoryContent
            resumeId={showVersionHistory!}
            onRollback={handleRollback}
          />
        </DialogContent>
      </Dialog>

      {/* Parsed Data Dialog */}
      <Dialog open={!!showParsedData} onOpenChange={() => setShowParsedData(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Parsed Resume Data</DialogTitle>
          </DialogHeader>
          <ParsedDataContent resumeId={showParsedData!} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface ResumeCardProps {
  resume: any;
  isActive: boolean;
  onActivate: () => void;
  onParse: () => void;
  onDelete: () => void;
  onViewVersions: () => void;
  onViewParsed: () => void;
  isParsing: boolean;
}

function ResumeCard({ resume, isActive, onActivate, onParse, onDelete, onViewVersions, onViewParsed, isParsing }: ResumeCardProps) {
  return (
    <div className="flex items-center justify-between p-4 border rounded-lg">
      <div className="flex items-center gap-4">
        <div className="p-2 bg-primary/10 rounded-lg">
          <FileText className="h-6 w-6 text-primary" />
        </div>
        <div>
          <p className="font-medium">{resume.file_name}</p>
          <p className="text-sm text-muted-foreground">
            Uploaded {formatDistanceToNow(new Date(resume.uploaded_at), { addSuffix: true })}
          </p>
          {resume.parsed_data && (
            <Badge variant="secondary" className="mt-1">
              Parsed
            </Badge>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {!isActive && (
          <Button variant="outline" size="sm" onClick={onActivate}>
            <CheckCircle className="h-4 w-4 mr-2" />
            Set Active
          </Button>
        )}
        <Button variant="outline" size="sm" onClick={onParse} disabled={isParsing}>
          {isParsing ? <Spinner className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
          Parse
        </Button>
        <Button variant="outline" size="sm" onClick={onViewVersions}>
          <History className="h-4 w-4 mr-2" />
          Versions
        </Button>
        <Button variant="outline" size="sm" onClick={onViewParsed}>
          <Download className="h-4 w-4 mr-2" />
          Data
        </Button>
        <Button variant="ghost" size="sm" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

interface VersionHistoryContentProps {
  resumeId: string;
  onRollback: (resumeId: string, versionId: string) => void;
}

function VersionHistoryContent({ resumeId, onRollback }: VersionHistoryContentProps) {
  const { data: versions, isLoading } = useResumeVersionHistory(resumeId);

  if (isLoading) {
    return <div className="flex justify-center py-8"><Spinner /></div>;
  }

  if (!versions || versions.length === 0) {
    return <p className="text-sm text-muted-foreground">No version history available</p>;
  }

  return (
    <ScrollArea className="h-96">
      <div className="space-y-3">
        {versions.map((version) => (
          <div key={version.id} className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">Version {version.version_number}</p>
              <p className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(version.uploaded_at), { addSuffix: true })}
              </p>
            </div>
            {!version.is_active && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRollback(resumeId, version.id)}
              >
                Rollback
              </Button>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}

interface ParsedDataContentProps {
  resumeId: string;
}

function ParsedDataContent({ resumeId }: ParsedDataContentProps) {
  const { data: resume } = useResumeVersionHistory(resumeId);
  const currentVersion = resume?.find(v => v.is_active);

  if (!currentVersion?.parsed_data) {
    return <p className="text-sm text-muted-foreground">No parsed data available</p>;
  }

  return (
    <ScrollArea className="h-96">
      <pre className="text-sm bg-muted p-4 rounded-lg overflow-auto">
        {JSON.stringify(currentVersion.parsed_data, null, 2)}
      </pre>
    </ScrollArea>
  );
}
