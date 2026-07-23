import { toast } from "@/hooks/use-toast"

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export const handleApiError = (error: any) => {
  console.error("API Error:", error)

  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        toast({
          title: "Authentication Error",
          description: "Please log in again",
          variant: "destructive",
        })
        // Redirect to login
        window.location.href = "/login"
        break
      case 403:
        toast({
          title: "Access Denied",
          description: "You don't have permission to perform this action",
          variant: "destructive",
        })
        break
      case 404:
        toast({
          title: "Not Found",
          description: "The requested resource was not found",
          variant: "destructive",
        })
        break
      case 500:
        toast({
          title: "Server Error",
          description: "Something went wrong on our end. Please try again later.",
          variant: "destructive",
        })
        break
      default:
        toast({
          title: "Error",
          description: error.message || "An unexpected error occurred",
          variant: "destructive",
        })
    }
  } else {
    toast({
      title: "Error",
      description: error.message || "An unexpected error occurred",
      variant: "destructive",
    })
  }

  throw error
}

export const createRetryHandler = (
  fn: (...args: any[]) => Promise<any>,
  maxRetries = 3,
  delay = 1000
) => {
  return async (...args: any[]) => {
    let lastError: any

    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn(...args)
      } catch (error) {
        lastError = error
        if (i < maxRetries - 1) {
          await new Promise((resolve) => setTimeout(resolve, delay * (i + 1)))
        }
      }
    }

    throw lastError
  }
}
