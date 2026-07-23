import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { FileUpload } from "@/components/ui/file-upload"
import { resumeService } from "../services/resume.service"

const resumeUploadSchema = z.object({
  file: z.any().refine((files) => files?.length > 0, "Please upload a resume file"),
})

type ResumeUploadFormData = z.infer<typeof resumeUploadSchema>

interface ResumeUploadFormProps {
  onSuccess?: (fileUrl: string) => void
  onError?: (error: Error) => void
}

export function ResumeUploadForm({ onSuccess, onError }: ResumeUploadFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ResumeUploadFormData>({
    resolver: zodResolver(resumeUploadSchema),
  })

  const files = watch("file") || []

  const onSubmit = async (data: ResumeUploadFormData) => {
    try {
      const result = await resumeService.uploadResumeFile(data.file[0])
      onSuccess?.(result.fileUrl)
    } catch (error) {
      onError?.(error as Error)
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Upload Resume</CardTitle>
        <CardDescription>Upload your resume to get started</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="file">Resume File</Label>
            <FileUpload
              accept=".pdf,.doc,.docx"
              onFileSelect={(selectedFiles) => setValue("file", selectedFiles)}
              value={files}
              onRemove={(index) => {
                const newFiles = [...files]
                newFiles.splice(index, 1)
                setValue("file", newFiles)
              }}
              maxSize={5 * 1024 * 1024}
              maxFiles={1}
            />
            {errors.file && (
              <p className="text-sm text-destructive" role="alert">
                {errors.file.message}
              </p>
            )}
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isSubmitting || files.length === 0}>
            {isSubmitting ? "Uploading..." : "Upload Resume"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}
