import { Skeleton } from "@/components/ui/skeleton"

interface SectionLoaderProps {
  count?: number
}

export function SectionLoader({ count = 3 }: SectionLoaderProps) {
  return (
    <div className="space-y-4">
      {[...Array(count)].map((_, i) => (
        <div key={i} className="space-y-3">
          <Skeleton className="h-6 w-1/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      ))}
    </div>
  )
}
