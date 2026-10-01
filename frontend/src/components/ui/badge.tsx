import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2 py-0.5 text-xs font-mono font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-ring",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-brass/15 text-brass border border-brass/30",
        secondary:
          "border-transparent bg-surface-secondary text-foreground border border-border",
        outline: "text-foreground border border-border",
        sage: "bg-sage/15 text-sage border border-sage/30",
        ochre: "bg-ochre/15 text-ochre border border-ochre/30",
        clay: "bg-clay/15 text-clay border border-clay/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
