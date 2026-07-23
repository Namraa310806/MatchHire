import * as React from "react"
import { cn } from "@/lib/utils"
import { Upload, X } from "lucide-react"
import { Button } from "./button"

interface FileUploadProps extends React.HTMLAttributes<HTMLDivElement> {
  onFileSelect?: (files: File[]) => void
  accept?: string
  multiple?: boolean
  maxSize?: number // in bytes
  maxFiles?: number
  value?: File[]
  onRemove?: (index: number) => void
}

const FileUpload = React.forwardRef<HTMLDivElement, FileUploadProps>(
  (
    {
      className,
      onFileSelect,
      accept,
      multiple = false,
      maxSize = 5 * 1024 * 1024, // 5MB default
      maxFiles = 5,
      value = [],
      onRemove,
      ...props
    },
    ref
  ) => {
    const [dragActive, setDragActive] = React.useState(false)
    const inputRef = React.useRef<HTMLInputElement>(null)

    const handleDrag = (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.type === "dragenter" || e.type === "dragover") {
        setDragActive(true)
      } else if (e.type === "dragleave") {
        setDragActive(false)
      }
    }

    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setDragActive(false)

      const files = Array.from(e.dataTransfer.files)
      processFiles(files)
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault()
      const files = Array.from(e.target.files || [])
      processFiles(files)
    }

    const processFiles = (files: File[]) => {
      const validFiles = files.filter((file) => {
        if (file.size > maxSize) {
          alert(`File ${file.name} is too large. Max size is ${maxSize / 1024 / 1024}MB`)
          return false
        }
        return true
      })

      if (multiple) {
        const newFiles = [...value, ...validFiles].slice(0, maxFiles)
        onFileSelect?.(newFiles)
      } else {
        onFileSelect?.([validFiles[0]])
      }
    }

    const onButtonClick = () => {
      inputRef.current?.click()
    }

    return (
      <div ref={ref} className={cn("w-full", className)} {...props}>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={handleChange}
          accept={accept}
          multiple={multiple}
        />

        <div
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
            dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={onButtonClick}
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm font-medium">
            {multiple ? "Drop files here or click to upload" : "Drop file here or click to upload"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Max size: {maxSize / 1024 / 1024}MB
            {maxFiles > 1 && ` • Max files: ${maxFiles}`}
          </p>
        </div>

        {value.length > 0 && (
          <div className="mt-4 space-y-2">
            {value.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-muted rounded-md"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                {onRemove && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onRemove(index)
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
)
FileUpload.displayName = "FileUpload"

export { FileUpload }
