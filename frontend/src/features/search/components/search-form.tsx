import * as React from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { searchService, SearchFilters } from "../services/search.service"

const searchSchema = z.object({
  query: z.string().min(1, "Search query is required"),
  type: z.enum(["job", "candidate", "company", "all"]).default("all"),
  location: z.string().optional(),
  experienceLevel: z.string().optional(),
})

type SearchFormData = z.infer<typeof searchSchema>

interface SearchFormProps {
  onSearch?: (results: any) => void
  onError?: (error: Error) => void
}

export function SearchForm({ onSearch, onError }: SearchFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<SearchFormData>({
    resolver: zodResolver(searchSchema),
    defaultValues: {
      type: "all",
    },
  })

  const onSubmit = async (data: SearchFormData) => {
    try {
      const filters: SearchFilters = {
        query: data.query,
        type: data.type as any,
        location: data.location,
        experienceLevel: data.experienceLevel,
      }
      const results = await searchService.search(filters)
      onSearch?.(results)
    } catch (error) {
      onError?.(error as Error)
    }
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Search</Label>
            <Input
              id="query"
              placeholder="Search for jobs, candidates, or companies..."
              {...register("query")}
              aria-invalid={errors.query ? "true" : "false"}
              aria-describedby={errors.query ? "query-error" : undefined}
            />
            {errors.query && (
              <p id="query-error" className="text-sm text-destructive" role="alert">
                {errors.query.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="type">Type</Label>
              <Select onValueChange={(value) => setValue("type", value as any)} defaultValue="all">
                <SelectTrigger id="type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="job">Jobs</SelectItem>
                  <SelectItem value="candidate">Candidates</SelectItem>
                  <SelectItem value="company">Companies</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="San Francisco, CA"
                {...register("location")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="experienceLevel">Experience Level</Label>
              <Select onValueChange={(value) => setValue("experienceLevel", value)}>
                <SelectTrigger id="experienceLevel">
                  <SelectValue placeholder="Any" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="entry">Entry Level</SelectItem>
                  <SelectItem value="mid">Mid Level</SelectItem>
                  <SelectItem value="senior">Senior Level</SelectItem>
                  <SelectItem value="executive">Executive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Searching..." : "Search"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
