import * as React from "react"
import { cn } from "@/lib/utils"
import { Search as SearchIcon, X } from "lucide-react"
import { Input } from "./input"

interface SearchBoxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onSearch?: (value: string) => void
  onClear?: () => void
  showClearButton?: boolean
}

const SearchBox = React.forwardRef<HTMLInputElement, SearchBoxProps>(
  (
    {
      className,
      onSearch,
      onClear,
      showClearButton = true,
      value,
      ...props
    },
    ref
  ) => {
    const [internalValue, setInternalValue] = React.useState(value || "")

    React.useEffect(() => {
      setInternalValue(value || "")
    }, [value])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value
      setInternalValue(newValue)
      onSearch?.(newValue)
    }

    const handleClear = () => {
      setInternalValue("")
      onSearch?.("")
      onClear?.()
    }

    return (
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          ref={ref}
          type="text"
          value={internalValue}
          onChange={handleChange}
          className={cn("pl-9 pr-9", className)}
          {...props}
        />
        {showClearButton && internalValue && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }
)
SearchBox.displayName = "SearchBox"

export { SearchBox }
