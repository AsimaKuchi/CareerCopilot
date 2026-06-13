/**
 * JobAutocompleteInput.jsx
 *
 * Combobox: an <Input> field that ALSO shows a filterable dropdown of
 * suggestions. The user can either pick from the dropdown or type a custom
 * value. The dropdown lists the user's saved applications + saved jobs
 * (fetched from GET /api/ai/interview-prep/suggestions).
 *
 * Props:
 *   value         - current text in the input
 *   onChange      - called with the new text on every keystroke
 *   onSelect(s)   - called with a full suggestion object when user picks one
 *                   from the dropdown ({ job_title, company, job_description })
 *   suggestions   - array of suggestion objects (fetched once by parent)
 *   field         - "job_title" or "company" - which field of each suggestion
 *                   to display in the row
 *   placeholder, icon, testId, label
 */
import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export default function JobAutocompleteInput({
  value,
  onChange,
  onSelect,
  suggestions = [],
  field,
  otherField,
  placeholder,
  icon: Icon,
  testId,
}) {
  const [open, setOpen] = useState(false);
  const inputRef = useRef(null);

  // De-dupe + filter suggestions by the typed value
  const seen = new Set();
  const filtered = suggestions
    .filter((s) => {
      const k = (s[field] || "").trim().toLowerCase();
      if (!k || seen.has(k)) return false;
      seen.add(k);
      return true;
    })
    .filter((s) => {
      if (!value) return true;
      const haystack = `${s.job_title} ${s.company}`.toLowerCase();
      return haystack.includes(value.toLowerCase());
    })
    .slice(0, 50);

  // Keep popover open while user types if there are matches
  useEffect(() => {
    if (document.activeElement === inputRef.current && filtered.length > 0) {
      setOpen(true);
    }
  }, [value, filtered.length]);

  return (
    <Popover open={open && filtered.length > 0} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <div className="relative">
          {Icon && (
            <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          )}
          <Input
            ref={inputRef}
            data-testid={testId}
            placeholder={placeholder}
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              if (!open) setOpen(true);
            }}
            onFocus={() => filtered.length > 0 && setOpen(true)}
            className={cn("bg-white border-gray-200", Icon ? "pl-10" : "", "pr-10")}
          />
          <button
            type="button"
            aria-label="Show suggestions"
            onClick={(e) => {
              e.preventDefault();
              inputRef.current?.focus();
              setOpen((o) => !o);
            }}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
          >
            <ChevronDown className={cn("w-4 h-4 transition-transform", open && "rotate-180")} />
          </button>
        </div>
      </PopoverTrigger>
      <PopoverContent
        className="w-[var(--radix-popover-trigger-width)] p-0"
        align="start"
        onOpenAutoFocus={(e) => e.preventDefault()} // keep focus on the input
      >
        <Command shouldFilter={false}>
          <CommandList>
            <CommandEmpty>No matches. Keep typing to use a custom value.</CommandEmpty>
            <CommandGroup heading={`Your ${field === "job_title" ? "roles" : "companies"}`}>
              {filtered.map((s, i) => (
                <CommandItem
                  key={`${s.job_title}|${s.company}|${i}`}
                  value={`${s.job_title} ${s.company}`}
                  onSelect={() => {
                    onSelect?.(s);
                    setOpen(false);
                  }}
                  className="cursor-pointer"
                  data-testid={`suggestion-${field}-${i}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <div className="min-w-0">
                      <div className="font-medium text-gray-900 truncate">
                        {s[field]}
                      </div>
                      {otherField && s[otherField] && (
                        <div className="text-xs text-gray-500 truncate">
                          {s[otherField]}
                        </div>
                      )}
                    </div>
                    {value && s[field].toLowerCase() === value.toLowerCase() && (
                      <Check className="w-4 h-4 text-emerald-500 ml-2 flex-shrink-0" />
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
