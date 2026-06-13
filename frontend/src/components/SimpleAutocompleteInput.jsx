/**
 * SimpleAutocompleteInput.jsx
 *
 * A text Input + dropdown of generic suggestions. User can:
 *   - Type freely (custom values always allowed)
 *   - Click the chevron to open the dropdown
 *   - Filter the dropdown by typing
 *   - Click a row to select it
 *
 * Unlike JobAutocompleteInput, this component does NOT carry contextual
 * pairs - the dropdown is a plain list of strings. Each field (Job Title,
 * Company) is independent.
 */
import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SimpleAutocompleteInput({
  value,
  onChange,
  options = [],
  placeholder,
  icon: Icon,
  testId,
  groupHeading,
}) {
  const [open, setOpen] = useState(false);
  const inputRef = useRef(null);

  // Filter the option list against current input value.
  const v = (value || "").toLowerCase();
  const filtered = options
    .filter((opt) => !v || opt.toLowerCase().includes(v))
    .slice(0, 100);

  // Keep the popover open while user types if there are matches
  useEffect(() => {
    if (document.activeElement === inputRef.current && filtered.length > 0) {
      setOpen(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
            className={cn(
              "bg-white border-gray-200",
              Icon ? "pl-10" : "",
              "pr-10"
            )}
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
            <ChevronDown
              className={cn(
                "w-4 h-4 transition-transform",
                open && "rotate-180"
              )}
            />
          </button>
        </div>
      </PopoverTrigger>
      <PopoverContent
        className="w-[var(--radix-popover-trigger-width)] p-0"
        align="start"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <Command shouldFilter={false}>
          <CommandList className="max-h-72">
            <CommandEmpty>
              No matches. Keep typing to use a custom value.
            </CommandEmpty>
            <CommandGroup heading={groupHeading}>
              {filtered.map((opt, i) => (
                <CommandItem
                  key={`${opt}|${i}`}
                  value={opt}
                  onSelect={() => {
                    onChange(opt);
                    setOpen(false);
                  }}
                  className="cursor-pointer"
                  data-testid={`autocomplete-option-${i}`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="truncate text-gray-900">{opt}</span>
                    {value && opt.toLowerCase() === value.toLowerCase() && (
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
