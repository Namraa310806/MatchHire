import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { jobService, CreateJobData } from "../services/job.service"

const jobSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters"),
  description: z.string().min(10, "Description must be at least 10 characters"),
  location: z.string().min(2, "Location is required"),
  employmentType: z.enum(["full-time", "part-time", "contract", "internship"]),
  experienceLevel: z.enum(["entry", "mid", "senior", "executive"]),
  salaryMin: z.number().min(0, "Minimum salary must be positive"),
  salaryMax: z.number().min(0, "Maximum salary must be positive"),
  currency: z.string().default("USD"),
  requirements: z.array(z.string()).min(1, "At least one requirement is needed"),
  responsibilities: z.array(z.string()).min(1, "At least one responsibility is needed"),
  skills: z.array(z.string()).min(1, "At least one skill is needed"),
}).refine((data) => data.salaryMax >= data.salaryMin, {
  message: "Maximum salary must be greater than or equal to minimum salary",
  path: ["salaryMax"],
})

type JobFormData = z.infer<typeof jobSchema>

interface JobFormProps {
  onSuccess?: () => void
  onError?: (error: Error) => void
  initialData?: Partial<CreateJobData>
}

export function JobForm({ onSuccess, onError, initialData }: JobFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema),
    defaultValues: initialData,
  })

  const onSubmit = async (data: JobFormData) => {
    try {
      const jobData: CreateJobData = {
        ...data,
        salary: {
          min: data.salaryMin,
          max: data.salaryMax,
          currency: data.currency,
        },
      }
      await jobService.createJob(jobData)
      onSuccess?.()
    } catch (error) {
      onError?.(error as Error)
    }
  }

  const addToArray = (field: "requirements" | "responsibilities" | "skills", value: string) => {
    if (value.trim()) {
      setValue(field, [...(register(field).value || []), value.trim()])
    }
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Create Job Posting</CardTitle>
        <CardDescription>Fill in the details to create a new job posting</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title">Job Title</Label>
            <Input
              id="title"
              placeholder="Software Engineer"
              {...register("title")}
              aria-invalid={errors.title ? "true" : "false"}
              aria-describedby={errors.title ? "title-error" : undefined}
            />
            {errors.title && (
              <p id="title-error" className="text-sm text-destructive" role="alert">
                {errors.title.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe the role and what makes it exciting..."
              rows={4}
              {...register("description")}
              aria-invalid={errors.description ? "true" : "false"}
              aria-describedby={errors.description ? "description-error" : undefined}
            />
            {errors.description && (
              <p id="description-error" className="text-sm text-destructive" role="alert">
                {errors.description.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="employmentType">Employment Type</Label>
              <Select onValueChange={(value) => setValue("employmentType", value as any)}>
                <SelectTrigger id="employmentType" aria-invalid={errors.employmentType ? "true" : "false"}>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="full-time">Full-time</SelectItem>
                  <SelectItem value="part-time">Part-time</SelectItem>
                  <SelectItem value="contract">Contract</SelectItem>
                  <SelectItem value="internship">Internship</SelectItem>
                </SelectContent>
              </Select>
              {errors.employmentType && (
                <p className="text-sm text-destructive" role="alert">
                  {errors.employmentType.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="experienceLevel">Experience Level</Label>
              <Select onValueChange={(value) => setValue("experienceLevel", value as any)}>
                <SelectTrigger id="experienceLevel" aria-invalid={errors.experienceLevel ? "true" : "false"}>
                  <SelectValue placeholder="Select level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="entry">Entry Level</SelectItem>
                  <SelectItem value="mid">Mid Level</SelectItem>
                  <SelectItem value="senior">Senior Level</SelectItem>
                  <SelectItem value="executive">Executive</SelectItem>
                </SelectContent>
              </Select>
              {errors.experienceLevel && (
                <p className="text-sm text-destructive" role="alert">
                  {errors.experienceLevel.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              placeholder="San Francisco, CA"
              {...register("location")}
              aria-invalid={errors.location ? "true" : "false"}
              aria-describedby={errors.location ? "location-error" : undefined}
            />
            {errors.location && (
              <p id="location-error" className="text-sm text-destructive" role="alert">
                {errors.location.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="salaryMin">Min Salary</Label>
              <Input
                id="salaryMin"
                type="number"
                placeholder="50000"
                {...register("salaryMin", { valueAsNumber: true })}
                aria-invalid={errors.salaryMin ? "true" : "false"}
                aria-describedby={errors.salaryMin ? "salaryMin-error" : undefined}
              />
              {errors.salaryMin && (
                <p id="salaryMin-error" className="text-sm text-destructive" role="alert">
                  {errors.salaryMin.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="salaryMax">Max Salary</Label>
              <Input
                id="salaryMax"
                type="number"
                placeholder="100000"
                {...register("salaryMax", { valueAsNumber: true })}
                aria-invalid={errors.salaryMax ? "true" : "false"}
                aria-describedby={errors.salaryMax ? "salaryMax-error" : undefined}
              />
              {errors.salaryMax && (
                <p id="salaryMax-error" className="text-sm text-destructive" role="alert">
                  {errors.salaryMax.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Select onValueChange={(value) => setValue("currency", value)} defaultValue="USD">
                <SelectTrigger id="currency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                  <SelectItem value="INR">INR</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="skills">Skills (comma-separated)</Label>
            <Input
              id="skills"
              placeholder="React, TypeScript, Node.js"
              {...register("skills")}
              aria-invalid={errors.skills ? "true" : "false"}
              aria-describedby={errors.skills ? "skills-error" : undefined}
            />
            {errors.skills && (
              <p id="skills-error" className="text-sm text-destructive" role="alert">
                {errors.skills.message}
              </p>
            )}
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating job..." : "Create Job Posting"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}
